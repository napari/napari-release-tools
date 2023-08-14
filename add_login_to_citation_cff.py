"""
This is a script for adding logins to the existing CITATION.cff file.
This simplifies future updating of this file. It creates a backup file with .bck suffix/
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from tqdm import tqdm
from unidecode import unidecode
from yaml import safe_dump, safe_load

from release_utils import BOT_LIST, existing_file, get_repo, setup_cache

LOCAL_DIR = Path(__file__).parent
DEFAULT_CORRECTION_FILE = LOCAL_DIR / "name_corrections.yaml"


def get_correction_dict(file_path: Path | None) -> dict[str, str]:
    """
    Read file with correction of name between
    """
    if not file_path or not file_path.exists():
        return {}

    correction_dict = {}
    with open(file_path) as f:
        corrections = safe_load(f)
        for correction in corrections["login_to_name"]:
            correction_dict[correction["login"]] = unidecode(
                correction["corrected_name"].lower()
            )

    return correction_dict


def get_corrections_from_citation_cff(cff_dict):
    res = {}
    for author in cff_dict["authors"]:
        if "alias" in author:
            res[author["alias"]] = unidecode(
                f'{author["given-names"]} {author["family-names"]}'.lower()
            )
    return res


def get_name(user, correction_dict):
    if user.login in correction_dict:
        return correction_dict[user.login]
    if user.name is None:
        return None
    return unidecode(user.name.lower())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="The path to the citation file to sort", type=Path)
    parser.add_argument(
        "--correction-file",
        help="The file with the corrections",
        default=DEFAULT_CORRECTION_FILE,
        type=existing_file,
    )
    parser.parse_args()


def add_logins(cff_path: Path, correction_file: Path | None = None) -> None:
    setup_cache()

    with cff_path.open(encoding="utf8") as f:
        data = safe_load(f)

    contributors_iterable = get_repo().get_contributors()

    correction_dict = get_correction_dict(
        correction_file
    ) | get_corrections_from_citation_cff(data)

    contributors = {
        get_name(user, correction_dict): user
        for user in tqdm(contributors_iterable, total=contributors_iterable.totalCount)
        if get_name(user, correction_dict) is not None
    }

    for user in get_repo().get_contributors():
        if get_name(user, correction_dict) is None and user.login not in BOT_LIST:
            print(f"Could not find {user.login}", file=sys.stderr)

    # assert len(contributors) == contributors_iterable.totalCount

    for i, author in enumerate(data["authors"]):
        if "alias" in author:
            continue
        name = unidecode(f'{author["given-names"]} {author["family-names"]}'.lower())
        if name in contributors:
            author["alias"] = contributors[name].login
        else:
            print(f"Could not find {name}", file=sys.stderr)

    shutil.copy(str(cff_path), f"{cff_path}.bck")

    with cff_path.open("w", encoding="utf8") as f:
        safe_dump(data, f, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    main()
