"""Integration test: Confluence folder lifecycle against the LIVE API.

Drives folders.py end to end: create a parent folder at the space root, create
a child folder under it, read it back, then move the child under a second parent
and verify the reparent. This is also where folder *move* support is actually
confirmed — the v2 folders API has no move endpoint, so folders.cmd_folder_move
falls back to the legacy content-move endpoint, which may or may not accept the
folder content type.

The skill intentionally has no `folder delete` command, so cleanup deletes the
created folders directly via the v2 API in a finally block.

Required env vars:
    ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN   (same as the skill)
    INTEGRATION_TEST_SPACE                                     (a space key you can write to, e.g. "~12345")

Run from the plugin root:
    INTEGRATION_TEST_SPACE='~12345' python3 -m unittest discover -s tests/integration -v

If INTEGRATION_TEST_SPACE (or any credential) is unset, the test is skipped.
Created folders are always cleaned up, even on failure.
"""
import os
import pathlib
import sys
import time
import unittest

REQUIRED_ENV = (
    "ATLASSIAN_BASE_URL",
    "ATLASSIAN_EMAIL",
    "ATLASSIAN_API_TOKEN",
    "INTEGRATION_TEST_SPACE",
)
_MISSING = [v for v in REQUIRED_ENV if not os.environ.get(v)]

ASSETS = pathlib.Path(__file__).resolve().parents[2] / "skills" / "confluence-api" / "assets"
sys.path.insert(0, str(ASSETS))


def _ns(**kw):
    import argparse

    return argparse.Namespace(**kw)


@unittest.skipIf(_MISSING, f"integration test requires env vars: {', '.join(_MISSING)}")
class FolderLifecycleIT(unittest.TestCase):
    def test_create_get_move(self):
        # Imported here (not at module top) so a missing credential skips the
        # test instead of triggering _client's hard exit during collection.
        import folders

        space = os.environ["INTEGRATION_TEST_SPACE"]
        suffix = f"{int(time.time())}-{os.getpid()}"

        created = []  # folder ids to clean up
        try:
            parent_a = folders.cmd_folder_create(
                _ns(space_key=space, space_id=None,
                    title=f"[itest A] {suffix}", parent_id=None)
            )
            created.append(parent_a["id"])

            parent_b = folders.cmd_folder_create(
                _ns(space_key=space, space_id=None,
                    title=f"[itest B] {suffix}", parent_id=None)
            )
            created.append(parent_b["id"])

            child = folders.cmd_folder_create(
                _ns(space_key=space, space_id=None,
                    title=f"[itest child] {suffix}", parent_id=parent_a["id"])
            )
            created.append(child["id"])

            # Read the child back; it should sit under parent A.
            fetched = folders.cmd_folder_get(_ns(folder_id=child["id"], children=False))
            self.assertEqual(str(fetched["parentId"]), str(parent_a["id"]))

            # Move the child under parent B and verify the reparent. This is the
            # real test of folder-move support via the legacy endpoint.
            folders.cmd_folder_move(
                _ns(folder_id=child["id"], target_id=parent_b["id"], position="append")
            )
            moved = folders.cmd_folder_get(_ns(folder_id=child["id"], children=False))
            self.assertEqual(str(moved["parentId"]), str(parent_b["id"]))
        finally:
            # The skill has no folder-delete command; clean up via the v2 API.
            session = folders._session()
            for folder_id in reversed(created):
                try:
                    session.delete(f"{folders.CONFLUENCE_BASE_URL}/api/v2/folders/{folder_id}")
                except Exception as exc:  # noqa: BLE001 - cleanup must not mask the real failure
                    print(f"cleanup warning: could not remove folder {folder_id}: {exc}")


if __name__ == "__main__":
    unittest.main()
