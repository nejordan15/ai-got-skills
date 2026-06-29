"""Atlassian Confluence CLI — pages and folders, directly via the REST API.

This is a thin dispatcher. The actual commands live in two backends in this
same directory:
  - pages.py    page commands (get/create/update/move/delete), via the
                atlassian-python-api library.
  - folders.py  folder commands (folder create/get/move), via the v2 REST API
                directly (the library does not wrap the folder content type).

Usage:
  python3 confluence.py get      --page-id <id>  [--out body.html]
  python3 confluence.py create   --space-key '<key>' --title "..." --body-file body.html  [--parent-id <id>] [--from-markdown]
  python3 confluence.py update   --page-id <id> --body-file body.html  [--title "..."] [--message "..."] [--from-markdown] [--keep-appearance]
  python3 confluence.py move     --page-id <id> --space-key '<key>' --target-id <id>  [--position append|above|below]
  python3 confluence.py delete   --page-id <id>  [--recursive]
  python3 confluence.py folder create --space-key '<key>' --title "..."  [--parent-id <id>]
  python3 confluence.py folder get    --folder-id <id>  [--children]
  python3 confluence.py folder move   --folder-id <id> --target-id <id>  [--position append|above|below]

Env vars required: ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN.
"""
import argparse

import folders
import pages


def main():
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pages.add_parsers(sub)
    folders.add_parsers(sub)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
