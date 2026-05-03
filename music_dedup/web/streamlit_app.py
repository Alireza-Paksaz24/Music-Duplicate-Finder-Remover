"""
Beautiful Web UI for Music Dedup (Streamlit).
"""

import streamlit as st
import sys
import io
import json
from pathlib import Path
from typing import Optional
import logging

# Fix import path — add the PARENT directory (MusicDuplicateFounder)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_dedup.core.config import Config
from music_dedup.core.deduplicator import Deduplicator


st.set_page_config(page_title="Music Dedup", layout="wide")
st.title("🎵 Music Duplicate Finder & Remover")

col1, col2 = st.columns(2)

with col1:
    directory = st.text_input("📁 Music folder", value=str(Path.home() / "Music"))
    threshold = st.slider("🎚️ Similarity threshold", 0.0, 1.0, 0.85, 0.01)
    method = st.selectbox("🔍 Detection method", ["auto", "fingerprint", "exact", "name"])

with col2:
    dry_run = st.checkbox("🛡️ Dry run (preview only)", True)
    trash_dir = st.text_input("🗑️ Trash folder (optional)", "")
    keep_largest = st.checkbox("📀 Keep largest file (ignore cover/metadata)")
    keep_path = st.text_input("🧲 Keep path pattern (e.g., FLAC)")

show_pairs = st.checkbox("Show all pair similarity scores (slow)")

run_button = st.button("🚀 Start Scan", type="primary")

if "report" not in st.session_state:
    st.session_state.report = None
    st.session_state.log_output = ""

if run_button:
    # Build config
    config = Config(
        directory=Path(directory).expanduser(),
        dry_run=dry_run,
        trash_dir=Path(trash_dir).expanduser() if trash_dir else None,
        threshold=threshold,
        method=method,
        keep_largest=keep_largest,
        keep_path_pattern=keep_path if keep_path else None,
        show_all_pairs=show_pairs,
        quiet=True  # we'll capture log and display in Streamlit
    )

    dedup = Deduplicator(config)

    # Progress bar and status
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_area = st.empty()

    # Capture logs to display
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    logger = logging.getLogger()
    logger.addHandler(handler)

    def update_progress(pct, msg):
        progress_bar.progress(min(pct, 1.0))
        status_text.text(msg)

    dedup.set_progress_callback(update_progress)

    report = dedup.run()

    # Display log
    log_output = log_stream.getvalue()
    st.session_state.log_output = log_output
    st.session_state.report = report

    st.success("✅ Scan complete!")
    st.subheader("📄 Log")
    st.code(log_output, language="text")

    # Show report
    st.subheader("📊 Report")
    if report:
        st.dataframe([
            {
                "Group": g["group"],
                "Similarity": g["similarity"],
                "Keep": Path(g["keep"]).name,
                "Keep Info": g["keep_info"],
                "Removed Count": len(g["removed"]),
            }
            for g in report
        ])
        # Download button
        st.download_button("Download JSON Report",
                           data=json.dumps(report, indent=2),
                           file_name="dedup_report.json")

    # Remove added handler
    logger.removeHandler(handler)
