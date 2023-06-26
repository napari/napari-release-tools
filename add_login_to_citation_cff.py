import argparse
from pathlib import Path

from yaml import safe_dump, safe_load
from tqdm import tqdm
from unidecode import unidecode

from release_utils import get_repo, setup_cache, BOT_LIST

LOCAL_DIR = Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument("path", help="The path to the citation file to sort", type=Path)
parser.add_argument(
    "--correction-file",
    help="The file with the corrections",
    default=LOCAL_DIR / "name_corrections.yaml",
)
args = parser.parse_args()

setup_cache()


with args.path.open(encoding="utf8") as f:
    data = safe_load(f)

contributors_iterable = get_repo().get_contributors()

correction_dict = {}
with open(args.correction_file) as f:
    corrections = safe_load(f)
    for correction in corrections["login_to_name"]:
        correction_dict[correction["login"]] = unidecode(correction["corrected_name"].lower())


def get_name(user):
    if user.login in correction_dict:
        return correction_dict[user.login]
    if user.name is None:
        return None
    return unidecode(user.name.lower())


contributors = { get_name(user): user for user in
    tqdm(contributors_iterable, total=contributors_iterable.totalCount) if get_name(user) is not None
}

for user in get_repo().get_contributors():
    if get_name(user) is None  and user.login not in BOT_LIST:
        print(f"Could not find {user.login}")

# assert len(contributors) == contributors_iterable.totalCount


for i, author in enumerate(data["authors"]):
    if "alias" in author:
        continue
    name = unidecode(f'{author["given-names"]} {author["family-names"]}'.lower())
    if name in contributors:
        author["alias"] = contributors[name].login
    else:
        print(f"Could not find {name}")


with args.path.open("w", encoding="utf8") as f:
    safe_dump(data, f, sort_keys=False, allow_unicode=True)
