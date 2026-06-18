"""Simple happy-path tests for the shared lib/_client.py.

No network and no atlassian-python-api install: the lazy `from atlassian
import ...` is satisfied by a fake module injected into sys.modules, so the
factories construct against a mock.

Run from the plugin root:
    python3 -m unittest discover -s tests -v
or directly:
    python3 tests/test_client.py
"""
import os
import pathlib
import sys
import unittest
from unittest import mock

# Dummy creds must exist before import: _client reads the ATLASSIAN_* env vars
# at import time and exits if any are missing.
os.environ.setdefault("ATLASSIAN_BASE_URL", "https://example.atlassian.net")
os.environ.setdefault("ATLASSIAN_EMAIL", "test@example.com")
os.environ.setdefault("ATLASSIAN_API_TOKEN", "dummy-token")

LIB = pathlib.Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import _client  # noqa: E402


class ClientHappyPath(unittest.TestCase):
    def test_require_env_returns_value(self):
        os.environ["SOME_TEST_VAR"] = "hello"
        try:
            self.assertEqual(_client._require_env("SOME_TEST_VAR"), "hello")
        finally:
            del os.environ["SOME_TEST_VAR"]

    def test_confluence_base_url_has_wiki_suffix(self):
        self.assertEqual(
            _client.CONFLUENCE_BASE_URL, _client.ATLASSIAN_BASE_URL + "/wiki"
        )

    def test_confluence_client_constructs_with_creds(self):
        fake = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"atlassian": fake}):
            client = _client.confluence_client()
        fake.Confluence.assert_called_once_with(
            url=_client.CONFLUENCE_BASE_URL,
            username=_client.ATLASSIAN_EMAIL,
            password=_client.ATLASSIAN_API_TOKEN,
            cloud=True,
        )
        self.assertIs(client, fake.Confluence.return_value)

    def test_jira_client_constructs_with_bare_base_url(self):
        fake = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"atlassian": fake}):
            client = _client.jira_client()
        fake.Jira.assert_called_once_with(
            url=_client.ATLASSIAN_BASE_URL,
            username=_client.ATLASSIAN_EMAIL,
            password=_client.ATLASSIAN_API_TOKEN,
            cloud=True,
        )
        self.assertIs(client, fake.Jira.return_value)


if __name__ == "__main__":
    unittest.main()
