# Napari release tools

This repository contains tools for simplifying releasing napari.

## Configuration

The tools are using following environment variables for configuration:

* `GH` - point to github server, default to `github.com`
* `GH_USER` - name of organization that holds the repositories, default to `napari`
* `GH_REPO` - main repository, default to `napari`
* `GH_DOCS_REPO` - docs repository, default to `docs`
* `GH_TOKEN` token to authorize with github. Need to be provided by user.


## Available tools

### `generate_release_notes.py`

This tool generates release notes for a new release. It uses github API to get list of merged PRs tagged with given milestone since last release. Uses `name_correction.yml` to provide proper user name in the release notes.

### `cherry_pick_process.py`

This tools analyses list of PR already merged into provided branch and try to cherry pick missed one from the main branch. When the merge conflict happens, then it calls `git mergetool` to allow user resolve it. After resolving the conflict, the tool will continue cherry picking.


### `docs_cherry_pick.py`

This is tool for cherry pick commits form docs repo to mian repo. May be useful in transition process. It uses patch files so may need more manual intervention than cherry pick between branches.
It requires that sorce repo does not use `lfs` and target repo disable `lfs` for the duration of the process.

### `find_contributors_without_citations.py`

Check if all contributors to a given release are cited in the CITATION.cff file. Uses `name_correction.yml` for support user that have different name in github and in CITATION.cff file.

### `sort_citation_cff.py`

Simple tool for sort authors in CITATION.cff file by `family-names` field.


### `filter_opened_bug_issues.py`

Find issues with bug label and given milestone.

### `filter_pr_that_may_be_selected.py`

Filter PR that satisfy given set of conditions. For simplify triage process.

### `list_opened_pr.py`

List opened PRs with given milestone.

### `generate_issue_content.py`

Generate content for issue to trace progress of release.
