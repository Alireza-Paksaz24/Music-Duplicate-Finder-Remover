"""
File ranking rules: keep the best based on cover art, metadata, size.
"""

from pathlib import Path
from typing import List, Tuple, Optional
from ..utils.audio import get_audio_info
import logging

log = logging.getLogger(__name__)


def score_file(path: Path) -> Tuple[int, int, int]:
    """Return a tuple for ranking: (has_cover (0/1), tag_count, file_size)."""
    info = get_audio_info(path)
    return (
        int(info["has_cover"]),
        info["tag_count"],
        info["size"],
    )


def pick_best(group: List[Path],
              keep_largest: bool = False,
              keep_path_pattern: Optional[str] = None) -> Tuple[Path, List[Path]]:
    """
    From a list of duplicate files, return (keep, to_remove) according to rules.
    """
    if len(group) == 1:
        return group[0], []

    # If a path pattern is given, force keep the first matching file
    if keep_path_pattern:
        pat = keep_path_pattern.lower()
        preferred = [f for f in group if pat in str(f).lower()]
        if preferred:
            keep = preferred[0]
            return keep, [f for f in group if f != keep]

    # Score all files
    scored = [(f, score_file(f)) for f in group]
    if keep_largest:
        scored.sort(key=lambda x: x[1][2], reverse=True)  # by size
    else:
        scored.sort(key=lambda x: x[1], reverse=True)     # cover > tags > size

    keep = scored[0][0]
    to_remove = [f for f in group if f != keep]
    return keep, to_remove
