"""Generate the release notes automatically from GitHub pull requests.

Start with:
```
export GH_TOKEN=<your-gh-api-token>
```
Then, for to include everything from a certain release to main:
```
python /path/to/generate_release_notes.py v0.14.0 main --version 0.15.0
```
Or two include only things between two releases:
```
python /path/to/generate_release_notes.py v.14.2 v0.14.3 --version 0.14.3
```
You should probably redirect the output with:
```
python /path/to/generate_release_notes.py [args] | tee release_notes.md
```
You'll require PyGitHub and tqdm, which you can install with:
```
python -m pip install -e ".[release]"
```
References
https://github.com/scikit-image/scikit-image/blob/main/tools/generate_release_notes.py
https://github.com/scikit-image/scikit-image/issues/3404
https://github.com/scikit-image/scikit-image/issues/3405
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

from github.PullRequest import PullRequest
from github.Repository import Repository

from release_utils import (
    BOT_LIST,
    GH,
    GH_DOCS_REPO,
    GH_REPO,
    GH_USER,
    REPO_DIR_NAME,
    get_correction_dict,
    get_corrections_from_citation_cff,
    get_repo,
    iter_pull_request,
    setup_cache,
)

LOCAL_DIR = Path(__file__).parent

PR_REGEXP = re.compile(r'(?P<user>[\w-]+)/(?P<repo>[\w-]+)#(?P<pr>\d+)')


class PRInfo(NamedTuple):
    user: str
    repo: str
    pr: int


def parse_pr_num(pr_num):
    if match := PR_REGEXP.match(pr_num):
        return PRInfo(
            match.group('user'), match.group('repo'), int(match.group('pr'))
        )
    try:
        return int(pr_num)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{pr_num} is not a valid PR number.')


parser = argparse.ArgumentParser(usage=__doc__)
parser.add_argument('milestone', help='The milestone to list')
parser.add_argument('--target-directory', type=Path, default=None)
parser.add_argument(
    '--correction-file',
    help='The file with the corrections',
    default=LOCAL_DIR / 'name_corrections.yaml',
)
parser.add_argument(
    '--with-pr',
    help='Include PR numbers for not merged PRs',
    type=parse_pr_num,
    default=None,
    nargs='+',
)

args = parser.parse_args()


setup_cache()
repo = get_repo()
correction_dict = get_correction_dict(
    args.correction_file
) | get_corrections_from_citation_cff(
    LOCAL_DIR / REPO_DIR_NAME / 'CITATION.cff'
)


def add_to_users(users_dkt, new_user):
    if new_user.login in users_dkt:
        # reduce obsolete requests to GitHub API
        return
    if new_user.login in correction_dict:
        users_dkt[new_user.login] = correction_dict[new_user.login]
    elif new_user.name is None:
        users_dkt[new_user.login] = new_user.login
    else:
        users_dkt[new_user.login] = new_user.name


authors = set()
committers = set()
docs_authors = set()
docs_committers = set()
reviewers = set()
docs_reviewers = set()
users = {}

highlights = {
    'Highlights': {},
    'New Features': {},
    'Improvements': {},
    'Performance': {},
    'Bug Fixes': {},
    'API Changes': {},
    'Deprecations': {},
    'Build Tools': {},
    'Documentation': {},
}

other_pull_requests = {}

label_to_section = {
    'bug': 'Bug Fixes',
    'bugfix': 'Bug Fixes',
    'feature': 'New Features',
    'api': 'API Changes',
    'highlight': 'Highlights',
    'performance': 'Performance',
    'enhancement': 'Improvements',
    'deprecation': 'Deprecations',
    'dependencies': 'Build Tools',
    'documentation': 'Documentation',
}


def parse_pull(pull: PullRequest, repo_: Repository = repo):
    # assert pull.merged or pull.number in args.with_pr

    commit = repo_.get_commit(pull.merge_commit_sha)

    if commit.committer is not None:
        add_to_users(users, commit.committer)
        committers.add(commit.committer.login)
    if commit.author is not None:
        add_to_users(users, commit.author)
        authors.add(commit.author.login)

    summary = pull.title

    for review in pull.get_reviews():
        if review.user is not None:
            add_to_users(users, review.user)
            reviewers.add(review.user.login)
    assigned_to_section = False
    pr_labels = {label.name.lower() for label in pull.labels}
    for label_name, section in label_to_section.items():
        if label_name in pr_labels:
            highlights[section][pull.number] = {
                'summary': summary,
                'repo': repo_.full_name.split('/')[1],
            }
            assigned_to_section = True

    if not assigned_to_section:
        other_pull_requests[pull.number] = {
            'summary': summary,
            'repo': repo_.full_name.split('/')[1],
        }


for pull_ in iter_pull_request(f'milestone:{args.milestone} is:merged'):
    parse_pull(pull_)

if args.with_pr is not None:
    for pr_num in args.with_pr:
        if isinstance(pr_num, int):
            pull = repo.get_pull(pr_num)
            r = repo
        else:
            r = get_repo(pr_num.user, pr_num.repo)
            pull = r.get_pull(pr_num.pr)

        parse_pull(pull, r)

for pull in iter_pull_request(
    f'milestone:{args.milestone} is:merged', repo=GH_DOCS_REPO
):
    issue = pull.as_issue()
    assert pull.merged

    add_to_users(users, issue.user)
    docs_authors.add(issue.user.login)

    summary = pull.title

    for review in pull.get_reviews():
        if review.user is not None:
            add_to_users(users, review.user)
            docs_reviewers.add(review.user.login)
    assigned_to_section = False
    pr_labels = {label.name.lower() for label in pull.labels}
    if 'maintenance' in pr_labels:
        other_pull_requests[pull.number] = {
            'summary': summary,
            'repo': GH_DOCS_REPO,
        }
    else:
        highlights['Documentation'][pull.number] = {
            'summary': summary,
            'repo': GH_DOCS_REPO,
        }


# add Other PRs to the ordered dict to make doc generation easier.
highlights['Other Pull Requests'] = other_pull_requests


# remove these bots.
committers -= BOT_LIST
authors -= BOT_LIST
docs_committers -= BOT_LIST
docs_authors -= BOT_LIST


user_name_pattern = re.compile(r'@([\w-]+)')  # pattern for GitHub usernames
pr_number_pattern = re.compile(r'#(\d+)')  # pattern for GitHub PR numbers

old_contributors = set()

if args.target_directory is None:
    file_handle = sys.stdout
else:
    res_file_name = f"release_{args.milestone.replace('.', '_')}.md"
    file_handle = open(args.target_directory / res_file_name, 'w')
    for file_path in args.target_directory.glob('release_*.md'):
        if file_path.name == res_file_name:
            continue
        with open(file_path) as f:
            old_contributors.update(user_name_pattern.findall(f.read()))


# Now generate the release notes
title = f'# napari {args.milestone}'
print(title, file=file_handle)

notes_dir = LOCAL_DIR / 'additional_notes' / args.milestone
if not notes_dir.glob('*.md'):
    print(
        'There is no prepared sections in the additional_notes directory.',
        file=sys.stderr,
    )

if (fn := notes_dir / 'header.md').exists():
    intro = fn.open().read()
else:
    intro = f"""
We're happy to announce the release of napari {args.milestone}!
napari is a fast, interactive, multi-dimensional image viewer for Python.
It's designed for browsing, annotating, and analyzing large multi-dimensional
images. It's built on top of Qt (for the GUI), vispy (for performant GPU-based
rendering), and the scientific Python stack (numpy, scipy).

For more information, examples, and documentation, please visit our website,
https://napari.org.
"""

print(intro, file=file_handle)

for section, pull_request_dicts in highlights.items():
    if not pull_request_dicts:
        continue
    print(f'## {section}\n', file=file_handle)
    section_path = (
        LOCAL_DIR
        / 'additional_notes'
        / args.milestone
        / f'{section.lower()}.md'
    )
    mentioned_pr = set()
    if section_path.exists():
        with section_path.open() as f:
            text = f.read()
        for pr_number in pr_number_pattern.findall(text):
            mentioned_pr.add(int(pr_number))
        print(text, file=file_handle)

    for number, pull_request_info in pull_request_dicts.items():
        if number in mentioned_pr:
            continue
        repo_str = pull_request_info['repo']
        repo_prefix = repo_str if repo_str != 'napari' else ''
        print(
            f'- {pull_request_info["summary"]} ([{repo_prefix}#{number}]'
            f"(https://{GH}/{GH_USER}/{repo_str}/pull/{number}))",
            file=file_handle,
        )
    print('', file=file_handle)


contributors = {
    'authors': authors | docs_authors,
    'reviewers': reviewers | docs_reviewers,
}

# ignore committers
# contributors['committers'] = committers
new_contributors = (authors | docs_authors) - old_contributors

for section_name, contributor_set in contributors.items():
    print('', file=file_handle)
    if None in contributor_set:
        contributor_set.remove(None)
    committer_str = (
        f'## {len(contributor_set)} {section_name} added to this '
        'release (alphabetical)'
    )
    print(committer_str, file=file_handle)
    print('', file=file_handle)
    print('(+) denotes first-time contributors 🥳', file=file_handle)
    print('', file=file_handle)

    for c in sorted(contributor_set, key=lambda x: users[x].lower()):
        if c in authors and c in docs_authors:
            first_repo_name = GH_REPO
            second_repo_str = (
                f' ([docs](https://{GH}/{GH_USER}/'
                f'{GH_DOCS_REPO}/commits?author={c})) '
            )
        elif c in authors:
            first_repo_name = GH_REPO
            second_repo_str = ''
        else:  # docs only
            first_repo_name = GH_DOCS_REPO
            second_repo_str = ''

        first = ' +' if c in new_contributors else ''
        commit_link = (
            f'https://{GH}/{GH_USER}/{first_repo_name}/' f'commits?author={c}'
        )
        print(
            f'- [{users[c]}]({commit_link}){second_repo_str} - @{c}{first}',
            file=file_handle,
        )
    print('', file=file_handle)
