"""
File system utilities: collecting, hashing, cleaning names.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Optional, Set

SUPPORTED_EXTENSIONS_DEFAULT = {".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wma",
                                ".wav", ".aiff", ".ape", ".opus", ".mp4"}

def full_hash(path: Path) -> str:
    """SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()

def clean_name(name: str) -> str:
    """Normalize filename for fuzzy grouping."""
    name = name.lower()
    name = re.sub(r"[\s_\-\.]+", " ", name)
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    return name.strip()

def collect_audio_files(root: Path,
                        extensions: Optional[Set[str]] = None,
                        exclude_patterns: List[str] = None,
                        min_size_kb: int = 0,
                        min_duration_sec: float = 0) -> List[Path]:
    """Walk directory and return audio files matching criteria."""
    exts = extensions or SUPPORTED_EXTENSIONS_DEFAULT
    exclude = [p.lower() for p in (exclude_patterns or [])]
    min_bytes = min_size_kb * 1024

    files = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if min_bytes and p.stat().st_size < min_bytes:
            continue
        if exclude and any(pat in str(p).lower() for pat in exclude):
            continue
        # min_duration check deferred until after audio info loaded
        files.append(p)
    # If min_duration > 0, we filter after loading info in deduplicator
    return files
