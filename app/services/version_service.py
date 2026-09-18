"""
Version Checker Service.
Queries GitHub Releases API to check for newer releases of ED_Journal_Analyzer.
Includes in-memory caching to avoid GitHub API rate limits.
"""

import json
import logging
import re
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from packaging.version import parse as parse_version, InvalidVersion

from app.config import APP_VERSION

logger = logging.getLogger(__name__)

GITHUB_REPO = "SuzuneYonaki/ED_Journal_Analyzer"
GITHUB_LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CACHE_TTL_SECONDS = 3600  # 1 hour
ERROR_COOLDOWN_SECONDS = 300  # 5 minutes on failure


def extract_release_summary(body: Optional[str], max_len: int = 140) -> str:
    """
    Extracts a concise, clean summary string from markdown release notes.
    Strips markdown heading lines, bullet symbols, links, and collapses whitespace.
    """
    if not body:
        return ""

    # Remove markdown header lines (e.g. # Title, ## Section)
    text = re.sub(r'(?m)^#+\s+.*$', '', body)
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove formatting bold/italic/code
    text = re.sub(r'[*_`]', '', text)

    # Split into lines and pick the first non-empty descriptive lines
    lines = [line.strip().lstrip("-*• ") for line in text.splitlines() if line.strip()]

    # If stripping headers removed everything, fall back to stripped body
    if not lines:
        cleaned = re.sub(r'[*_`#]', '', body)
        lines = [line.strip().lstrip("-*• ") for line in cleaned.splitlines() if line.strip()]

    summary_parts = []
    current_len = 0
    for line in lines:
        if not line:
            continue
        if current_len + len(line) + 3 > max_len:
            remaining = max_len - current_len - 3
            if remaining > 10:
                summary_parts.append(line[:remaining].rstrip() + "...")
            elif not summary_parts:
                summary_parts.append(line[:max_len - 3].rstrip() + "...")
            break
        summary_parts.append(line)
        current_len += len(line) + 3

    return " / ".join(summary_parts) if summary_parts else ""


def is_newer_version(latest_tag: str, current_ver: str = APP_VERSION) -> bool:
    """
    Returns True if latest_tag is strictly newer than current_ver.
    Handles 'v' prefix and invalid version strings gracefully.
    """
    if not latest_tag or not current_ver:
        return False
    try:
        clean_latest = latest_tag.strip().lstrip("vV")
        clean_current = current_ver.strip().lstrip("vV")
        return parse_version(clean_latest) > parse_version(clean_current)
    except (InvalidVersion, TypeError, AttributeError) as e:
        logger.warning(f"Failed to compare versions '{latest_tag}' vs '{current_ver}': {e}")
        return False


class VersionCheckerService:
    def __init__(self, repo: str = GITHUB_REPO, cache_ttl: int = CACHE_TTL_SECONDS):
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        self.cache_ttl = cache_ttl
        self._cached_result: Optional[Dict[str, Any]] = None
        self._last_checked_time: float = 0.0

    def check_update(self, force: bool = False) -> Dict[str, Any]:
        """
        Checks for newer release on GitHub.
        Returns dictionary containing:
          - has_update: bool
          - latest_version: str
          - current_version: str
          - release_name: str
          - release_url: str
          - summary: str
          - body: str
          - published_at: str
          - error: Optional[str]
        """
        now = time.time()
        if not force and self._cached_result is not None:
            ttl = self.cache_ttl if not self._cached_result.get("error") else ERROR_COOLDOWN_SECONDS
            if now - self._last_checked_time < ttl:
                return self._cached_result

        result = self._fetch_latest_release()
        self._cached_result = result
        self._last_checked_time = now
        return result

    def _fetch_latest_release(self) -> Dict[str, Any]:
        req = urllib.request.Request(
            self.api_url,
            headers={
                "User-Agent": f"ED_Journal_Analyzer/{APP_VERSION}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                release_name = data.get("name") or tag_name
                release_url = data.get("html_url", f"https://github.com/{self.repo}/releases")
                body = data.get("body", "")
                published_at = data.get("published_at", "")

                has_update = is_newer_version(tag_name, APP_VERSION)
                summary = extract_release_summary(body)

                return {
                    "has_update": has_update,
                    "latest_version": tag_name,
                    "current_version": APP_VERSION,
                    "release_name": release_name,
                    "release_url": release_url,
                    "summary": summary,
                    "body": body,
                    "published_at": published_at,
                    "error": None
                }
        except urllib.error.HTTPError as e:
            logger.warning(f"GitHub API HTTP {e.code} while checking updates: {e.reason}")
            return {
                "has_update": False,
                "latest_version": None,
                "current_version": APP_VERSION,
                "release_name": None,
                "release_url": f"https://github.com/{self.repo}/releases",
                "summary": None,
                "body": None,
                "published_at": None,
                "error": f"HTTP {e.code}"
            }
        except Exception as e:
            logger.warning(f"Failed to check updates from GitHub: {e}")
            return {
                "has_update": False,
                "latest_version": None,
                "current_version": APP_VERSION,
                "release_name": None,
                "release_url": f"https://github.com/{self.repo}/releases",
                "summary": None,
                "body": None,
                "published_at": None,
                "error": str(e)
            }


version_service = VersionCheckerService()
