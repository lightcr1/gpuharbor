"""Guards for the dashboard markup so UI typos fail the test suite."""
from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).parents[1] / "gpuharbor" / "static"


def read(name: str) -> str:
    return (STATIC / name).read_text(encoding="utf-8")


def _translation_keys() -> tuple[set[str], set[str], set[str]]:
    import re

    html = read("index.html")
    script = read("app.js")
    used = set(re.findall(r'data-i18n(?:-title)?="([^"]+)"', html))
    body = script.split("const I18N=", 1)[1].split("let lang=", 1)[0]
    english_block, german_block = body.split("de:{", 1)
    english = set(re.findall(r'"([a-z][a-z0-9_.]+)":', english_block))
    german = set(re.findall(r'"([a-z][a-z0-9_.]+)":', german_block))
    return used, english, german


def test_every_visible_string_is_translated_in_both_languages():
    used, english, german = _translation_keys()
    assert used, "no data-i18n attributes found"
    assert not (used - english), f"missing English translations: {sorted(used - english)}"
    assert not (used - german), f"missing German translations: {sorted(used - german)}"


def test_both_dictionaries_define_the_same_keys():
    _, english, german = _translation_keys()
    assert english == german, f"only in English: {sorted(english - german)}, only in German: {sorted(german - english)}"


def test_dictionary_values_contain_no_html_entities():
    """Values are assigned with textContent, so entities would show up literally."""
    import re

    body = read("app.js").split("const I18N=", 1)[1].split("let lang=", 1)[0]
    bad = re.findall(r'"[a-z][a-z0-9_.]+":"[^"]*&(?:amp|nbsp|lt|gt|quot);[^"]*"', body)
    assert not bad, f"HTML entities in translation values: {bad}"


def test_dashboard_element_references_resolve():
    html = read("index.html")
    script = read("app.js")
    ids = set(re.findall(r'\bid="([^"]+)"', html))
    refs = set(re.findall(r"\$\('([^']+)'\)", script))
    refs |= set(re.findall(r"getElementById\('([^']+)'\)", script))
    refs |= set(re.findall(r"onChange\('([^']+)'", script))
    assert refs <= ids, f"Dashboard references missing element ids: {sorted(refs - ids)}"


def test_dashboard_links_favicon_and_docs():
    html = read("index.html")
    assert 'href="/favicon.svg"' in html
    assert 'href="/docs"' in html


def test_dashboard_has_both_languages():
    html = read("index.html")
    script = read("app.js")
    assert 'id="lang-switch"' in html
    assert '<option value="en">' in html and '<option value="de">' in html
    assert "const I18N=" in script
    for key in ("nav.docs", "btn.start", "field.trust"):
        assert script.count(f'"{key}"') >= 2, f"{key} is not translated in both languages"


def test_docs_page_covers_key_topics():
    english = read("docs.html")
    for topic in (
        "Trust Hugging Face remote code",
        "Regions and datacenters",
        "Pod actions",
        "Adding runtimes",
        "Error messages",
        "Model catalog",
    ):
        assert topic in english, f"/docs is missing the topic: {topic}"

    german = read("docs.de.html")
    for topic in (
        "Remote-Code vertrauen",
        "Regionen und Rechenzentren",
        "Pod-Aktionen",
        "Runtimes erweitern",
        "Fehlermeldungen",
        "Modellkatalog",
    ):
        assert topic in german, f"/docs/de is missing the topic: {topic}"
    assert 'href="/docs"' in german
    assert 'href="/docs/de"' in english


def test_favicon_is_svg():
    svg = read("favicon.svg")
    assert svg.lstrip().startswith("<svg")
    assert 'viewBox="0 0 64 64"' in svg


def test_pages_need_no_inline_code_or_styles():
    """The CSP forbids inline scripts and styles, so pages must not contain any."""
    for name in ("index.html", "docs.html", "docs.de.html"):
        html = read(name)
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), f"{name} has an inline script"
        assert "<style" not in html, f"{name} has an inline style block"
        assert not re.search(r'\sstyle="', html), f"{name} has a style attribute"
        assert not re.search(r'\son[a-z]+="', html), f"{name} has an inline event handler"


def test_content_security_policy_is_strict(app_client):
    client, _ = app_client
    policy = client.get("/health").headers["content-security-policy"]
    assert "unsafe-inline" not in policy
    assert "script-src 'self'" in policy


def test_static_assets_are_served(app_client):
    client, _ = app_client
    for name in ("app.js", "app.css", "theme.js", "theme.css", "docs.css", "docs.js"):
        assert client.get(f"/static/{name}").status_code == 200, name
    assert client.get("/static/../main.py").status_code in {400, 404}
