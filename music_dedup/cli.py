#!/usr/bin/env python3
"""
Command-line interface for Music Dedup.
"""

import sys
import argparse
from pathlib import Path
import logging

from .core.config import Config
from .core.deduplicator import Deduplicator

def main():
    parser = argparse.ArgumentParser(
        description="Find and remove duplicate music files based on acoustic similarity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run with --dry-run first to preview changes."
    )
    parser.add_argument("directory", type=Path, help="Root music directory")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview without deleting")
    parser.add_argument("--trash", type=Path, help="Move duplicates to trash folder")
    parser.add_argument("--threshold", "-t", type=float, default=0.85,
                        help="Similarity threshold (0-1, default 0.85)")
    parser.add_argument("--method", choices=["auto","fingerprint","exact","name"],
                        default="auto", help="Detection method")
    parser.add_argument("--extensions", nargs="+",
                        help="Only scan these extensions (e.g., .mp3 .flac)")
    parser.add_argument("--exclude", nargs="+", help="Exclude files/folders containing these strings")
    parser.add_argument("--min-size", type=int, default=0,
                        help="Ignore files smaller than this KB")
    parser.add_argument("--min-duration", type=float, default=0.0,
                        help="Ignore files shorter than this seconds")
    parser.add_argument("--keep-largest", action="store_true",
                        help="Keep the largest file regardless of cover/metadata")
    parser.add_argument("--keep-path", help="Always keep file whose path contains this pattern")
    parser.add_argument("--show-all-pairs", action="store_true",
                        help="Print all file pairs and similarity scores")
    parser.add_argument("--no-confirm", action="store_true",
                        help="Skip confirmation prompt")
    parser.add_argument("--report", default="dedup_report.json",
                        help="JSON report path")
    parser.add_argument("--log-file", default="music_dedup.log",
                        help="Log file path")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress progress lines")

    args = parser.parse_args()

    # Build config
    config = Config(
        directory=args.directory.resolve(),
        dry_run=args.dry_run,
        trash_dir=args.trash.resolve() if args.trash else None,
        threshold=args.threshold,
        method=args.method,
        extensions=set(args.extensions) if args.extensions else None,
        exclude_patterns=args.exclude or [],
        min_size_kb=args.min_size,
        min_duration_sec=args.min_duration,
        keep_largest=args.keep_largest,
        keep_path_pattern=args.keep_path,
        show_all_pairs=args.show_all_pairs,
        no_confirm=args.no_confirm,
        report_file=Path(args.report),
        log_file=Path(args.log_file),
        quiet=args.quiet,
    )

    # Logging setup
    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=level,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[
                            logging.StreamHandler(sys.stdout),
                            logging.FileHandler(config.log_file, encoding="utf-8")
                        ])
    log = logging.getLogger(__name__)

    dedup = Deduplicator(config)

    # Confirmation prompt unless dry-run or --no-confirm
    if not config.dry_run and not config.no_confirm:
        print("⚠️  This will permanently DELETE duplicates. Type 'yes' to confirm:")
        if input().strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    dedup.run()

if __name__ == "__main__":
    main()
