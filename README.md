# 🎵 Music Duplicate Finder & Remover

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Find and remove duplicate music files based on acoustic similarity.**  
Keep the best copy (cover art, metadata, highest quality) while safely deleting (or trashing) the rest.

---

## ✨ Features

- **Audio fingerprinting** – Chromaprint (fpcalc) detects **exact** and **near‑duplicate** songs (live, remastered, different bitrates).
- **Multiple detection strategies** – exact byte‑hash, acoustic similarity, or filename+duration.
- **Smart keep rules** – prefers files with cover art → richer metadata → larger size, all configurable.
- **Safe by default** – `--dry-run` previews everything; `--trash` moves files instead of deleting.
- **Beautiful Web UI** – real‑time progress dashboard powered by Streamlit.
- **Detailed reports** – JSON report of every group, kept file, and removed duplicates.
- **Pluggable & extensible** – modular codebase, easy to add new matching methods or custom scoring.

## 🚀 Quick Start

### 1. Install dependencies
#### System tool for audio fingerprinting
sudo apt install libchromaprint-tools   # Ubuntu/Debian
brew install chromaprint                # macOS
##### Windows: download from https://acoustid.org/chromaprint

#### Python packages
pip install -r requirements.txt
2. Preview duplicates (safe)
bash
python -m music_dedup.cli /path/to/music --dry-run
3. Launch the Web UI
bash
streamlit run music_dedup/web/streamlit_app.py
4. Actually remove duplicates
bash
python -m music_dedup.cli /path/to/music
Or use the web interface to review and delete interactively.

📋 CLI Usage Examples
Command	Description
cli.py ~/Music --dry-run	Preview what would be deleted
cli.py ~/Music --threshold 0.75 --dry-run	Catch live versions (lower threshold)
cli.py ~/Music --trash ./Trash	Move duplicates to a Trash folder
cli.py ~/Music --keep-path FLAC	Always keep files in a FLAC folder
cli.py ~/Music --show-all-pairs	Print every file pair & similarity score
Full help: python -m music_dedup.cli --help

🧠 How It Works
Collect – Walk directory, filter by extension/size/duration.

Fingerprint – Run fpcalc -raw to get a vector of 32‑bit integers.

Compare – Hamming distance between vectors → similarity score (0–1).

Group – Union‑find clustering with a tunable threshold.

Score & Keep – Rank files per group: cover art → metadata tags → file size.

Act – Delete or move the lower‑scoring duplicates.

🧰 Project Structure
text
music_dedup/
├── core/               # Business logic
├── utils/              # Helpers
├── web/                # Streamlit frontend
├── cli.py              # Command‑line entry
├── requirements.txt
└── README.md
🤝 Contributing
Contributions welcome! You can:

Add new matching methods (key/BPM, DTW).

Improve the Web UI with React.

Write unit tests.

Package as a PyPI package.

📄 License
MIT © [Alireza Paksaz]


All files are ready to be placed in the project tree. To run the CLI, use `python -m music_dedup.cli <args>` from the parent directory. The Streamlit app is launched with `streamlit run music_dedup/web/streamlit_app.py`. Enjoy your beautifully architected music deduplicator!

