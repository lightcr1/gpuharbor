# GPUHarbor

[![CI](https://github.com/lightcr1/gpuharbor/actions/workflows/ci.yml/badge.svg)](https://github.com/lightcr1/gpuharbor/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/lightcr1/gpuharbor)](https://github.com/lightcr1/gpuharbor/releases)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Eine kleine Steuerzentrale, um KI-Modelle auf RunPod laufen zu lassen. GPUHarbor
verwaltet einen GPU-Pod, lädt ein Modell und stellt es über eine
OpenAI-kompatible API bereit.

```
Browser -> GPUHarbor -> RunPod-Pod -> Runtime-Image -> Modell
```

Der Controller läuft überall, wo Docker läuft, und braucht keine GPU. Nur der
Pod kostet Geld.

![GPUHarbor Dashboard](docs/screenshots/dashboard.de.png)

Nicht mit RunPod verbunden und nicht von RunPod betrieben.

## Was es macht

- Einen Pod starten und stoppen, mit standardmäßig aktiver Kostensperre.
- Modellprofile auf der Platte speichern und im Browser bearbeiten. Updates
  bringen neue Profile, deine eigenen bleiben unberührt.
- GPUs aus dem echten RunPod-Katalog wählen, oder einfach eine Region angeben
  und das Rechenzentrum automatisch zuweisen lassen.
- Die genaue RunPod-Anfrage vorher ansehen, mit entfernten Geheimnissen.
- Das Modell jedem OpenAI-kompatiblen Client bereitstellen.
- Open WebUI und OpenHands nach Wunsch dazunehmen.

## Installation

Du brauchst Docker mit Compose und einen [RunPod](https://www.runpod.io/)-Account
(nur zum Starten echter Pods; das Dashboard läuft auch ohne).

```bash
git clone https://github.com/lightcr1/gpuharbor.git
cd gpuharbor
./scripts/install
```

Danach `https://localhost:8443` öffnen (HTTPS ist Standard, Zertifikat einer lokalen CA, siehe [TLS](docs/TLS.md); Benutzer `admin`, Passwort anzeigen mit `./scripts/init-env --show-login`). Mit `--webui` kommt Open WebUI dazu. Für LAN oder die interaktive
Variante siehe [Setup](docs/SETUP.md). Die App erklärt jedes Feld unter `/docs`.

Nichts an RunPod passiert, solange `RUNPOD_ALLOW_BILLABLE_ACTIONS=false` gesetzt
ist.

## Modellprofile

Vier Profile sind dabei:

| Profil | Runtime | Stand |
|---|---|---|
| Qwen3.8 27B FP8 | vLLM | lief auf einer A40 |
| Qwen3 Coder 30B FP8 | vLLM | noch nicht auf GPU getestet |
| HauhauCS 35B Aggressive Q6 | llama.cpp | noch nicht auf GPU getestet |
| Ternary Bonsai 2 27B PTQ1_0 | Bonsai-Fork | noch nicht auf GPU getestet |

Die Modellgewichte lädt der Pod beim ersten Start und legt sie auf seinem Volume
ab. GPUHarbor verteilt sie nicht. Siehe [Models](docs/MODELS.md) und
[Third-party components](docs/THIRD_PARTY.md).

## Dokumentation

[docs/](docs/README.md) enthält Setup, Modelle, Upgrades, Status und die
Sicherheitsrichtlinie. [docs/STATUS.md](docs/STATUS.md) sagt offen, was getestet
ist und was nicht.

## Lizenz

Apache-2.0 für den offenen Kern, siehe [LICENSE](LICENSE). Geplante bezahlte
Funktionen (mehrere Anbieter, Teams, Kostenautomatik) sind ein getrenntes,
geschlossenes Modul und nicht in diesem Repository.
[docs/LICENSING.md](docs/LICENSING.md) erklärt die Aufteilung.
