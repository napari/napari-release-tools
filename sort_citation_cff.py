"""
Sort CITATION.cff files by author family-name.
"""
import argparse
from pathlib import Path

from yaml import safe_dump, safe_load

parser = argparse.ArgumentParser()
parser.add_argument("path", help="The path to the citation file to sort", type=Path)


args = parser.parse_args()


with args.path.open(encoding="utf8") as f:
    data = safe_load(f)


def reorder_author_fields(author):
    res = {}
    for key in ["given-names", "family-names", "affiliation", "orcid"]:
        if key in author:
            res[key] = author[key]
    return res


data["authors"] = [
    reorder_author_fields(x)
    for x in sorted(data["authors"], key=lambda x: x["family-names"])
]


with args.path.open("w", encoding="utf8") as f:
    safe_dump(data, f, sort_keys=False, allow_unicode=True)
