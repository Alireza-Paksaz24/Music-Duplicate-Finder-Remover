"""
Detection strategies: exact hash, acoustic similarity, name+duration.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
import re

from .fingerprinter import compute_similarity, Fingerprinter
from ..utils.files import full_hash, clean_name
from ..utils.audio import get_audio_info

log = logging.getLogger(__name__)


def group_exact(files: List[Path]) -> Tuple[List[List[Path]], Set[Path]]:
    """Group byte-identical files."""
    buckets = defaultdict(list)
    for f in files:
        buckets[full_hash(f)].append(f)
    groups = [v for v in buckets.values() if len(v) > 1]
    used = {f for g in groups for f in g}
    return groups, used


def group_by_similarity(
    files: List[Path],
    threshold: float,
    fingerprinter: Fingerprinter,
    show_all_pairs: bool = False,
) -> List[dict]:
    """
    Acoustic similarity grouping via union-find.
    Returns list of dicts: {'files': [...], 'similarity': max_sim}
    """
    log.info("Computing fingerprints...")
    fp_cache = {}
    for f in files:
        log.info(f"  fpcalc ← {f.name}")
        fp_cache[f] = fingerprinter.fingerprint(f)

    file_list = [f for f in files if fp_cache[f] is not None]
    if not file_list:
        return []

    n = len(file_list)
    log.info(f"Calculating {n*(n-1)//2} pairwise similarities...")

    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            sim = compute_similarity(fp_cache[file_list[i]], fp_cache[file_list[j]])
            pairs.append((sim, file_list[i], file_list[j]))

    pairs.sort(reverse=True)

    if show_all_pairs:
        log.info("\n── All pairs sorted by similarity ──")
        for sim, fi, fj in pairs:
            marker = "✅ DUPLICATE" if sim >= threshold else ("⚠️  SIMILAR" if sim >= 0.65 else "   different")
            log.info(f"  {sim:.3f}  {marker}  {fi.name}  ↔  {fj.name}")
        log.info("────────────────────────────────────\n")

    # Union-find
    parent = {f: f for f in file_list}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        parent[find(x)] = find(y)

    pair_sims: Dict[Tuple[Path, Path], float] = {}
    for sim, fi, fj in pairs:
        pair_sims[(fi, fj)] = sim
        if sim >= threshold:
            union(fi, fj)

    clusters = defaultdict(list)
    for f in file_list:
        clusters[find(f)].append(f)

    groups = []
    for cluster in clusters.values():
        if len(cluster) < 2:
            continue
        max_sim = max(pair_sims.get((a, b), pair_sims.get((b, a), 0.0))
                      for i, a in enumerate(cluster)
                      for b in cluster[i+1:])
        groups.append({"files": cluster, "similarity": max_sim})

    groups.sort(key=lambda x: x["similarity"], reverse=True)
    return groups


def group_by_name_duration(files: List[Path]) -> List[List[Path]]:
    """Group by cleaned filename stem and similar duration."""
    infos = {f: get_audio_info(f) for f in files}
    buckets = defaultdict(list)
    for f in files:
        buckets[clean_name(f.stem)].append(f)

    groups = []
    for bucket in buckets.values():
        if len(bucket) < 2:
            continue
        used = set()
        for i, fi in enumerate(bucket):
            if fi in used:
                continue
            dur_i = infos[fi].get("duration")
            grp = [fi]
            used.add(fi)
            for j, fj in enumerate(bucket):
                if i == j or fj in used:
                    continue
                dur_j = infos[fj].get("duration")
                if dur_i is None or dur_j is None or abs(dur_i - dur_j) <= 4:
                    grp.append(fj)
                    used.add(fj)
            if len(grp) > 1:
                groups.append(grp)
    return groups
