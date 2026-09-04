"""Generate the release notes automatically from GitHub pull requests.

We recoment using uv for runing this script.
1. clone the napari/docs repository to read previous contributors and to write the release notes to the correct location.

2. Install the requirements into a virtual environment (PyGitHub and tqdm) with
   ```
   uv sync
   ```
3. Start by creating a GitHub API token. You can do this by going to
GitHub settings -> Developer settings -> Personal access tokens -> Fine-grained tokens.
Create a new token with read-only access to Public repositories;
the token must expire in 365 days or less.

4. Set the token as an environment variable:
On Linux or MacOS:
```
export GH_TOKEN='<your-gh-api-token>'
```
or in Windows cmd:
```
set GH_TOKEN=<your-gh-api-token>
```
or set permanently with Windows PowerShell:
```
[Environment]::SetEnvironmentVariable("GH_TOKEN", "<your-gh-api-token>", "User")
```

5. Run the script:
Then, to include everything set for the a chosen milestone:
```
uv run generate_release_notes.py <milestone> --target-directory=/path/to/docs/release/
```
For example:
```
uv run generate_release_notes.py 0.7.1 --target-directory=../napari-docs/docs/release/
```

To substitute GitHub handles for author names, use the `--correction-file` option:
```
uv run generate_release_notes.py <milestone> --target-directory=/path/to/docs/release/ --correction-file /path/to/name_corrections.yaml
```

The default correction file is `name_corrections.yaml` in the same directory as this script, so the argument is not needed.

By default the script is caching GitHub API requests to speed
up execution and reduce the number of requests to the GitHub API.
It means that if you edit some PR titles or labels, you may not see
the changes in the generated release notes until the cache expires (after 1h by default).

Cache is used to avoid hitting GitHub API rate limits, which can be a
problem when generating release notes for a large number of pull requests.

Script can be run with the `--no-cache` option to disable caching of GitHub API requests.

To clean the cache, you can delete the `github_cache` directory in the current working directory.

There is a known problem with using cache on conda environments, because
we use threads to speed up the execution, and
access to sqlite database used by cache is not thread-safe.
Even if we use `filesystem` backend for cache, it still uses sqlite database under the hood.

Hoever, when using `uv` it works and speeds up the execution significantly, so we recommend using `uv` for running this script.



References:
- https://github.com/scikit-image/scikit-image/blob/main/tools/generate_release_notes.py
- https://github.com/scikit-image/scikit-image/issues/3404
- https://github.com/scikit-image/scikit-image/issues/3405
"""

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple

from packaging.version import parse as parse_version
from tqdm import tqdm

from release_utils import (
    BOT_LIST,
    GH,
    GH_DOCS_REPO,
    GH_REPO,
    GH_USER,
    REPO_DIR_NAME,
    get_correction_dict,
    get_corrections_from_citation_cff,
    get_milestone,
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

    def to_str(self):
        return f'{self.user}/{self.repo}#{self.pr}'


class ReleaseType(StrEnum):
    MACRO = 'major'
    MESO = 'meso'
    MICRO = 'micro'
    BUGFIX = 'bugfix'


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
parser.add_argument('tag', help='The tag that will be released, e.g. 0.6.2')
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
parser.add_argument(
    '--only-merged',
    help='Only include merged PRs, excluding open ones.',
    action='store_const',
    const='is:merged',
    default='',
    dest='merged',
)
parser.add_argument(
    '--no-cache',
    help='Disable caching of GitHub API requests. This may lead to slower execution and more requests to the GitHub API, but ensures that you are getting the most up-to-date information.',
    action='store_true',
)

parser.add_argument(
    '--release-type',
    help='The type of the release (e.g., major, minor, patch)',
    default=None,
    type=ReleaseType,
)

args = parser.parse_args()


version = parse_version(args.tag)

args.milestone = version.base_version

if not args.no_cache:
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

non_merged_pr = []

highlights: dict[str, dict[PRInfo, dict[str, str]]] = {
    'Highlights': {},
    'New Features': {},
    'Breaking Changes': {},
    'Improvements': {},
    'Performance': {},
    'Bug Fixes': {},
    'API Changes': {},
    'Deprecations': {},
    'Build Tools': {},
    'Documentation': {},
}

other_pull_requests: dict[PRInfo, dict[str, str]] = {}

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
    'example': 'Documentation',
    'release:breaking change': 'Breaking Changes',
}

section_to_label: dict[str, list[str]] = {}
for label, section in label_to_section.items():
    section_to_label.setdefault(section, []).append(label)


def parse_pull(pull_number: int, user_name: str, repo_name: str) -> None:
    repo_ = get_repo(user_name, repo_name)
    pull = repo_.get_pull(pull_number)

    is_merged = pull.raw_data.get('merged')
    if is_merged is None:
        is_merged = pull.merged

    if is_merged:
        if pull.merged_by is not None:
            add_to_users(users, pull.merged_by)
            committers.add(pull.merged_by.login)
        if pull.user is not None:
            add_to_users(users, pull.user)
            authors.add(pull.user.login)
    else:
        if pull.raw_data.get('state') == 'closed':
            print(
                f'Warning: PR {pull_number} in {user_name}/{repo_name} is closed but not merged. It will be ignored in the release notes.',
                file=sys.stderr,
            )
            return
        else:
            non_merged_pr.append(pull)

    summary = pull.title

    for review in pull.get_reviews():
        if review.user is not None:
            add_to_users(users, review.user)
            reviewers.add(review.user.login)
    assigned_to_section = False
    pr_labels = {label.name.lower() for label in pull.labels}
    for label_name, section in label_to_section.items():
        if label_name in pr_labels:
            highlights[section][PRInfo(user_name, repo_name, pull_number)] = {
                'summary': summary,
                'repo': repo_name,
            }
            assigned_to_section = True

    if not assigned_to_section:
        other_pull_requests[PRInfo(user_name, repo_name, pull_number)] = {
            'summary': summary,
            'repo': repo_name,
        }


def parse_docs_pull(pull_number: int, user_name: str, repo_name: str) -> None:
    repo_ = get_repo(user_name, repo_name)

    pull = repo_.get_pull(pull_number)

    is_merged = pull.raw_data.get('merged')
    if is_merged is None:
        is_merged = pull.merged

    if is_merged:
        if pull.merged_by is not None:
            add_to_users(users, pull.merged_by)
            docs_committers.add(pull.merged_by.login)
        if pull.user is not None:
            add_to_users(users, pull.user)
            docs_authors.add(pull.user.login)
    else:
        if pull.raw_data.get('state') == 'closed':
            print(
                f'Warning: PR {pull_number} in {user_name}/{repo_name} is closed but not merged. It will be ignored in the release notes.',
                file=sys.stderr,
            )
        else:
            non_merged_pr.append(pull)

    for review in pull.get_reviews():
        if review.user is not None:
            add_to_users(users, review.user)
            docs_reviewers.add(review.user.login)

    pr_labels = {label.name.lower() for label in pull.labels}
    summary = pull.title
    if 'highlight' in pr_labels:
        highlights['Highlights'][PRInfo(user_name, repo_name, pull.number)] = {
            'summary': summary,
            'repo': GH_DOCS_REPO,
        }
    if 'maintenance' in pr_labels:
        other_pull_requests[PRInfo(user_name, repo_name, pull.number)] = {
            'summary': summary,
            'repo': GH_DOCS_REPO,
        }
    else:
        highlights['Documentation'][
            PRInfo(user_name, repo_name, pull.number)
        ] = {
            'summary': summary,
            'repo': GH_DOCS_REPO,
        }


pulls_to_parse = [
    (x.number, GH_USER, GH_REPO)
    for x in iter_pull_request(f'milestone:{args.milestone} {args.merged}')
]

if args.with_pr is not None:
    for pr_num in args.with_pr:
        if isinstance(pr_num, int):
            pulls_to_parse.append((pr_num, GH_USER, GH_REPO))
        else:
            r = get_repo(pr_num.user, pr_num.repo)
            pulls_to_parse.append((pr_num.pr, pr_num.user, pr_num.repo))

doc_pulls = list(
    iter_pull_request(
        f'milestone:{args.milestone} {args.merged}', repo=GH_DOCS_REPO
    )
)

with ThreadPoolExecutor(max_workers=10) as executor:
    list(
        tqdm(
            executor.map(lambda x: parse_pull(*x), pulls_to_parse),
            desc='napari/napari parse',
            total=len(pulls_to_parse),
        )
    )

with ThreadPoolExecutor(max_workers=10) as executor:
    list(
        tqdm(
            executor.map(
                lambda x: parse_docs_pull(*x),
                [(pull.number, GH_USER, GH_DOCS_REPO) for pull in doc_pulls],
            ),
            desc='napari/docs parse',
            total=len(doc_pulls),
        )
    )


# add Other PRs to the ordered dict to make doc generation easier.
highlights['Other Pull Requests'] = other_pull_requests


# remove these bots.
committers -= BOT_LIST
authors -= BOT_LIST
docs_committers -= BOT_LIST
docs_authors -= BOT_LIST
reviewers -= BOT_LIST
docs_reviewers -= BOT_LIST

GITHUB_PR_LINK_PATTERN = re.compile(
    GH + r'/(?P<owner>[\w-]+)/(?P<repo>[\w-]+)/pull/(?P<number>\d+)'
)  # pattern for GitHub PR link
USER_NAME_PATTERN = re.compile(r'@([\w-]+)')
AUTHOR_SECTION_RE = re.compile(
    r'^##\s+\d+\s+authors added to this release \(alphabetical\)\s*\n(?P<body>.*?)(?=^##\s+|\Z)',
    re.M | re.S | re.I,
)
REVIEWER_SECTION_RE = re.compile(
    r'^##\s+\d+\s+reviewers added to this release \(alphabetical\)\s*\n(?P<body>.*?)(?=^##\s+|\Z)',
    re.M | re.S | re.I,
)
AUTHOR_LINE_RE = re.compile(r'- .*? - @([\w-]+)')

old_contributors = set()
old_reviewers = set()
if args.target_directory is None:
    file_handle = sys.stdout
else:
    res_file_name = f'release_{args.milestone.replace(".", "_")}.md'
    file_handle = open(
        args.target_directory / res_file_name, 'w', encoding='utf-8'
    )

    for file_path in args.target_directory.glob('release_*.md'):
        if file_path.name == res_file_name:
            continue

        text = file_path.read_text(encoding='utf-8')
        match = AUTHOR_SECTION_RE.search(text)
        if match:
            section_text = match.group('body')
            old_contributors.update(AUTHOR_LINE_RE.findall(section_text))

        match = REVIEWER_SECTION_RE.search(text)
        if match:
            section_text = match.group('body')
            old_reviewers.update(AUTHOR_LINE_RE.findall(section_text))

# Now generate the release notes
title = f'# napari {args.milestone}'
print(title, file=file_handle)

notes_dir = LOCAL_DIR / 'additional_notes' / args.milestone
if not notes_dir.glob('*.md'):
    print(
        'There is no prepared sections in the additional_notes directory.',
        file=sys.stderr,
    )

milestone_obj = get_milestone(args.milestone)

# prerelease includes alpha and rc versions
if version.is_prerelease:
    print(
        f'⚠️ *Note: these release notes are still in draft while {version} is in prerelease testing.* ⚠️',
        file=file_handle,
    )
print('', file=file_handle)
print(f'*{milestone_obj.due_on.strftime("%a, %b %d, %Y")}*', file=file_handle)
print('', file=file_handle)

if (fn := notes_dir / 'header.md').exists():
    intro = fn.open(encoding='utf-8').read()
else:
    intro = f"""We're happy to announce the release of napari {args.milestone}!
napari is a fast, interactive, multi-dimensional image viewer for Python.
It's designed for browsing, annotating, and analyzing large multi-dimensional
images. It's built on top of Qt (for the GUI), vispy (for performant GPU-based
rendering), and the scientific Python stack (numpy, scipy).

For more information, examples, and documentation, please visit our website,
https://napari.org.
"""

print(intro, file=file_handle)


def detect_effver_type(milestone, release_type=None) -> ReleaseType:
    """Detect if this is a MACRO, MESO, or MICRO release based on version number."""
    # Remove any pre-release suffixes (like 0.6.0rc1 -> 0.6.0)
    if release_type is not None:
        return release_type

    clean_version = milestone.split('rc')[0].split('a')[0].split('b')[0]
    parts = clean_version.split('.')
    vinfo = int(parts[0]), int(parts[1]), int(parts[2])
    match vinfo:
        case 0, _, 0:
            return ReleaseType.MACRO
        case 0, _, _:
            return ReleaseType.MESO
        case _, 0, 0:
            return ReleaseType.MACRO
        case _, _, 0:
            return ReleaseType.MESO
        case _:
            return ReleaseType.MICRO


effver_type = detect_effver_type(
    args.milestone, release_type=args.release_type
)

effver_info = {
    ReleaseType.MACRO: 'this is a **Macro** release containing awesome new features, but may require dedication of some significant time when upgrading projects to use this version.',
    ReleaseType.MESO: 'this is a **Meso** release containing awesome new features, but some effort may be needed when updating previous projects to use this version.',
    ReleaseType.MICRO: 'this is a **Micro** release containing awesome new features that are expected to be adoptable with no additional effort.',
    ReleaseType.BUGFIX: 'this is a **Micro** release containing bug fixes, so we encourage upgrading.',
}
effver_info = f"""napari follows [EffVer (Intended Effort Versioning)](https://effver.org/); {effver_info.get(effver_type)}
"""

mentioned_pr_outside_sections = []

print(effver_info, file=file_handle)

for section, pull_request_dicts in highlights.items():
    section_path = (
        LOCAL_DIR
        / 'additional_notes'
        / args.milestone
        / f'{section.lower().replace(" ", "_")}.md'
    )

    if not section_path.exists() and not pull_request_dicts:
        continue

    print(f'## {section}\n', file=file_handle)

    mentioned_pr = set()
    if section_path.exists():
        with section_path.open(encoding='utf-8') as f:
            text = f.read()
        for owner, repo, pr_number in GITHUB_PR_LINK_PATTERN.findall(text):
            pr_info = PRInfo(user=owner, repo=repo, pr=int(pr_number))
            if pr_info not in pull_request_dicts:
                # raise ValueError(
                #     f'PR {pr_info} in {section_path} is not in the list of pull requests for this release.'
                # )
                mentioned_pr_outside_sections.append((pr_info, section))

            mentioned_pr.add(pr_info)
        print(text, file=file_handle)
        print('', file=file_handle)

    for pr_info, pull_request_info in sorted(
        pull_request_dicts.items(), key=lambda x: x[0]
    ):
        if (
            PRInfo(user=GH_USER, repo=pull_request_info['repo'], pr=pr_info.pr)
            in mentioned_pr
        ):
            continue
        repo_str = pull_request_info['repo']
        repo_prefix = repo_str if repo_str != 'napari' else ''
        print(
            f'- {pull_request_info["summary"]} ([{repo_prefix}#{pr_info.pr}]'
            f'(https://{GH}/{GH_USER}/{repo_str}/pull/{pr_info.pr}))',
            file=file_handle,
        )
    print('', file=file_handle)


contributors = {
    'authors': (authors | docs_authors, old_contributors),
    'reviewers': (reviewers | docs_reviewers, old_reviewers),
}

# ignore committers
# contributors['committers'] = committers

for section_name, (
    contributor_set,
    old_contributor_set,
) in contributors.items():
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

        first = ' +' if c not in old_contributor_set else ''
        commit_link = (
            f'https://{GH}/{GH_USER}/{first_repo_name}/commits?author={c}'
        )
        print(
            f'- [{users[c]}]({commit_link}){second_repo_str} - @{c}{first}',
            file=file_handle,
        )

if args.target_directory:
    toc_path = args.target_directory.parent / '_toc.yml'
    with open(toc_path) as f:
        toc = f.read()
    # add new notes to release
    new_version = args.milestone.replace('.', '_')
    if not re.search(rf'release_{new_version}', toc):
        toc = re.sub(
            r'(\s+- file: release/release)(.*)',
            rf'\1_{new_version}\1\2',
            toc,
            count=1,
        )
        with open(toc_path, 'w') as f:
            toc = f.write(toc)

if non_merged_pr:
    if len(non_merged_pr) == 1:
        pr = non_merged_pr[0]
        print(
            f"There is on unmerged PR ({pr.number} {pr.title} - {pr.html_url}). If it is release notes PR it's fine.",
            file=sys.stderr,
        )

    else:
        pr_info = [
            f'{pr.base.repo.full_name}#{pr.number} - {pr.title} {pr.html_url}'
            for pr in non_merged_pr
        ]
        print('#' * 50, file=sys.stderr)
        print(f'There are {len(non_merged_pr)} unmerged PRs:', file=sys.stderr)
        print('\n'.join(pr_info), file=sys.stderr)

if mentioned_pr_outside_sections:
    print(
        f'There are {len(mentioned_pr_outside_sections)} PRs mentioned in the release notes that do not have labels matching the sections:',
        file=sys.stderr,
    )
    for pr_info, section in mentioned_pr_outside_sections:
        section_labels = ', '.join(section_to_label[section])
        if len(section_to_label[section]) > 1:
            section_labels = f'one of the labels: {section_labels}'
        else:
            section_labels = f'the label: {section_labels}'

        file_name = f'{section.lower().replace(" ", "_")}.md'
        print(
            f'PR {pr_info.to_str()} in {file_name} does not have {section_labels} so should not be in this section. Please check its labels.',
            file=sys.stderr,
        )
