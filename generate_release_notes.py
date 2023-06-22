"""Generate the release notes automatically from Github pull requests.
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
import os
import re
import sys
from datetime import datetime
from itertools import chain
from os.path import abspath
from pathlib import Path
from warnings import warn

from yaml import safe_load

from git import Repo
from github import Github

from release_utils import setup_cache, short_cache, iter_pull_request, get_repo, BOT_LIST, GH, GH_REPO, GH_USER


LOCAL_DIR = Path(__file__).parent


parser = argparse.ArgumentParser(usage=__doc__)
parser.add_argument('milestone', help='The milestone to list')
parser.add_argument("--correction-file", help="The file with the corrections", default=LOCAL_DIR / "name_corrections.yaml")

args = parser.parse_args()


setup_cache()
repo = get_repo()

correction_dict = {}
with open(args.correction_file) as f:
    corrections = safe_load(f)
    for correction in corrections["login_to_name"]:
        correction_dict[correction["login"]] = correction["corrected_name"]


def add_to_users(users, new_user):
    if new_user.login in users:
        # reduce obsolete requests to GitHub API
        return
    if new_user.login in correction_dict:
        users[new_user.login] = correction_dict[new_user.login]
    elif new_user.name is None:
        users[new_user.login] = new_user.login
    else:
        users[new_user.login] = new_user.name


authors = set()
committers = set()
reviewers = set()
users = {}

highlights = {}

highlights['Highlights'] = {}
highlights['New Features'] = {}
highlights['Improvements'] = {}
highlights["Performance"] = {}
highlights['Bug Fixes'] = {}
highlights['API Changes'] = {}
highlights['Deprecations'] = {}
highlights['Build Tools'] = {}
highlights['Documentation'] = {}
other_pull_requests = {}

label_to_section = {
    "bug": "Bug Fixes",
    "bugfix": "Bug Fixes",
    "feature": "New Features",
    "api": "API Changes",
    "highlight": "Highlights",
    "performance": "Performance",
    "enhancement": "Improvements",
    "deprecation": "Deprecations",
    "dependencies": "Build Tools",
    "documentation": "Documentation",
}


for pull in iter_pull_request(f"milestone:{args.milestone} is:merged"):
    issue = pull.as_issue()
    assert pull.merged 

    commit = repo.get_commit(pull.merge_commit_sha)

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
    pr_lables = {label.name.lower() for label in pull.labels}
    for label_name, section in label_to_section.items():
        if label_name in pr_lables:
            highlights[section][pull.number] = {'summary': summary}
            assigned_to_section = True

    if not assigned_to_section:
        other_pull_requests[pull.number] = {'summary': summary}


# add Other PRs to the ordered dict to make doc generation easier.
highlights['Other Pull Requests'] = other_pull_requests


# remove these bots.
committers -= BOT_LIST
authors  -= BOT_LIST


# Now generate the release notes
title = f'# napari {args.milestone}'
print(title)

print(
    f"""
We're happy to announce the release of napari {args.milestone}!
napari is a fast, interactive, multi-dimensional image viewer for Python.
It's designed for browsing, annotating, and analyzing large multi-dimensional
images. It's built on top of Qt (for the GUI), vispy (for performant GPU-based
rendering), and the scientific Python stack (numpy, scipy).
"""
)

print(
    """
For more information, examples, and documentation, please visit our website:
https://github.com/napari/napari
"""
)

for section, pull_request_dicts in highlights.items():
    print(f'## {section}\n')
    for number, pull_request_info in pull_request_dicts.items():
        print(f'- {pull_request_info["summary"]} (#{number})')
    print()


contributors = {}

contributors['authors'] = authors
contributors['reviewers'] = reviewers
# ignore committers
# contributors['committers'] = committers

for section_name, contributor_set in contributors.items():
    print()
    if None in contributor_set:
        contributor_set.remove(None)
    committer_str = (
        f'## {len(contributor_set)} {section_name} added to this '
        'release (alphabetical)'
    )
    print(committer_str)
    print()

    for c in sorted(contributor_set, key=lambda x: users[x].lower()):
        commit_link = f"{GH}/{GH_USER}/{GH_REPO}/commits?author={c}"
        print(f"- [{users[c]}]({commit_link}) - @{c}")
    print()
