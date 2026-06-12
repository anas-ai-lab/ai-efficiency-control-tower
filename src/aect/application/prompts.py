"""Prompt-Loader -- laedt versionierte Prompt-Dateien aus prompts/.

Pfadauflösung analog aect.domain.roi.load_roi_config(): src/aect/application/
liegt auf derselben Tiefe wie src/aect/domain/ -- parents[3] fuehrt zum
Repo-Root.

Versionierung: prompts/<name>/<version>/<role>.md. Aendern eines Prompts
heisst eine neue Versionsdatei anlegen, nicht die alte ueberschreiben --
prompt_version im SharpenedUseCase-Ergebnis macht nachvollziehbar, welche
Prompt-Version welches Ergebnis erzeugt hat.
"""

from __future__ import annotations

from pathlib import Path


def load_prompt(name: str, role: str, version: str = "v1") -> str:
    """Laedt eine Prompt-Datei aus prompts/<name>/<version>/<role>.md.

    Args:
        name: Prompt-Familie, z. B. "sharpen_use_case".
        role: "system" oder "user".
        version: Versionsordner, Default "v1".

    Raises:
        FileNotFoundError: Wenn name/version/role nicht existiert.
    """
    # src/aect/application/prompts.py -> parents[0]=application, [1]=aect,
    # [2]=src, [3]=repo_root
    repo_root = Path(__file__).resolve().parents[3]
    path = repo_root / "prompts" / name / version / f"{role}.md"
    return path.read_text(encoding="utf-8")
