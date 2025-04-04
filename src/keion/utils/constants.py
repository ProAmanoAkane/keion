"""Constants used throughout the application."""

# HTTP Status Codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401

# Playlist Display
MAX_PLAYLIST_DISPLAY = 10

# FFmpeg Settings
FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 -reconnect_streamed 1 "
    "-reconnect_delay_max 5 -thread_queue_size 4096"
)
FFMPEG_OPTIONS = (
    "-vn -c:a libopus -b:a 96k -bufsize 64k " "-threads 2 -application lowdelay"
)
