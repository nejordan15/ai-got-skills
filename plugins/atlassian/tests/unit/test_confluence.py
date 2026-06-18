"""Simple happy-path tests for the confluence-api skill's CLI.

No network: the Confluence client is mocked, so these exercise argument
handling, file I/O, and the right client calls — not the live API.

Run from the plugin root:
    python3 -m unittest discover tests
or directly:
    python3 tests/test_confluence.py
"""
import argparse
import contextlib
import io
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

# Dummy creds must exist before importing the script: lib/_client.py reads the
# ATLASSIAN_* env vars at import time and exits if any are missing.
os.environ.setdefault("ATLASSIAN_BASE_URL", "https://example.atlassian.net")
os.environ.setdefault("ATLASSIAN_EMAIL", "test@example.com")
os.environ.setdefault("ATLASSIAN_API_TOKEN", "dummy-token")

ASSETS = pathlib.Path(__file__).resolve().parents[2] / "skills" / "confluence-api" / "assets"
sys.path.insert(0, str(ASSETS))
import confluence  # noqa: E402


def _ns(**kw):
    return argparse.Namespace(**kw)


def _run(fn, args):
    """Call a cmd_* function with stdout silenced; return printed output."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(args)
    return buf.getvalue()


class ConfluenceHappyPath(unittest.TestCase):
    def test_is_wide(self):
        self.assertTrue(confluence._is_wide("max"))
        self.assertTrue(confluence._is_wide("full-width"))
        self.assertFalse(confluence._is_wide("fixed-width"))
        self.assertFalse(confluence._is_wide(None))

    @mock.patch("confluence.confluence_client")
    def test_get_writes_body_to_file(self, factory):
        client = factory.return_value
        client.get_page_by_id.return_value = {
            "id": "123",
            "title": "My Page",
            "space": {"key": "DOCS"},
            "version": {"number": 4},
            "body": {"storage": {"value": "<p>hello</p>"}},
        }
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "body.html"
            _run(confluence.cmd_get, _ns(page_id="123", out=str(out)))
            self.assertEqual(out.read_text(), "<p>hello</p>")
        client.get_page_by_id.assert_called_once_with(
            "123", expand="body.storage,version,space"
        )

    @mock.patch("confluence.confluence_client")
    def test_create_uses_storage_and_full_width(self, factory):
        client = factory.return_value
        client.create_page.return_value = {
            "id": "999",
            "title": "New Page",
            "space": {"key": "DOCS"},
        }
        with tempfile.TemporaryDirectory() as d:
            body_file = pathlib.Path(d) / "body.html"
            body_file.write_text("<p>body</p>")
            _run(
                confluence.cmd_create,
                _ns(
                    space_key="DOCS",
                    title="New Page",
                    body_file=str(body_file),
                    parent_id=None,
                    from_markdown=False,
                ),
            )
        _, kwargs = client.create_page.call_args
        self.assertEqual(kwargs["body"], "<p>body</p>")
        self.assertEqual(kwargs["representation"], "storage")
        self.assertTrue(kwargs["full_width"])

    @mock.patch("confluence.confluence_client")
    def test_update_defaults_to_wide(self, factory):
        client = factory.return_value
        client.update_page.return_value = {
            "id": "123",
            "title": "Existing",
            "version": {"number": 5},
        }
        with tempfile.TemporaryDirectory() as d:
            body_file = pathlib.Path(d) / "body.html"
            body_file.write_text("<p>updated</p>")
            _run(
                confluence.cmd_update,
                _ns(
                    page_id="123",
                    body_file=str(body_file),
                    title="Existing",
                    message="test edit",
                    from_markdown=False,
                    keep_appearance=False,
                ),
            )
        _, kwargs = client.update_page.call_args
        self.assertEqual(kwargs["body"], "<p>updated</p>")
        self.assertEqual(kwargs["representation"], "storage")
        self.assertTrue(kwargs["full_width"])
        # title was supplied, so no extra fetch is needed to look it up.
        client.get_page_by_id.assert_not_called()

    @mock.patch("confluence.confluence_client")
    def test_move_calls_move_page(self, factory):
        client = factory.return_value
        _run(
            confluence.cmd_move,
            _ns(page_id="123", space_key="DOCS", target_id="999", position="append"),
        )
        client.move_page.assert_called_once_with(
            space_key="DOCS", page_id="123", target_id="999", position="append"
        )

    @mock.patch("confluence.confluence_client")
    def test_delete_calls_remove_page(self, factory):
        client = factory.return_value
        _run(confluence.cmd_delete, _ns(page_id="123", recursive=False))
        client.remove_page.assert_called_once_with("123", recursive=False)


if __name__ == "__main__":
    unittest.main()
