# 0018 -- ChromaDB als lokaler Docker-Container

**Status:** Accepted
**Datum:** 2026-06-18
**Phase:** D (RAG)

## Kontext

Phase D braucht einen Vektor-Store fuer Hybrid-Retrieval (BM25 + Vektor,
ADR-0014). Stack-Lock: ChromaDB lokal. Chroma laeuft als Server-Prozess;
der empfohlene Betrieb ist ein Container, nicht ein eingebetteter
In-Process-Store. Die Security-Checkliste Phase D fordert: kein offener
Port, Persist-Dir chmod 700, Non-root-Owner.

## Entscheidung

ChromaDB laeuft als gepinnter Docker-Container (`chromadb/chroma:1.5.3`)
ueber `docker-compose.yml`. Datenpersistenz im host-gemounteten
Verzeichnis `./chroma_db` (Mount-Ziel `/data`, v1.x-Konvention),
chmod 700. Port-Mapping ausschliesslich `127.0.0.1:8001:8000` --
erreichbar nur vom Host, nicht aus dem Netz. Version gepinnt fuer
reproduzierbare Builds.

## Abweichungen von der Checkliste (bewusst, kompensiert)

- "Kein offener Port / nur internes Docker-Netz": AECT laeuft in v1 via
  `uv run` auf dem Host (kein AECT-Dockerfile), braucht also Host-Zugriff
  auf Chroma. Statt internem Docker-Netz: 127.0.0.1-only-Binding. Der
  Sicherheitszweck (keine externe Exposition) ist erfuellt.
- "Non-root-Owner im Container": [HIER eintragen, was `docker exec id`
  ergeben hat]. Falls das offizielle Image als root laeuft, wird die echte
  Container-Haertung (eigenes Dockerfile mit USER-Direktive) bewusst auf
  den Phase-F-Hardening-Pass verschoben -- analog zur SHA-Pinning- und
  Branch-Protection-Behandlung. Kompensierende Kontrollen jetzt:
  127.0.0.1-only, chmod 700, gepinnte Version.

## Konsequenzen

- Reproduzierbares, vom frischen Clone startbares RAG-Backend
  (`docker compose up -d`).
- `chroma_db/` ist via .gitignore vom Tracking ausgenommen -- Daten landen
  nie im Repo.
- Der Chroma-Python-Client (`chromadb`) wird erst mit dem Retriever-Adapter
  eingefuehrt, nicht hier -- kein Paket vor dem Code, der es nutzt.
- Restart-Policy bewusst weggelassen: kein Dauerlaeufer, Container startet
  nur auf explizites `docker compose up`.

## Alternativen

- Eingebetteter In-Process-Chroma (PersistentClient ohne Server): einfacher,
  aber weicht vom realistischen Deployment-Bild ab und macht den spaeteren
  Hybrid-/Client-Server-Pfad unnoetig anders. Verworfen.
- `latest`-Tag statt Pinning: verworfen (unkontrollierte Upgrades brechen
  Client-Kompatibilitaet).
