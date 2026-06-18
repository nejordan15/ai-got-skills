"""Atlassian Confluence CLI — get/create/update pages directly via the REST API.

Usage:
  python3 confluence.py get      --page-id <id>  [--out body.html]
  python3 confluence.py create   --space-key '<space-key>' --title "..." --body-file body.html  [--parent-id <id>] [--from-markdown]
  python3 confluence.py update   --page-id <id> --body-file body.html  [--title "..."] [--message "..."] [--from-markdown] [--keep-appearance]

Env vars required: ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN.

Page width: create always sets new pages to wide via the library's
`full_width=True` parameter. update defaults to wide as well. Pass
--keep-appearance on update to read the page's current appearance pre-update
and preserve it (the underlying library writes a content-appearance value on
every update; --keep-appearance picks the right value based on the page's
existing state).
"""
import argparse
import pathlib
import sys

# Shared client lives at the plugin root: plugins/atlassian/lib/_client.py.
# From this file (…/skills/confluence-api/assets/confluence.py) that's parents[3]/lib.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "lib"))

from _client import confluence_client, CONFLUENCE_BASE_URL  # noqa: E402


APPEARANCE_KEYS = ("content-appearance-published", "content-appearance-draft")
WIDE_VALUES = ("max", "full-width")  # both render as wide layout in Confluence


def _is_wide(value):
    """Return True if the appearance value represents the wide layout."""
    return value in WIDE_VALUES


def _save_appearance(client, page_id):
    """Read current appearance values. Returns {key: value or None}."""
    out = {}
    for key in APPEARANCE_KEYS:
        try:
            prop = client.get_page_property(page_id, key)
            out[key] = prop.get("value")
        except Exception:
            out[key] = None
    return out


def cmd_get(args):
    client = confluence_client()
    page = client.get_page_by_id(args.page_id, expand="body.storage,version,space")
    print(
        f"id={page['id']}  title={page['title']}  "
        f"space={page['space']['key']}  version={page['version']['number']}"
    )
    body = page["body"]["storage"]["value"]
    if args.out:
        pathlib.Path(args.out).write_text(body)
        print(f"wrote storage-format body to {args.out} ({len(body)} chars)")
    else:
        print("--- body (storage, first 1000 chars) ---")
        print(body[:1000])
        if len(body) > 1000:
            print(f"... ({len(body)} chars total)")
    return page


def cmd_create(args):
    client = confluence_client()
    body = pathlib.Path(args.body_file).read_text()
    representation = "wiki" if args.from_markdown else "storage"
    # New pages always default to wide layout. Bundled into the single PUT
    # via the library's full_width=True parameter — no separate property write.
    page = client.create_page(
        space=args.space_key,
        title=args.title,
        body=body,
        parent_id=args.parent_id,
        representation=representation,
        full_width=True,
    )
    print(f"created page id={page['id']}  title={page['title']}")
    space_key = page.get("space", {}).get("key", args.space_key)
    print(f"url: {CONFLUENCE_BASE_URL}/spaces/{space_key}/pages/{page['id']}")
    return page


def cmd_update(args):
    client = confluence_client()
    body = pathlib.Path(args.body_file).read_text()
    representation = "wiki" if args.from_markdown else "storage"
    title = args.title
    if not title:
        current = client.get_page_by_id(args.page_id)
        title = current["title"]

    # Default: full_width=True — sets the page to wide via the single PUT.
    # With --keep-appearance: read current appearance and preserve it
    # (wide if either appearance property currently holds a wide value,
    # else narrow).
    full_width = True
    if args.keep_appearance:
        saved = _save_appearance(client, args.page_id)
        full_width = any(_is_wide(v) for v in saved.values())

    page = client.update_page(
        page_id=args.page_id,
        title=title,
        body=body,
        representation=representation,
        version_comment=args.message or "Updated via confluence-api skill",
        full_width=full_width,
    )
    print(
        f"updated page id={page['id']}  title={page['title']}  "
        f"version={page['version']['number']}  "
        f"width={'wide' if full_width else 'narrow'}"
    )
    return page


def cmd_move(args):
    client = confluence_client()
    # Re-parent the page under target_id within the space. position controls
    # ordering among siblings (append = last child of the new parent).
    result = client.move_page(
        space_key=args.space_key,
        page_id=args.page_id,
        target_id=args.target_id,
        position=args.position,
    )
    print(
        f"moved page id={args.page_id} under target_id={args.target_id} "
        f"(position={args.position})"
    )
    return result


def cmd_delete(args):
    client = confluence_client()
    client.remove_page(args.page_id, recursive=args.recursive)
    print(f"deleted page id={args.page_id} (recursive={args.recursive})")
    return args.page_id


def main():
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="Fetch a page by ID")
    g.add_argument("--page-id", required=True)
    g.add_argument("--out", help="write storage-format body to this file")
    g.set_defaults(func=cmd_get)

    c = sub.add_parser("create", help="Create a new page")
    c.add_argument("--space-key", required=True)
    c.add_argument("--title", required=True)
    c.add_argument("--body-file", required=True)
    c.add_argument("--parent-id")
    c.add_argument(
        "--from-markdown",
        action="store_true",
        help="treat body as wiki markup / markdown; Confluence converts to storage server-side",
    )
    c.set_defaults(func=cmd_create)

    u = sub.add_parser("update", help="Update an existing page")
    u.add_argument("--page-id", required=True)
    u.add_argument("--body-file", required=True)
    u.add_argument("--title", help="defaults to current page title")
    u.add_argument("--message", help="version comment shown in page history")
    u.add_argument("--from-markdown", action="store_true")
    u.add_argument(
        "--keep-appearance",
        action="store_true",
        help="preserve the page's existing content-appearance setting "
             "(default: force to wide via full_width=True)",
    )
    u.set_defaults(func=cmd_update)

    m = sub.add_parser("move", help="Move a page under a new parent")
    m.add_argument("--page-id", required=True)
    m.add_argument("--space-key", required=True)
    m.add_argument("--target-id", required=True, help="new parent page id")
    m.add_argument(
        "--position",
        default="append",
        choices=("append", "above", "below"),
        help="placement relative to the target (default: append as last child)",
    )
    m.set_defaults(func=cmd_move)

    d = sub.add_parser("delete", help="Delete (trash) a page")
    d.add_argument("--page-id", required=True)
    d.add_argument(
        "--recursive",
        action="store_true",
        help="also delete child pages",
    )
    d.set_defaults(func=cmd_delete)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
