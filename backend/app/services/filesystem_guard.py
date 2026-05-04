from __future__ import annotations

import re
from pathlib import Path


SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._\-/]+")


def sanitize_relative_path(path: str) -> str:
    cleaned = path.replace("\\", "/").strip()
    cleaned = SAFE_NAME_RE.sub("_", cleaned)
    cleaned = cleaned.lstrip("/")
    if ".." in Path(cleaned).parts:
        raise ValueError("Ruta inválida: no se permite '..'")
    return cleaned


def safe_join(base_dir: Path | str, relative_path: str) -> Path:
    base = Path(base_dir).expanduser().resolve()
    rel = sanitize_relative_path(relative_path)
    target = (base / rel).resolve()

    if not str(target).startswith(str(base)):
        raise ValueError("Ruta fuera del directorio permitido")

    return target
