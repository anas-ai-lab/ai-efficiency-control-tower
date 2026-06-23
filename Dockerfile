# AECT -- FastAPI Application Container
# Phase F, aect-security-checklist v2.1: Non-root-User im finalen Dockerfile.
#
# Deployment-Kontext (ADR-0035 Azure Container Apps -- nur Design in v1):
#   - AECT_API_KEY und AECT_AZURE_OPENAI_* als Secrets injizieren, nie als ENV
#   - ChromaDB laeuft als separater Container (docker-compose.yml)
#   - EU-Data-Zone: Deployment-Region muss swedencentral/westeurope sein (ADR-0003)
#
# uv-Image-Version: derzeit "latest" -- fuer Produktion auf SHA pinnen
# (analog GitHub-Actions, aect-security-checklist Phase F).

FROM python:3.12-slim

# Non-root user. --no-create-home: kein /home/aect -- unnoetig fuer Server.
# /bin/false: kein Shell-Login moeglich.
RUN groupadd --gid 1000 aect && \
    useradd --uid 1000 --gid aect --no-create-home --shell /bin/false aect

# uv aus offiziellem Image -- kein curl-pipe-sh.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Layer-Caching: Dependency-Files zuerst, Source danach.
# --no-install-project: installiert nur die Abhaengigkeiten, noch nicht das Projekt.
# Naechster Layer-Invalidierung nur bei Quellcode-Aenderung, nicht bei Dep-Aenderung.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Anwendungscode -- invalidiert ab hier.
COPY src/ ./src/

# Projekt installieren (editable via setuptools.build_meta, Fallen-Katalog SS6.4).
# __file__ zeigt nach /app/src/aect/... -> parents[3] = /app (Repo-Root-Konvention
# aus tools.py / prompts.py). Config + Prompts + KB muessen deshalb unter /app/ liegen.
RUN uv sync --frozen --no-dev

# Runtime-Assets relativ zu /app/ (Pfad-Konvention, siehe oben).
COPY config/ ./config/
COPY knowledge_base/ ./knowledge_base/
# prompts/ -- load_prompt() erwartet Verzeichnis unter Repo-Root.
# Hinweis: Verzeichnis muss existieren; fehlt es beim docker build, schlaegt COPY fehl.
COPY prompts/ ./prompts/

# Eigentuemer auf non-root user uebertragen (inkl. .venv).
# Muss nach allen RUN-Schritten als root erfolgen.
RUN chown -R aect:aect /app

# Ab hier: kein root mehr.
USER aect

EXPOSE 8000

# JSON-Array-Form: uvicorn erhaelt SIGTERM direkt (kein Shell-Wrapper).
# --no-access-log: FastAPI-Accesslog ist kein structlog-JSON -- Formatinkonsistenz.
# Requests sind per CorrelationIDMiddleware ohnehin in structlog erfasst (app.py).
CMD ["uv", "run", "uvicorn", "aect.adapters.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
