"""
Find contributors without citation in the CITATION.cff file.

This script could work in two modes:

1. Find missed contributors fo a given milestone
2. Find missed contributors for the whole project

When pass `--generate` option then script will generate
the missing entries based on GitHub data.

A GH_TOKEN environment variable must be set for this to work.

Example usage:
```
python find_contributors_without_citation.py --citation-path ../napari/CITATION.cff --generate --milestone 0.6.2
```
"""

import argparse
import os

from tqdm import tqdm
from yaml import safe_load

from release_utils import (
    BOT_LIST,
    LOCAL_DIR,
    REPO_DIR_NAME,
    existing_file,
    get_milestone,
    get_repo,
    iter_pull_request,
    setup_cache,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--milestone', help='The milestone to check', default=''
    )
    parser.add_argument('--repo', help='The repo to check', action='append')
    # parser.add_argument(
    #     "--additional-repo", help="The additional repo to check", action="append"
    # )
    parser.add_argument(
        '--correction-file',
        help='The file with the corrections',
        default=LOCAL_DIR / 'name_corrections.yaml',
    )
    parser.add_argument(
        '--citation-path',
        help='',
        default=str(os.path.join(REPO_DIR_NAME, 'CITATION.cff')),
        type=existing_file,
    )
    parser.add_argument(
        '--generate',
        help='Generate the missing entries based on github data',
        action='store_true',
    )

    args = parser.parse_args()
    if args.repo is None:
        args.repo = ['napari/napari', 'napari/docs']

    with args.citation_path.open() as f:
        citation = safe_load(f)

    repo_missing_authors = {}
    total_missing_authors = set()

    for repo in args.repo:
        missing = find_missing_authors_for_milestone(
            citation, repo, args.milestone
        )
        repo_missing_authors[repo] = missing
        total_missing_authors |= missing
        print(f"Repo '{repo}' has {len(missing)} missing contributors.")

    if args.generate:
        for login, name in sorted(total_missing_authors):
            if name is None:
                continue
            parts = name.rsplit(' ', 1)
            if len(parts) == 2:
                given_names, family_names = parts
            else:
                given_names = parts[0]
                family_names = ''
            print(
                f'- given-names: {given_names}\n  family-names: {family_names}\n alias: {login}'
            )
    else:
        for login, name in sorted(total_missing_authors):
            print(f'@{login} ', end='')  # ({name})")
    print()


def find_missing_authors(citation, repository: str) -> set[tuple[str, str]]:
    author_dict = {}

    for author in citation['authors']:
        author_dict[author['alias']] = author

    setup_cache()
    missing_authors = set()

    contributors = get_repo(*repository.split('/')).get_contributors()

    for creator in tqdm(
        contributors,
        total=contributors.totalCount,
        desc=f'finding authors for {repository}',
    ):
        if creator.login in BOT_LIST:
            continue
        if creator.login not in author_dict:
            missing_authors.add((creator.login, creator.name))
    return missing_authors


def find_missing_authors_for_milestone(
    citation, repository: str, milestone_str: str = ''
) -> set[tuple[str, str]]:
    if not milestone_str:
        return find_missing_authors(citation, repository)

    author_dict = {}

    for author in citation['authors']:
        author_dict[author['alias']] = author

    setup_cache()
    milestone = get_milestone(milestone_str, repository)
    missing_authors = set()

    user, repo = repository.split('/')

    for pull in iter_pull_request(
        f'milestone:{milestone.title} is:merged', user, repo
    ):
        issue = pull.as_issue()
        creator = issue.user
        if creator.login in BOT_LIST:
            continue
        if creator.login not in author_dict:
            missing_authors.add((creator.login, creator.name))
    return missing_authors


if __name__ == '__main__':
    main()
