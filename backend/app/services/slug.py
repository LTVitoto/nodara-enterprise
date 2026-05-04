from __future__ import annotations

import re
import unicodedata


_slug_re = re.compile(r"[^a-zA-Z0-9_-]+")


def slugify(value: str, max_len: int = 100) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.strip().lower().replace(" ", "_")
    normalized = _slug_re.sub("_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return (normalized or "proyecto")[:max_len]
