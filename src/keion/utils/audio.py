"""Audio processing utilities for the music bot."""

from .constants import FFMPEG_BEFORE_OPTIONS, FFMPEG_OPTIONS

youtube_dl_options: dict[str, str] = {
    "format": "bestaudio[abr<=96]/bestaudio/best",
    "extractaudio": True,
    "audioformat": "opus",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "quiet": True,
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "youtube_include_dash_manifest": False,
    "youtube_include_hls_manifest": False,
}

ffmpeg_opts: dict[str, str] = {
    "before_options": FFMPEG_BEFORE_OPTIONS,
    "options": FFMPEG_OPTIONS,
}
