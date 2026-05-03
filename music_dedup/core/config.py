from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

@dataclass
class Config:
    """Master configuration for a dedup run."""
    directory: Path
    dry_run: bool = True
    trash_dir: Optional[Path] = None
    threshold: float = 0.85
    method: str = "auto"               # auto, fingerprint, exact, name
    extensions: Optional[Set[str]] = None
    exclude_patterns: List[str] = field(default_factory=list)
    min_size_kb: int = 0
    min_duration_sec: float = 0.0
    keep_largest: bool = False
    keep_path_pattern: Optional[str] = None
    show_all_pairs: bool = False
    no_confirm: bool = False
    report_file: Path = Path("dedup_report.json")
    log_file: Path = Path("music_dedup.log")
    quiet: bool = False
