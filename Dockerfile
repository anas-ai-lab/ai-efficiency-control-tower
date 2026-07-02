# AECT -- FastAPI Application Container (Multi-Stage)
# Phase F, aect-security-checklist v2.1: Non-root-User im finalen Image.
# AUDIT-005: Multi-Stage-Build -- Build-Tools (uv) bleiben in Stage 1,
# das finale Image enthaelt nur .venv + Quellcode + Runtime-Assets.
#
# Deployment-Kontext (ADR-0035 Azure Container Apps -- nur Design in v1):
#   - AECT_API_KEY und AECT_AZURE_OPENAI_* als Secrets injizieren, nie als ENV
#   - ChromaDB laeuft als separater Container (docker-compose.yml)
#   - EU-Data-Zone: Deployment-Region muss swedencentral/westeurope sein (ADR-0003)
#
# Basis-Images per SHA-Digest gepinnt (Phase-2-Fix, analog SHA-gepinnter
# GitHub-Actions): Tag-Kommentar dokumentiert den aufgeloesten Stand
# (2026-07-02). Bump = neuen Digest eintragen, bewusster Schritt statt
# stillem Upstream-Drift.

# ─── Stage 1: Builder ────────────────────────────────────────────────────────
# Installiert alle Abhaengigkeiten + Projekt in /app/.venv. uv lebt nur hier.
FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf AS builder

# uv aus offiziellem Image -- kein curl-pipe-sh.
COPY --from=ghcr.io/astral-sh/uv:0.11.26@sha256:3d868e555f8f1dbc324afa005066cd11e1053fc4743b9808ca8025283e65efa5 /uv /uvx /usr/local/bin/

WORKDIR /app

# UV_COMPILE_BYTECODE: schnellerer Start. UV_LINK_MODE=copy: keine Hardlink-
# Warnung beim Schreiben in .venv (separates Layer-Dateisystem).
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Layer-Caching: Dependency-Files zuerst, Source danach.
# --no-install-project: installiert nur die Abhaengigkeiten, noch nicht das Projekt.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Anwendungscode -- invalidiert ab hier.
# Projekt installieren (editable via setuptools.build_meta, Fallen-Katalog SS6.4).
# Editable-Install zeigt nach /app/src -> finaler Stage muss src ebenfalls
# unter /app/src ablegen, sonst schlaegt der Import fehl.
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ─── Stage 2: Final ──────────────────────────────────────────────────────────
# Kein uv, kein Build-Tool. Nur Python-Runtime, .venv, Quellcode, Assets.
FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf AS final

# curl ausschliesslich fuer HEALTHCHECK (python:slim bringt es nicht mit).
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Non-root user. --no-create-home: kein /home/aect -- unnoetig fuer Server.
# /bin/false: kein Shell-Login moeglich.
RUN groupadd --gid 1000 aect && \
    useradd --uid 1000 --gid aect --no-create-home --shell /bin/false aect

WORKDIR /app

# Virtuelle Umgebung aus dem Builder uebernehmen -- enthaelt alle Deps + Projekt.
COPY --from=builder /app/.venv /app/.venv

# Quellcode + Runtime-Assets relativ zu /app/ (Pfad-Konvention __file__ -> parents[3]).
COPY src/ ./src/
COPY config/ ./config/
COPY knowledge_base/ ./knowledge_base/
COPY prompts/ ./prompts/

# .venv/bin in PATH -> uvicorn direkt aufrufbar, ohne uv im finalen Image.
ENV PATH="/app/.venv/bin:$PATH"

# Eigentuemer auf non-root user uebertragen (inkl. .venv).
# Muss nach allen COPY-Schritten als root erfolgen.
RUN chown -R aect:aect /app

# Ab hier: kein root mehr.
USER aect

EXPOSE 8000

# HEALTHCHECK: curl -f liefert bei != 2xx einen Exit-Code != 0 -> Docker markiert
# den Container als unhealthy. Shell-Form, weil "|| exit 1" einen Shell-Operator
# braucht (Exec-Form ["curl", ..., "||", "exit 1"] wuerde "||" als URL behandeln).
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# JSON-Array-Form: uvicorn erhaelt SIGTERM direkt (kein Shell-Wrapper).
# --no-access-log: FastAPI-Accesslog ist kein structlog-JSON -- Formatinkonsistenz.
# Requests sind per CorrelationIDMiddleware ohnehin in structlog erfasst (app.py).
CMD ["uvicorn", "aect.adapters.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-server-header"]
