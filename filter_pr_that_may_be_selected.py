"""
This is supporting script for generating list of PR that may be
cherry-picked for bugfix release.
"""
from __future__ import annotations

import argparse

from release_utils import (
    REPO_DIR_NAME,
    get_consumed_pr,
    get_local_repo,
    get_milestone,
    get_repo,
    get_split_date,
    iter_pull_request,
    pr_num_pattern,
    setup_cache,
    short_cache,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("from_commit", help="The starting tag.")
    parser.add_argument("to_commit", help="The head branch.")
    parser.add_argument(
        "--milestone",
        help="if present then filter PR with a given milestone",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--label",
        help="if present then filter PR with a given label",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--skip-triaged",
        action="store_true",
        default=False,
        help="if present then skip triaged PRs",
    )
    parser.add_argument("--target-branch", help="The target branch", default="")

    args = parser.parse_args()

    filter_pr(
        milestone_str=args.milestone,
        label=args.label,
        skip_triaged=args.skip_triaged,
        target_branch=args.target_branch,
        from_commit=args.from_commit,
        to_commit=args.to_commit,
    )


def filter_pr(
    milestone_str: str,
    label: str | None,
    skip_triaged: bool,
    target_branch: str,
    from_commit: str,
    to_commit: str,
):
    setup_cache()

    repository = get_repo()

    milestone = get_milestone(milestone_str)

    label = repository.get_label(label) if label else None

    repo = get_local_repo(REPO_DIR_NAME)
    consumed_pr = get_consumed_pr(repo, target_branch) if target_branch else set()

    if skip_triaged:
        triage_labels = [
            x for x in repository.get_labels() if x.name.startswith("triaged")
        ]
    else:
        triage_labels = []

    if milestone is not None:
        query = f"milestone:{milestone.title} is:merged "
    else:
        previous_tag_date = get_split_date(from_commit, to_commit)
        query = f"merged:>{previous_tag_date.isoformat()} no:milestone "

    if label is not None:
        query += f" label:{label.name} "

    with short_cache(60):
        iterable = iter_pull_request(query)

    pr_to_list = []

    for pull in sorted(iterable, key=lambda x: x.closed_at):
        if label is not None and label not in pull.labels:
            continue
        if skip_triaged and any(x in pull.labels for x in triage_labels):
            continue
        pr_to_list.append(pull)

    if not pr_to_list:
        text = (
            f"## No PRs found with milestone {milestone.title}"
            if milestone
            else "## No PRs found without milestone"
        )
    elif milestone:
        text = f"## {len(pr_to_list)} PRs with milestone {milestone.title}"
    else:
        text = f"## {len(pr_to_list)} PRs without milestone"

    if label:
        text += f" and label {label.name}"

    text += ":"
    print(text)

    for pull in sorted(pr_to_list, key=lambda x: x.closed_at):
        print(f' * [{"x" if pull.number in consumed_pr else " "}] #{pull.number}')


if __name__ == "__main__":
    main()
