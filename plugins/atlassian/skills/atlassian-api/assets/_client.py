"""Shared Atlassian API client setup.

Reads credentials from environment variables and returns configured clients.
Used by confluence.py and (future) jira.py.
"""
import os
import sys


def _require_env(var_name: str) -> str:
    val = os.environ.get(var_name)
    if not val:
        sys.exit(
            f"error: required env var {var_name} is not set. "
            f"Set ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL, and ATLASSIAN_API_TOKEN in your shell rc."
        )
    return val


ATLASSIAN_BASE_URL = _require_env("ATLASSIAN_BASE_URL")  # e.g. https://YOUR-DOMAIN.atlassian.net
ATLASSIAN_EMAIL = _require_env("ATLASSIAN_EMAIL")
ATLASSIAN_API_TOKEN = _require_env("ATLASSIAN_API_TOKEN")

# Confluence Cloud expects the /wiki suffix; Jira uses the bare base URL.
CONFLUENCE_BASE_URL = ATLASSIAN_BASE_URL + "/wiki"


def confluence_client():
    """Return a configured Confluence Cloud client."""
    from atlassian import Confluence

    return Confluence(
        url=CONFLUENCE_BASE_URL,
        username=ATLASSIAN_EMAIL,
        password=ATLASSIAN_API_TOKEN,
        cloud=True,
    )


def jira_client():
    """Return a configured Jira Cloud client. Stub for future use."""
    from atlassian import Jira

    return Jira(
        url=ATLASSIAN_BASE_URL,
        username=ATLASSIAN_EMAIL,
        password=ATLASSIAN_API_TOKEN,
        cloud=True,
    )
