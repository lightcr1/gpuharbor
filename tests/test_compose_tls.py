"""Guards for the HTTPS-by-default stack: overlays, proxy listeners and the installer."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_nginx_serves_controller_webui_and_openhands_over_tls():
    conf = read("deploy/nginx.conf")
    assert re.findall(r"listen (\d+) ssl;", conf) == ["8443", "8444", "8445"]
    assert "proxy_pass $controller" in conf and "proxy_pass $webui" in conf and "proxy_pass $openhands" in conf
    assert "Upgrade $http_upgrade" in conf, "websockets are needed by Open WebUI and OpenHands"
    assert "Strict-Transport-Security" not in conf.replace("# No Strict-Transport-Security", "")


def test_tls_overlays_limit_plain_http_to_loopback():
    for name, port in (
        ("compose.tls.yml", "127.0.0.1:8080:8080"),
        ("compose.openwebui.tls.yml", "127.0.0.1:3000:8080"),
        ("compose.openhands.tls.yml", "127.0.0.1:3001:8000"),
    ):
        text = read(name)
        assert "ports: !override" in text and port in text, name


def test_integration_ports_are_only_published_with_their_overlay():
    assert "8444" not in read("compose.tls.yml") and "8445" not in read("compose.tls.yml")
    assert "8444" in read("compose.openwebui.tls.yml")
    assert "8445" in read("compose.openhands.tls.yml")


def test_installer_writes_compose_file_and_extra_names(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text("CONTROL_TOKEN=replace-me\nGPUHARBOR_TRUSTED_HOSTS=localhost,127.0.0.1\n", encoding="utf-8")
    target = tmp_path / ".env"
    subprocess.run(
        [
            sys.executable, str(ROOT / "scripts/init-env"), "--env", str(target), "--example", str(example),
            "--bind-ip", "0.0.0.0", "--https-host", "localhost", "--tls-bind-ip", "0.0.0.0",
            "--overlay", "compose.tls.yml", "--overlay", "compose.openwebui.yml",
        ],
        check=True, capture_output=True, text=True,
    )
    values = dict(line.split("=", 1) for line in target.read_text().splitlines() if "=" in line)
    assert values["COMPOSE_FILE"] == "compose.yml:compose.tls.yml:compose.openwebui.yml"
    assert values["TLS_BIND_IP"] == "0.0.0.0"
    assert values["GPUHARBOR_COOKIE_SECURE"] == "true"


def test_local_certificate_covers_localhost_and_extra_names(tmp_path):
    subprocess.run(
        [str(ROOT / "scripts/generate-local-tls"), "192.0.2.10,harbor.lan", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    assert not (tmp_path / "local-ca.key").exists(), "the CA key must not be kept"
    text = subprocess.run(
        ["openssl", "x509", "-in", str(tmp_path / "server.crt"), "-noout", "-ext", "subjectAltName"],
        check=True, capture_output=True, text=True,
    ).stdout
    for name in ("192.0.2.10", "harbor.lan", "localhost", "127.0.0.1"):
        assert name in text, name
