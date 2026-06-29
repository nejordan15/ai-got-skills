"""Happy-path tests for the confluence-api skill's folder commands.

No network: folders._session() is mocked to return a fake session whose
HTTP verbs return canned responses, so these exercise URL/payload construction
and space-id resolution — not the live API.

Run from the plugin root:
    python3 -m unittest discover tests
or directly:
    python3 tests/unit/test_folders.py
"""
import argparse
import contextlib
import io
import os
import pathlib
import sys
import unittest
from unittest import mock

# Dummy creds must exist before importing the script: lib/_client.py reads the
# ATLASSIAN_* env vars at import time and exits if any are missing.
os.environ.setdefault("ATLASSIAN_BASE_URL", "https://example.atlassian.net")
os.environ.setdefault("ATLASSIAN_EMAIL", "test@example.com")
os.environ.setdefault("ATLASSIAN_API_TOKEN", "dummy-token")

ASSETS = pathlib.Path(__file__).resolve().parents[2] / "skills" / "confluence-api" / "assets"
sys.path.insert(0, str(ASSETS))
import folders  # noqa: E402

BASE = "https://example.atlassian.net/wiki"


def _ns(**kw):
    return argparse.Namespace(**kw)


def _run(fn, args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(args)
    return result


class _Resp:
    """Minimal stand-in for a requests.Response that passes folders._check."""

    def __init__(self, payload, status_code=200, method="GET", url=BASE):
        self._payload = payload
        self.status_code = status_code
        self.text = "" if payload is None else "<body>"
        self.url = url
        self.request = mock.Mock(method=method)

    def json(self):
        return self._payload


class FoldersHappyPath(unittest.TestCase):
    def test_create_resolves_space_then_posts(self):
        session = mock.Mock()
        session.get.return_value = _Resp({"results": [{"id": "12345"}]})
        session.post.return_value = _Resp(
            {"id": "f1", "title": "2025", "parentId": "p1", "_links": {}}
        )
        with mock.patch("folders._session", return_value=session):
            folder = _run(
                folders.cmd_folder_create,
                _ns(space_key="RATE", space_id=None, title="2025", parent_id="p1"),
            )

        # space resolution hit the v2 spaces endpoint with the key
        _, get_kwargs = session.get.call_args
        self.assertEqual(session.get.call_args[0][0], f"{BASE}/api/v2/spaces")
        self.assertEqual(get_kwargs["params"]["keys"], "RATE")

        # create POSTed to the v2 folders endpoint with the resolved spaceId
        post_args, post_kwargs = session.post.call_args
        self.assertEqual(post_args[0], f"{BASE}/api/v2/folders")
        self.assertEqual(
            post_kwargs["json"],
            {"spaceId": "12345", "title": "2025", "parentId": "p1"},
        )
        self.assertEqual(folder["id"], "f1")

    def test_create_with_space_id_skips_lookup(self):
        session = mock.Mock()
        session.post.return_value = _Resp({"id": "f2", "title": "december"})
        with mock.patch("folders._session", return_value=session):
            _run(
                folders.cmd_folder_create,
                _ns(space_key=None, space_id="999", title="december", parent_id="f1"),
            )
        session.get.assert_not_called()
        _, post_kwargs = session.post.call_args
        self.assertEqual(post_kwargs["json"]["spaceId"], "999")
        self.assertEqual(post_kwargs["json"]["parentId"], "f1")

    def test_create_root_omits_parent(self):
        session = mock.Mock()
        session.post.return_value = _Resp({"id": "f3", "title": "top"})
        with mock.patch("folders._session", return_value=session):
            _run(
                folders.cmd_folder_create,
                _ns(space_key=None, space_id="999", title="top", parent_id=None),
            )
        _, post_kwargs = session.post.call_args
        self.assertNotIn("parentId", post_kwargs["json"])

    def test_get_hits_folder_endpoint(self):
        session = mock.Mock()
        session.get.return_value = _Resp(
            {"id": "f1", "title": "2025", "spaceId": "12345", "parentId": "p1"}
        )
        with mock.patch("folders._session", return_value=session):
            _run(folders.cmd_folder_get, _ns(folder_id="f1", children=False))
        args, kwargs = session.get.call_args
        self.assertEqual(args[0], f"{BASE}/api/v2/folders/f1")
        self.assertEqual(kwargs["params"], {})

    def test_get_children_sets_include_param(self):
        session = mock.Mock()
        session.get.return_value = _Resp(
            {"id": "f1", "title": "2025",
             "directChildren": {"results": [
                 {"type": "folder", "id": "f2", "title": "December"}]}}
        )
        with mock.patch("folders._session", return_value=session):
            _run(folders.cmd_folder_get, _ns(folder_id="f1", children=True))
        _, kwargs = session.get.call_args
        self.assertEqual(kwargs["params"]["include-direct-children"], "true")

    def test_move_uses_legacy_endpoint(self):
        session = mock.Mock()
        session.put.return_value = _Resp({}, method="PUT")
        with mock.patch("folders._session", return_value=session):
            _run(
                folders.cmd_folder_move,
                _ns(folder_id="f2", target_id="f1", position="append"),
            )
        args, _ = session.put.call_args
        self.assertEqual(
            args[0], f"{BASE}/rest/api/content/f2/move/append/f1"
        )


if __name__ == "__main__":
    unittest.main()
