# PYTHON_ARGCOMPLETE_OK
"""
This is script to cherry-pick commits base on PR labels
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import argcomplete
from git import GitCommandError, Repo
from tqdm import tqdm

from release_utils import (
    GH,
    GH_REPO,
    GH_USER,
    LOCAL_DIR,
    REPO_DIR_NAME,
    get_consumed_pr,
    get_milestone,
    get_pr_commits_dict,
    iter_pull_request,
    setup_cache,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_branch", help="The base branch.")
    parser.add_argument("milestone", help="The milestone to list")
    parser.add_argument(
        "--first-commits", help="file with list of first commits to cherry pick"
    )
    parser.add_argument(
        "--stop-after", help="Stop after this PR", default=0, type=int
    )
    parser.add_argument(
        "--git-main-branch",
        help="The git main branch",
        default=os.environ.get("GIT_RELEASE_MAIN_BRANCH", "main"),
    )

    parser.add_argument(
        "--working-dir", help="path to repository", default=LOCAL_DIR, type=Path
    )
    parser.add_argument(
        "--skip-commits", nargs="+", help="list of commits to skip as they are already cherry-picked", type=int
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    target_branch = f"v{args.milestone}x"

    if args.first_commits is not None:
        with open(args.first_commits) as f:
            first_commits = {int(el) for el in f.read().splitlines()}
    else:
        first_commits = set()

    perform_cherry_pick(
        working_dir=args.working_dir,
        target_branch=target_branch,
        milestone_str=args.milestone,
        first_commits=first_commits,
        stop_after=args.stop_after,
        base_branch=args.base_branch,
        main_branch=args.git_main_branch,
        skip_commits=args.skip_commits,
    )


def prepare_repo(
    working_dir: Path, target_branch: str, base_branch: str, main_branch: str = "main"
) -> Repo:
    if not working_dir.exists():
        repo = Repo.clone_from(f"git@{GH}:{GH_USER}/{GH_REPO}.git", working_dir)
    else:
        repo = Repo(LOCAL_DIR / REPO_DIR_NAME)

    if target_branch not in repo.branches:
        repo.git.checkout(base_branch)
        repo.git.checkout("HEAD", b=target_branch)
    else:
        repo.git.reset("--hard", "HEAD")
        repo.git.checkout(main_branch)
        repo.git.pull()
        repo.git.checkout(target_branch)
        # repo.git.pull()

    return repo


def perform_cherry_pick(
    working_dir: Path,
    target_branch: str,
    milestone_str: str,
    first_commits: set,
    stop_after: int | None,
    base_branch: str,
    main_branch: str = "main",
    skip_commits: list[int] = None,
):
    """
    Perform cherry-pick process

    Parameters
    ----------
    working_dir: Path
        Path to working directory
    target_branch: str
        branch that is target for cherry-pick process
    milestone_str: str
        name of milestone to which will be released
    first_commits: set[int]
        set of commit that need to ben cherry-picked on begin, for example fixes for CI
    stop_after: int | None
        PR number after which cherry-pick process should be stopped
    base_branch: str
        branch or commit where target branch will be created if missed
    main_branch: str
        the main branch of repository, by default is ``main``
        but could be for example ``master``
    skip_commits: list[int]
        list of commits to skip as they are already cherry-picked

    Returns
    -------
    Nothing
    """
    repo = prepare_repo(
        working_dir=working_dir / REPO_DIR_NAME,
        target_branch=target_branch,
        base_branch=base_branch,
        main_branch=main_branch,
    )

    setup_cache()

    milestone = get_milestone(milestone_str)
    patch_dir_path = working_dir / "patch_dir" / milestone.title
    patch_dir_path.mkdir(parents=True, exist_ok=True)

    # with short_cache(60):
    pr_targeted_for_release = [
        x
        for x in iter_pull_request(f"milestone:{milestone.title} is:merged")
        if x.milestone == milestone
    ]

    pr_commits_dict = get_pr_commits_dict(repo, main_branch)
    consumed_pr = get_consumed_pr(repo, target_branch)

    if skip_commits:
        consumed_pr.update(skip_commits)

    # check for errors, may require to reset cache if happens
    for el in pr_targeted_for_release:
        assert el.closed_at is not None, el

    # order PR by merge date, move "first_commits" to begin
    # (by default PR are ordered by creation date)
    pr_list_base = sorted(
        pr_targeted_for_release,
        key=lambda x: (x.number not in first_commits, x.closed_at),
    )

    # list of PR to cherry pic in this run
    pr_list = []

    for pr in pr_list_base:
        pr_list.append(pr)
        if pr.number == stop_after:
            break

    # print already cherry-picked PR
    for el in pr_list:
        if el.number in consumed_pr:
            print(el, el.number in consumed_pr)


    for pull in tqdm(pr_list):
        if pull.number in consumed_pr:
            continue
        # commit = repo.commit(pr_commits_dict[pull.number])
        # print("hash",  pr_commits_dict[pull.number])
        # break
        patch_file = patch_dir_path / f"{pull.number}.patch"
        if patch_file.exists():
            print(f"Apply patch {patch_file}")
            repo.git.am(str(patch_file))
            continue
        try:
            repo.git.cherry_pick(pr_commits_dict[pull.number])
        except GitCommandError:
            print(pull, pr_commits_dict[pull.number])
            repo.git.mergetool()
            repo.git.cherry_pick("--continue")
            with open(patch_file, "w") as f:
                f.write(repo.git.format_patch("HEAD~1", "--stdout"))


if __name__ == "__main__":
    main()
