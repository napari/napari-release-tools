import argparse
from pathlib import Path

from yaml import safe_load
from tqdm import tqdm

from release_utils import (
    get_milestone,
    iter_pull_request,
    setup_cache,
    BOT_LIST,
    get_repo,
)

LOCAL_DIR = Path(__file__).parent


def existing_file(path: str) -> Path:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--milestone", help="The milestone to check")
    parser.add_argument(
        "--correction-file",
        help="The file with the corrections",
        default=LOCAL_DIR / "name_corrections.yaml",
    )
    parser.add_argument(
        "--citation-path",
        help="",
        default=str(LOCAL_DIR / "napari_repo" / "CITATION.cff"),
        type=existing_file,
    )
    parser.add_argument(
        "--generate",
        help="Generate the missing entries based on github data",
        action="store_true",
    )

    args = parser.parse_args()
    with args.citation_path.open() as f:
        citation = safe_load(f)

    if args.milestone is not None:
        missing_authors = find_missing_authors_for_milestone(citation, args.milestone)
    else:
        missing_authors = find_missing_authors(citation)

    if args.generate:
        for login, name in sorted(missing_authors):
            if name is None:
                continue
            name, sure_name = name.rsplit(" ", 1)
            print(f"- given-names: {name}\n  family-names: {sure_name}\n alias: {login}")
    else:
        for login, name in sorted(missing_authors):
            print(f"@{login} ", end="")  # ({name})")
    print()


def find_missing_authors(citation) -> set[tuple[str, str]]:
    author_dict = {}

    for author in citation["authors"]:
        author_dict[author['alias']] = author

    setup_cache()
    missing_authors = set()

    contributtors = get_repo().get_contributors()

    for creator in tqdm(contributtors, total=contributtors.totalCount):
        if creator.login in BOT_LIST:
            continue
        if creator.login not in author_dict:
            missing_authors.add((creator.login, creator.name))
    return missing_authors


def find_missing_authors_for_milestone(citation, milestone_str: str) -> set[tuple[str, str]]:
    author_dict = {}

    for author in citation["authors"]:
        author_dict[author['alias']] = author

    setup_cache()
    milestone = get_milestone(milestone_str)
    missing_authors = set()

    for pull in iter_pull_request(f"milestone:{milestone.title} is:merged"):
        issue = pull.as_issue()
        creator = issue.user
        if creator.login in BOT_LIST:
            continue
        if creator.login not in author_dict:
            missing_authors.add((creator.login, creator.name))
    return missing_authors


if __name__ == "__main__":
    main()
