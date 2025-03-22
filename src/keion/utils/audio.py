"""Audio processing utilities for the music bot."""

from typing import Dict

youtube_dl_options: Dict[str, str] = {
    "format": "bestaudio[abr<=96]/bestaudio/best",
    "extractaudio": True,
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

ffmpeg_opts: Dict[str, str] = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn -c:a libopus -b:a 96k -bufsize 64k",
}