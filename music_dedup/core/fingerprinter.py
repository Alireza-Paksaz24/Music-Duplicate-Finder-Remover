"""
Audio fingerprinting using Chromaprint (fpcalc).
Computes raw integer vectors and similarity scores.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import numpy as np

log = logging.getLogger(__name__)


def get_raw_fingerprint(filepath: Path) -> Optional[List[int]]:
    """Run fpcalc -raw to get the fingerprint integer vector."""
    try:
        result = subprocess.run(
            ["fpcalc", "-raw", "-json", str(filepath)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            fp = data.get("fingerprint")
            if isinstance(fp, list):
                return fp
            if isinstance(fp, str):
                return [int(x) for x in fp.split(",") if x.strip()]
    except FileNotFoundError:
        log.error("fpcalc not found. Install libchromaprint-tools.")
    except Exception as e:
        log.debug(f"fpcalc error for {filepath}: {e}")
    return None


def compute_similarity(fp1: List[int], fp2: List[int]) -> float:
    """
    Calculate similarity (0.0 - 1.0) using Hamming distance on 32‑bit chunks,
    blended with length ratio.
    """
    if not fp1 or not fp2:
        return 0.0
    min_len = min(len(fp1), len(fp2))
    max_len = max(len(fp1), len(fp2))
    if min_len == 0:
        return 0.0

    length_ratio = min_len / max_len

    a = np.array(fp1[:min_len], dtype=np.uint32)
    b = np.array(fp2[:min_len], dtype=np.uint32)
    xor = np.bitwise_xor(a, b)

    # Population count for each uint32
    bits_set = np.zeros(len(xor), dtype=np.int32)
    temp = xor.copy()
    while np.any(temp > 0):
        bits_set += (temp & 1).astype(np.int32)
        temp = np.right_shift(temp, 1)

    matching_bits = int(32 * min_len - np.sum(bits_set))
    total_bits = 32 * min_len
    bit_sim = matching_bits / total_bits if total_bits > 0 else 0.0

    return 0.8 * bit_sim + 0.2 * length_ratio


class Fingerprinter:
    """Handles fingerprint computation and caching (optional)."""
    def __init__(self, cache: Optional[Dict[Path, Optional[List[int]]]] = None):
        self.cache = cache or {}

    def fingerprint(self, path: Path) -> Optional[List[int]]:
        if path in self.cache:
            return self.cache[path]
        fp = get_raw_fingerprint(path)
        self.cache[path] = fp
        return fp
