import json
import urllib.error
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.server.api import app
from app.services.version_service import (
    is_newer_version,
    extract_release_summary,
    VersionCheckerService
)


def test_is_newer_version():
    assert is_newer_version("v0.8.3", "0.8.2") is True
    assert is_newer_version("0.8.3", "0.8.2") is True
    assert is_newer_version("v1.0.0", "0.8.2") is True
    assert is_newer_version("0.9.0", "0.8.2") is True
    assert is_newer_version("0.8.2.1", "0.8.2") is True

    # Same version
    assert is_newer_version("v0.8.2", "0.8.2") is False
    assert is_newer_version("0.8.2", "0.8.2") is False

    # Older version
    assert is_newer_version("v0.8.1", "0.8.2") is False
    assert is_newer_version("0.7.9", "0.8.2") is False

    # Invalid or empty
    assert is_newer_version("", "0.8.2") is False
    assert is_newer_version("invalid", "0.8.2") is False
    assert is_newer_version("v0.8.3", "") is False


def test_extract_release_summary():
    assert extract_release_summary(None) == ""
    assert extract_release_summary("") == ""

    body = """### What's Changed
- Added update checker notification in [PR #45](https://github.com/example/pull/45)
- Fixed TTS modal terms of service display
- General performance improvements

### Documentation
* Updated README.md
"""
    summary = extract_release_summary(body, max_len=120)
    assert len(summary) <= 125
    assert "What's Changed" not in summary  # Header stripped or separated
    assert "Added update checker notification in PR #45" in summary
    assert "http" not in summary  # URL stripped


def test_version_checker_service_success():
    service = VersionCheckerService(repo="TestOwner/TestRepo", cache_ttl=100)

    mock_payload = {
        "tag_name": "v0.9.0",
        "name": "Release v0.9.0 - Major Overhaul",
        "html_url": "https://github.com/TestOwner/TestRepo/releases/tag/v0.9.0",
        "body": "## Overview\n- Amazing new features added!\n- Better performance.",
        "published_at": "2026-09-18T12:00:00Z"
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        # First call: hits network
        res = service.check_update()
        assert res["has_update"] is True
        assert res["latest_version"] == "v0.9.0"
        assert res["release_name"] == "Release v0.9.0 - Major Overhaul"
        assert res["release_url"] == "https://github.com/TestOwner/TestRepo/releases/tag/v0.9.0"
        assert "Amazing new features" in res["summary"]
        assert mock_urlopen.call_count == 1

        # Second call: served from cache
        res2 = service.check_update()
        assert res2["has_update"] is True
        assert mock_urlopen.call_count == 1

        # Force refresh: hits network again
        res3 = service.check_update(force=True)
        assert res3["has_update"] is True
        assert mock_urlopen.call_count == 2


def test_version_checker_service_http_error():
    service = VersionCheckerService(repo="TestOwner/TestRepo", cache_ttl=100)

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="http://test", code=403, msg="rate limit exceeded", hdrs={}, fp=None
    )):
        res = service.check_update()
        assert res["has_update"] is False
        assert res["latest_version"] is None
        assert "HTTP 403" in res["error"]


def test_version_checker_service_network_exception():
    service = VersionCheckerService(repo="TestOwner/TestRepo", cache_ttl=100)

    with patch("urllib.request.urlopen", side_effect=OSError("Network unreachable")):
        res = service.check_update()
        assert res["has_update"] is False
        assert res["latest_version"] is None
        assert "Network unreachable" in res["error"]


def test_api_check_update_endpoint():
    client = TestClient(app)
    with patch("app.services.version_service.version_service.check_update") as mock_check:
        mock_check.return_value = {
            "has_update": True,
            "latest_version": "v0.9.0",
            "current_version": "0.8.2",
            "release_name": "v0.9.0",
            "release_url": "https://github.com/test",
            "summary": "Awesome update",
            "body": "Detailed notes",
            "published_at": "2026-09-18T12:00:00Z",
            "error": None
        }

        resp = client.get("/api/check_update")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_update"] is True
        assert data["latest_version"] == "v0.9.0"
        assert data["current_version"] == "0.8.2"
