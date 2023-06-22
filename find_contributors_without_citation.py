import argparse
import sys
from pathlib import Path

from tqdm import tqdm

from yaml import safe_load

from release_utils import (
    setup_cache,
    get_milestone,
    iter_pull_request,
)

LOCAL_DIR = Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument('milestone', help='The milestone to check')
parser.add_argument("--correction-file", help="The file with the corrections", default=LOCAL_DIR / "name_corrections.yaml")
parser.add_argument("--citation-path", help="", default=LOCAL_DIR / "napari_repo" / "CITATION.cff", type=Path)

args = parser.parse_args()


if not args.citation_path.exists():
    raise FileNotFoundError("Citation file not found")

with args.citation_path.open() as f:
    citation = safe_load(f)

author_dict = {}

for author in citation["authors"]:
    author_dict[f"{author['given-names']} {author['family-names']}"] = author

correction_dict = {}
with open(args.correction_file) as f:
    corrections = safe_load(f)
    for correction in corrections["login_to_name"]:
        correction_dict[correction["login"]] = correction["corrected_name"]



print(citation)

setup_cache()

milestone = get_milestone(args.milestone)

missing_authors = set()


for pull in iter_pull_request(f"milestone:{args.milestone} is:merged"):
    issue = pull.as_issue()
    creator = issue.user
    if creator.login in {"github-actions[bot]", "pre-commit-ci[bot]", "dependabot[bot]", "napari-bot"}:
        continue
    if correction_dict.get(creator.login, creator.name) not in author_dict:
        missing_authors.add((creator.login, creator.name))

for login, name in sorted(missing_authors):
    print(f"@{login} ", end="")# ({name})")
