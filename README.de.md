# GPUHarbor

**Eine selbst gehostete Steuerzentrale für kuratierte KI-Modelle auf RunPod.**

GPUHarbor verwaltet einen GPU-Pod, stellt das Modell über eine authentifizierte
OpenAI-kompatible API bereit und bietet eine übersichtliche Weboberfläche.
Open WebUI und OpenHands sind optionale Integrationen.

## Funktionen

- Modelle direkt in der UI hinzufügen und bearbeiten
- Kontextlänge, Parallelität, GPU, Rechenzentrum und Volume beim Start wählen
- kuratierte Profile für vLLM, llama.cpp/GGUF und die Bonsai-Spezial-Runtime
- kostenfreien, von Geheimnissen bereinigten Startplan anzeigen
- kostenpflichtige Aktionen standardmäßig vollständig sperren
- Open WebUI und OpenHands unabhängig voneinander aktivieren

## Sicherer lokaler Start

```bash
cp .env.example .env
# Alle Geheimnisse ersetzen; RUNPOD_ALLOW_BILLABLE_ACTIONS=false lassen.
docker compose up --build -d
```

Anschließend `http://127.0.0.1:8080` öffnen. Solange die Kostensperre aktiv ist,
kann GPUHarbor keinen kostenpflichtigen Pod starten.

## Optionale Komponenten

```bash
# Open WebUI
docker compose -f compose.yml -f compose.openwebui.yml up -d --build

# OpenHands – besitzt weitreichende Ausführungsrechte
docker compose -f compose.yml -f compose.openhands.yml up -d --build
```

Vor OpenHands unbedingt [die Sicherheitshinweise](docs/integrations/openhands.md)
lesen. Das Projekt befindet sich noch im lokalen Vorbereitungsstadium, besitzt
noch keine endgültige Lizenz und wird noch nicht öffentlich veröffentlicht.
