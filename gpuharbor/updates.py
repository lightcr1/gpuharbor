"""Optional, opt-in update check against the public GitHub releases.

Nothing here runs unless ``GPUHARBOR_UPDATE_CHECK=true`` is set. The only data
leaving the machine is a plain HTTPS GET to the GitHub releases API; no token and
no configuration is sent.
"""
from __future__ import annotations

import re

import httpx

RELEASES_URL = "https://api.github.com/repos/{repo}/releases/latest"
_VERSION = re.compile(r"^v?(\d+(?:\.\d+)*)")


def normalize(version: str) -> tuple[int, ...]:
    """Return the leading numeric parts of a version, ignoring suffixes."""
    match = _VERSION.match((version or "").strip())
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(latest: str, current: str) -> bool:
    """True when ``latest`` is a higher version than ``current``."""
    newer, installed = normalize(latest), normalize(current)
    if not newer or not installed:
        return False
    width = max(len(newer), len(installed))
    return newer + (0,) * (width - len(newer)) > installed + (0,) * (width - len(installed))


async def fetch_latest(client: httpx.AsyncClient, repo: str) -> dict[str, str]:
    """Read the latest published release from GitHub."""
    response = await client.get(
        RELEASES_URL.format(repo=repo),
        headers={"Accept": "application/vnd.github+json", "User-Agent": "gpuharbor-update-check"},
        timeout=8,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "tag": str(data.get("tag_name") or ""),
        "url": str(data.get("html_url") or ""),
        "published_at": str(data.get("published_at") or ""),
    }
