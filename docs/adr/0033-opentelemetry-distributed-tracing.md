# ADR-0033 — Observability: structlog statt OpenTelemetry/Jaeger

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Phase F — Dokumentation downgraded Topics (Master-Plan v3.1, Scope-Downsizing)

---

## Kontext

AECT nutzt structlog mit JSON-Output und CorrelationIDMiddleware
(`logging_config.py`, eingerichtet in Phase B). OpenTelemetry/Jaeger
stand als Alternative fuer Distributed Tracing auf der Downsizing-Liste.

Was implementiert ist:
- structlog: request_id + route + status + latency_ms + token_count
  pro Log-Eintrag, JSON-Format, kompatibel mit Azure Monitor und ELK.
- CorrelationIDMiddleware: propagiert request_id automatisch durch alle
  Log-Events eines Request-Lifecycle.
- Logging-Allowlist (aect-security-checklist v2.1): kein Body, kein
  Prompt, kein PII in Logs.

---

## Alternativen

**A) structlog + Correlation-ID (umgesetzt)**

Pros: kein Infra-Overhead; JSON-Output direkt Azure-Monitor-kompatibel;
request_id liefert request-level Rueckverfolgbarkeit fuer Single-Service.
Cons: kein span-basiertes Tracing; keine automatische Instrumentierung
externer Calls (Azure OpenAI Latenz, ChromaDB Query-Latenz als separate
Spans nicht sichtbar).

**B) OpenTelemetry SDK + Jaeger (Design, nicht gebaut)**

Pros: span-basiertes Distributed Tracing; auto-Instrumentierung fuer
FastAPI, httpx, SQLite; standardisiertes W3C-Trace-Context-Format;
exportierbar nach Jaeger (lokal), Azure Monitor Application Insights
oder beliebigem OTLP-Collector.
Cons: opentelemetry-sdk + Exporter als Dependency (~6 Pakete, davon 3
bereits transitiv vorhanden); Jaeger-Container oder Azure Monitor
Workspace als Infra-Voraussetzung; Azure Monitor Application Insights
ab Freigrenze ~2-5 EUR/Monat; Komplexitaet unverhältnismaessig fuer
Single-Service-Architektur.

Design-Skizze (B):

    # Zusaetzliche Abhaengigkeit (opentelemetry-api/sdk/exporter-otlp
    # bereits als transitive Deps von chromadb-client installiert)
    uv add opentelemetry-instrumentation-fastapi

    # app.py -- Tracing-Setup vor app = FastAPI()
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    # nach app = FastAPI():
    FastAPIInstrumentor.instrument_app(app)

    # Jaeger lokal (Port 16686 UI, 4317 OTLP-Eingang)
    docker run -d -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one

---

## Entscheidung

A) structlog bleibt. OpenTelemetry/Jaeger: verstanden, Design oben
skizziert, bewusst nicht aktiviert.

Gruende:
1. AECT ist ein Single-Service ohne Microservice-Verbund -- Distributed
   Tracing loest ein Problem, das hier nicht existiert.
2. request_id via CorrelationIDMiddleware liefert vollstaendige
   Request-level-Rueckverfolgbarkeit fuer alle Observability-Anforderungen
   eines privaten Builds.
3. structlog-JSON ist bereits Azure-Monitor-kompatibel -- der Logging-
   Layer muss bei einem kuenftigen Cloud-Deploy nicht geaendert werden.
4. Infra-Overhead (Jaeger-Container oder Azure-Monitor-Workspace) ist
   fuer ein privates Portfolio-Build nicht gerechtfertigt (Scope-Disziplin).

---

## Konsequenzen

- structlog bleibt alleinige Logging-Loesung in v1.
- Kein zusaetzlicher Infra-Baustein, kein zusaetzliches Docker-Volume.
- Fuer einen produktiven Multi-Service-Einsatz waere OTel mit
  W3C-Trace-Context der naechste Schritt; Einstiegspunkt ist dieser ADR.
- Interview-Position: bewusste Entscheidung mit Design-Nachweis --
  kein Wissensmangel, sondern Scope-Disziplin.
