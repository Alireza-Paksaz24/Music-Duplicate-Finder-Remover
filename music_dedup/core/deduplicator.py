"""
Orchestrator that ties scanning, matching, scoring, and deletion together.
"""

import logging
import os
import shutil
import json
from pathlib import Path
from typing import List, Set, Callable, Optional

from .config import Config
from .fingerprinter import Fingerprinter
from .matcher import group_exact, group_by_similarity, group_by_name_duration
from .scorer import pick_best, score_file
from ..utils.files import collect_audio_files
from ..utils.audio import get_audio_info, fmt_score

log = logging.getLogger(__name__)


class Deduplicator:
    def __init__(self, config: Config):
        self.config = config
        self.fingerprinter = Fingerprinter()
        self.progress_callback: Optional[Callable[[float, str], None]] = None

    def set_progress_callback(self, callback: Callable[[float, str], None]):
        self.progress_callback = callback

    def _update_progress(self, fraction: float, message: str):
        if self.progress_callback:
            self.progress_callback(fraction, message)
        else:
            log.info(message)

    def run(self) -> List[dict]:
        """Execute deduplication and return a report (list of groups)."""
        cfg = self.config
        self._update_progress(0.0, "Collecting audio files...")

        # Collect files with all filters applied
        files = collect_audio_files(
            cfg.directory,
            extensions=cfg.extensions,
            exclude_patterns=cfg.exclude_patterns,
            min_size_kb=cfg.min_size_kb,
            min_duration_sec=cfg.min_duration_sec,
        )

        self._update_progress(0.1, f"Found {len(files)} audio files.")

        all_groups = []
        used_exact: Set[Path] = set()
        fp_group_metas = []

        # 1. Exact duplicates
        if cfg.method in ("auto", "exact"):
            exact_groups, used_exact = group_exact(files)
            self._update_progress(0.2, f"Exact duplicate groups: {len(exact_groups)}")
            all_groups.extend(exact_groups)

        remaining = [f for f in files if f not in used_exact]

        # 2. Acoustic similarity
        if cfg.method in ("auto", "fingerprint") and remaining:
            self._update_progress(0.3, "Computing acoustic similarities...")
            sim_groups = group_by_similarity(
                remaining,
                cfg.threshold,
                self.fingerprinter,
                show_all_pairs=cfg.show_all_pairs,
            )
            self._update_progress(0.7, f"Acoustic similarity groups: {len(sim_groups)}")
            for g in sim_groups:
                fp_group_metas.append(g)
                all_groups.append(g["files"])
            used_fp = {f for g in sim_groups for f in g["files"]}
            remaining = [f for f in remaining if f not in used_fp]

        # 3. Name+duration fallback
        if cfg.method in ("auto", "name") and remaining:
            name_groups = group_by_name_duration(remaining)
            self._update_progress(0.8, f"Name+duration groups: {len(name_groups)}")
            all_groups.extend(name_groups)

        self._update_progress(0.9, f"Total duplicate groups: {len(all_groups)}")

        if not all_groups:
            self._update_progress(1.0, "No duplicates found!")
            return []

        # Build similarity lookup for reporting
        sim_lookup = {}
        for g in fp_group_metas:
            for f in g["files"]:
                sim_lookup[f] = g["similarity"]

        report = []
        total_removed = 0
        total_bytes_freed = 0

        for idx, group in enumerate(all_groups):
            keep, to_remove = pick_best(
                group,
                keep_largest=cfg.keep_largest,
                keep_path_pattern=cfg.keep_path_pattern,
            )
            sims = [sim_lookup[f] for f in group if f in sim_lookup]
            max_sim = max(sims) if sims else None

            keep_info = get_audio_info(keep)
            entry = {
                "group": idx + 1,
                "similarity": max_sim,
                "keep": str(keep),
                "keep_info": fmt_score(keep_info),
                "removed": [],
            }

            for r in to_remove:
                r_info = get_audio_info(r)
                total_bytes_freed += r_info["size"]
                total_removed += 1
                action = "dry_run"

                if not cfg.dry_run:
                    try:
                        if cfg.trash_dir:
                            cfg.trash_dir.mkdir(parents=True, exist_ok=True)
                            dest = cfg.trash_dir / r.name
                            if dest.exists():
                                dest = cfg.trash_dir / f"{r.stem}_{idx}{r.suffix}"
                            shutil.move(str(r), str(dest))
                            action = f"moved_to_trash:{dest}"
                        else:
                            os.remove(r)
                            action = "deleted"
                    except Exception as e:
                        action = f"error:{e}"
                        log.error(f"Failed to remove {r}: {e}")

                entry["removed"].append({
                    "path": str(r),
                    "info": fmt_score(r_info),
                    "score": list(score_file(r)),
                    "size_bytes": r_info["size"],
                    "action": action,
                })

            report.append(entry)

        self._update_progress(
            1.0,
            f"Done! {len(all_groups)} groups | {total_removed} files to remove | "
            f"{total_bytes_freed / 1024**2:.1f} MB freed"
        )

        # Save report
        with open(cfg.report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report

