#!/usr/bin/env python3
"""
SHA-Pinning fuer GitHub Actions Workflows.
AECT Phase F -- aect-security-checklist v2.1

Ersetzt alle `uses: owner/repo@ref` durch `uses: owner/repo@SHA  # ref`.
Ueberspringt bereits gepinnte Actions (40-stellige SHA) und lokale Actions (./).
Benoetigt: Python 3.12, keine externen Pakete, Netzwerkzugang zu api.github.com.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_RE = re.compile(r"^([ \t]*-?\s*uses:\s+)([^@\s]+)@([^\s#]+)(.*)")


def _get_commit_sha(owner_repo: str, ref: str) -> str | None:
    url = f"https://api.github.com/repos/{owner_repo}/commits/{ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "aect-pin-ci/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("sha")
    except urllib.error.HTTPError as exc:
        print(f"  HTTP {exc.code} fuer {owner_repo}@{ref}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"  Fehler bei {owner_repo}@{ref}: {exc}", file=sys.stderr)
        return None


def _owner_repo(action: str) -> str | None:
    """Gibt owner/repo zurueck. None fuer lokale Actions (./)."""
    if action.startswith("./") or action.startswith("/"):
        return None
    parts = action.split("/")
    return f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else None


def pin_workflow(path: Path) -> int:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    pinned = 0

    for i, line in enumerate(lines):
        m = USES_RE.match(line)
        if not m:
            continue
        prefix, action, ref, _rest = m.groups()
        ref = ref.strip()

        if SHA_RE.match(ref):
            print(f"  SKIP (bereits gepinnt): {action}@{ref[:8]}...")
            continue

        or_ = _owner_repo(action)
        if or_ is None:
            print(f"  SKIP (lokal): {action}")
            continue

        print(f"  Pinne: {action}@{ref} ... ", end="", flush=True)
        sha = _get_commit_sha(or_, ref)
        if sha:
            lines[i] = f"{prefix}{action}@{sha}  # {ref}\n"
            print(f"OK ({sha[:8]}...)")
            pinned += 1
        else:
            print("FEHLER -- Zeile unveraendert")

    path.write_text("".join(lines), encoding="utf-8")
    return pinned


if __name__ == "__main__":
    target = Path(".github/workflows/ci.yml")
    if not target.exists():
        print(f"FEHLER: {target} nicht gefunden", file=sys.stderr)
        sys.exit(1)
    print(f"SHA-Pinning: {target}\n")
    count = pin_workflow(target)
    print(f"\nErgebnis: {count} Action(s) gepinnt.")
