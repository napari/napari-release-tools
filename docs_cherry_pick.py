"""
To ge files from LFS to apply patch use `git add --renormalize .`
"""

import argparse
import os
from pathlib import Path
import urllib.request

from git import GitCommandError, Repo
from tqdm import tqdm

from release_utils import (
    get_milestone,
    iter_pull_request,
    pr_num_pattern,
    setup_cache,
    GH, GH_REPO, GH_USER,
    get_repo
)


def get_pr_commits_dict():
    res = {}

    for commit in repo.iter_commits("main"):
        if (match := pr_num_pattern.search(commit.message)) is not None:
            pr_num = int(match[1])
            res[pr_num] = commit.hexsha

    return res


def get_consumed_pr():
    res = set()

    for commit in repo.iter_commits(target_branch):
        if (match := pr_num_pattern.search(commit.message)) is not None:
            pr_num = int(match[1])
            res.add(pr_num)
    return res


parser = argparse.ArgumentParser()
parser.add_argument('milestone', help='The milestone to list')
parser.add_argument(
    '--first-commits', help='file with list of first commits to cherry pick'
)
parser.add_argument(
    '--stop-after', help='Stop after this commit', default=0, type=int
)
parser.add_argument(
    "--git-repository",
    help="The git repository",
    default=os.environ.get(
        "GIT_RELEASE_REPOSITORY", "git@github.com:napari/napari.git"
    ),
)

parser.add_argument(
    "--git-main-branch",
    help="The git main branch",
    default=os.environ.get("GIT_RELEASE_MAIN_BRANCH", "main"),
)

def get_consumed_pr():
    res = set()

    base = repo.merge_base(f"docs_{milestone.title}", f"v{milestone.title}x")

    for commit in repo.iter_commits(f"{base[0].binsha.hex()}..docs_{milestone.title}"):
        if (match := pr_num_pattern.search(commit.message)) is not None:
            pr_num = int(match[1])
            res.add(pr_num)
    return res

LOCAL_DIR = Path(__file__).parent.absolute()

args = parser.parse_args()

setup_cache()

milestone = get_milestone(args.milestone)

if not (LOCAL_DIR / "patch_dir").exists():
    (LOCAL_DIR / "patch_dir").mkdir()

patch_dir_path =  LOCAL_DIR / "patch_dir" / f"docs_{milestone.title}"

if not patch_dir_path.exists():
    patch_dir_path.mkdir()


repo = Repo(LOCAL_DIR / "napari_repo")
repo.git.checkout(f"docs_{milestone.title}")


pr_list_base = sorted(
    iter_pull_request(f"milestone:{args.milestone} is:merged", repo="docs"),
    key=lambda x: x.closed_at,  
    )

skip_pr = {58, 106, 149, 151, 181, 175} | get_consumed_pr()


for pull in tqdm(pr_list_base):
    patch_file = patch_dir_path / f"{pull.number}.patch"
    if pull.number in skip_pr:
        continue
    
    print(pull.number, pull.title)
    if not patch_file.exists():
        urllib.request.urlretrieve(f"https://github.com/napari/docs/commit/{pull.merge_commit_sha}.patch", patch_file)
    repo.git.am(str(patch_file))