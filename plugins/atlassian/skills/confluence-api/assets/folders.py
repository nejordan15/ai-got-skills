"""Confluence folder commands — create/get/move via the REST API directly.

Folders are a distinct Confluence content type that the atlassian-python-api
library does not wrap, so this module talks to the v2 REST API
(/wiki/api/v2/folders) over its own authenticated requests.Session, built
from the same ATLASSIAN_* env vars as the page commands.

Note on move: the v2 folders API has no move/reparent endpoint, so folder
move reuses the legacy content-move endpoint that page move also uses
(PUT /wiki/rest/api/content/{id}/move/{position}/{targetId}).

Registered into the top-level CLI by confluence.py via add_parsers().
"""
import pathlib
import sys

import requests

# Shared client constants live at the plugin root: plugins/atlassian/lib/_client.py.
# From this file (…/skills/confluence-api/assets/folders.py) that's parents[3]/lib.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "lib"))

from _client import (  # noqa: E402
    CONFLUENCE_BASE_URL,
    ATLASSIAN_EMAIL,
    ATLASSIAN_API_TOKEN,
)


def _session():
    """A requests.Session pre-configured with HTTP Basic auth and JSON headers."""
    s = requests.Session()
    s.auth = (ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)
    s.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    return s


def _check(resp):
    """Raise with status + body on a non-2xx response; else return the response."""
    if not (200 <= resp.status_code < 300):
        raise SystemExit(
            f"error: {resp.request.method} {resp.url} -> {resp.status_code}\n{resp.text}"
        )
    return resp


def _resolve_space_id(session, space_key):
    """Resolve a space key (e.g. 'RATE') to its numeric space id."""
    resp = _check(
        session.get(
            f"{CONFLUENCE_BASE_URL}/api/v2/spaces",
            params={"keys": space_key, "limit": 1},
        )
    )
    results = resp.json().get("results", [])
    if not results:
        raise SystemExit(f"error: no space found for key {space_key!r}")
    return results[0]["id"]


def cmd_folder_create(args):
    session = _session()
    space_id = args.space_id or _resolve_space_id(session, args.space_key)
    payload = {"spaceId": str(space_id), "title": args.title}
    if args.parent_id:
        payload["parentId"] = str(args.parent_id)

    resp = _check(session.post(f"{CONFLUENCE_BASE_URL}/api/v2/folders", json=payload))
    folder = resp.json()
    print(
        f"created folder id={folder['id']}  title={folder['title']}  "
        f"parentId={folder.get('parentId')}"
    )
    webui = folder.get("_links", {}).get("webui")
    if webui:
        print(f"url: {CONFLUENCE_BASE_URL}{webui}")
    return folder


def cmd_folder_get(args):
    session = _session()
    params = {}
    if args.children:
        params["include-direct-children"] = "true"
    resp = _check(
        session.get(
            f"{CONFLUENCE_BASE_URL}/api/v2/folders/{args.folder_id}", params=params
        )
    )
    folder = resp.json()
    print(
        f"id={folder['id']}  title={folder['title']}  "
        f"spaceId={folder.get('spaceId')}  parentId={folder.get('parentId')}  "
        f"parentType={folder.get('parentType')}"
    )
    if args.children:
        # The v2 folder response nests children under "directChildren".
        children = folder.get("directChildren", {}).get("results", [])
        print(f"--- direct children ({len(children)}) ---")
        for child in children:
            print(f"  {child.get('type')}  id={child.get('id')}  {child.get('title')}")
    return folder


def cmd_folder_move(args):
    session = _session()
    # v2 has no folder move endpoint; reuse the legacy content-move endpoint
    # (the same one the library's move_page uses for pages).
    resp = _check(
        session.put(
            f"{CONFLUENCE_BASE_URL}/rest/api/content/{args.folder_id}"
            f"/move/{args.position}/{args.target_id}"
        )
    )
    print(
        f"moved folder id={args.folder_id} under target_id={args.target_id} "
        f"(position={args.position})"
    )
    return resp.json() if resp.text else {}


def add_parsers(sub):
    """Register the `folder` command group on the shared subparsers object."""
    folder = sub.add_parser("folder", help="Manage Confluence folders (v2 API)")
    fsub = folder.add_subparsers(dest="folder_cmd", required=True)

    c = fsub.add_parser("create", help="Create a folder")
    src = c.add_mutually_exclusive_group(required=True)
    src.add_argument("--space-key", help="space key (e.g. RATE); resolved to a space id")
    src.add_argument("--space-id", help="numeric space id (skips the key lookup)")
    c.add_argument("--title", required=True)
    c.add_argument("--parent-id", help="parent page or folder id (omit for space root)")
    c.set_defaults(func=cmd_folder_create)

    g = fsub.add_parser("get", help="Fetch a folder by ID")
    g.add_argument("--folder-id", required=True)
    g.add_argument(
        "--children",
        action="store_true",
        help="include the folder's direct children",
    )
    g.set_defaults(func=cmd_folder_get)

    m = fsub.add_parser("move", help="Move a folder under a new parent")
    m.add_argument("--folder-id", required=True)
    m.add_argument("--target-id", required=True, help="new parent page or folder id")
    m.add_argument(
        "--position",
        default="append",
        choices=("append", "above", "below"),
        help="placement relative to the target (default: append as last child)",
    )
    m.set_defaults(func=cmd_folder_move)
