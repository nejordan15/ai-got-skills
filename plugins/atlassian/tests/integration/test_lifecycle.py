"""Integration test: full Confluence page lifecycle against the LIVE API.

Drives the confluence-api script's cmd_* functions end to end:
create → update → read → move → delete. This really creates and deletes
pages, so it only runs when the required env vars are set.

Required env vars:
    ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN   (same as the skill)
    INTEGRATION_TEST_SPACE                                     (a space key you can write to, e.g. "~12345" or "DOCS")

Run from the plugin root:
    INTEGRATION_TEST_SPACE=DOCS python3 -m unittest discover -s tests/integration -v

If INTEGRATION_TEST_SPACE (or any credential) is unset, the test is skipped.
Created pages are always cleaned up, even on failure.
"""
import os
import pathlib
import sys
import tempfile
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
class ConfluenceLifecycleIT(unittest.TestCase):
    def test_create_update_read_move_delete(self):
        # Imported here (not at module top) so a missing credential skips the
        # test instead of triggering _client's hard exit during collection.
        import confluence

        space = os.environ["INTEGRATION_TEST_SPACE"]
        client = confluence.confluence_client()
        suffix = f"{int(time.time())}-{os.getpid()}"
        parent_title = f"[itest parent] {suffix}"
        child_title = f"[itest child] {suffix}"

        to_clean = []
        try:
            with tempfile.TemporaryDirectory() as d:
                body_file = pathlib.Path(d) / "body.html"

                # 1. Create the move target (parent) and the page under test (child).
                body_file.write_text("<p>integration test v1</p>")
                parent = confluence.cmd_create(
                    _ns(space_key=space, title=parent_title, body_file=str(body_file),
                        parent_id=None, from_markdown=False)
                )
                to_clean.append(parent["id"])
                child = confluence.cmd_create(
                    _ns(space_key=space, title=child_title, body_file=str(body_file),
                        parent_id=None, from_markdown=False)
                )
                child_id = child["id"]
                to_clean.append(child_id)

                # 2. Update the child's body.
                body_file.write_text("<p>integration test v2 — updated</p>")
                updated = confluence.cmd_update(
                    _ns(page_id=child_id, body_file=str(body_file), title=None,
                        message="integration test update", from_markdown=False,
                        keep_appearance=False)
                )
                self.assertGreaterEqual(updated["version"]["number"], 2)

                # 3. Read it back and confirm the update landed.
                fetched = confluence.cmd_get(_ns(page_id=child_id, out=None))
                self.assertIn("updated", fetched["body"]["storage"]["value"])

                # 4. Move the child under the parent.
                confluence.cmd_move(
                    _ns(page_id=child_id, space_key=space, target_id=parent["id"],
                        position="append")
                )

                # 5. Verify the new parent via ancestors.
                moved = client.get_page_by_id(child_id, expand="ancestors")
                ancestor_ids = [a["id"] for a in moved.get("ancestors", [])]
                self.assertIn(parent["id"], ancestor_ids)

                # 6. Delete both pages through the script; mark them cleaned.
                confluence.cmd_delete(_ns(page_id=child_id, recursive=False))
                confluence.cmd_delete(_ns(page_id=parent["id"], recursive=False))
                to_clean = []
        finally:
            # Best-effort cleanup for anything left if an assertion failed midway.
            for page_id in to_clean:
                try:
                    client.remove_page(page_id, recursive=True)
                except Exception as exc:  # noqa: BLE001 - cleanup must not mask the real failure
                    print(f"cleanup warning: could not remove page {page_id}: {exc}")


if __name__ == "__main__":
    unittest.main()
