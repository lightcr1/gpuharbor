"""Guards for the dashboard markup so UI typos fail the test suite."""
from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).parents[1] / "gpuharbor" / "static"


def read(name: str) -> str:
    return (STATIC / name).read_text(encoding="utf-8")


def test_dashboard_element_references_resolve():
    html = read("index.html")
    ids = set(re.findall(r'\bid="([^"]+)"', html))
    refs = set(re.findall(r"\$\('([^']+)'\)", html))
    refs |= set(re.findall(r"getElementById\('([^']+)'\)", html))
    refs |= set(re.findall(r"document\.querySelector\('#([A-Za-z0-9_-]+)'\)", html))
    assert refs <= ids, f"Dashboard references missing element ids: {sorted(refs - ids)}"


def test_dashboard_links_favicon_and_docs():
    html = read("index.html")
    assert 'href="/favicon.svg"' in html
    assert 'href="/docs"' in html


def test_docs_page_covers_key_topics():
    html = read("docs.html")
    for topic in (
        "Hugging-Face Remote-Code",
        "Regionen",
        "Pod-Aktionen",
        "Runtimes erweitern",
        "Fehlermeldungen",
        "Modellkatalog",
    ):
        assert topic in html, f"/docs is missing the topic: {topic}"


def test_favicon_is_svg():
    svg = read("favicon.svg")
    assert svg.lstrip().startswith("<svg")
    assert 'viewBox="0 0 64 64"' in svg
