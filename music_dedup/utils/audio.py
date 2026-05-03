"""
Mutagen wrappers for extracting audio metadata.
"""

from pathlib import Path
try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None
    raise ImportError("mutagen is required. Install with: pip install mutagen")

def get_audio_info(filepath: Path) -> dict:
    """Return dictionary with basic audio info."""
    info = {
        "path": str(filepath),
        "size": filepath.stat().st_size,
        "has_cover": False,
        "tag_count": 0,
        "duration": None,
        "bitrate": None,
    }
    if MutagenFile is None:
        return info
    try:
        audio = MutagenFile(str(filepath), easy=False)
        if audio is None:
            return info
        if hasattr(audio, "info"):
            info["duration"] = getattr(audio.info, "length", None)
            info["bitrate"] = getattr(audio.info, "bitrate", None)
        if audio.tags:
            tags = dict(audio.tags)
            info["tag_count"] = len(tags)
            for k in tags:
                ks = str(k)
                if any(ck in ks for ck in ("APIC", "covr", "METADATA_BLOCK_PICTURE", "WM/Picture")):
                    info["has_cover"] = True
                    break
    except Exception:
        pass
    return info


def fmt_score(info: dict) -> str:
    """Format audio info for display."""
    cover = "🖼  cover" if info["has_cover"] else "   no cover"
    tags = f"{info['tag_count']} tags"
    size = f"{info['size'] / 1024**2:.1f} MB"
    br = f"{info['bitrate']//1000}kbps" if info.get("bitrate") else "?kbps"
    dur = (f"{int(info['duration']//60)}:{int(info['duration']%60):02d}"
           if info.get("duration") else "?:??")
    return f"{cover} | {tags} | {size} | {br} | {dur}"
