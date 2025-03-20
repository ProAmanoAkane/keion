#!/bin/bash
set -euo pipefail

# Download FFmpeg binary directly
FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/2024-02-28-git-61845112/ffmpeg-master-latest-linux64-gpl-61845112"
FFMPEG_BIN="/usr/local/bin/ffmpeg"

if ! curl -sSL "${FFMPEG_URL}" -o "${FFMPEG_BIN}"; then
    echo "Failed to download FFmpeg"
    exit 1
fi

# Make the binary executable
chmod +x "${FFMPEG_BIN}"

# Verify installation
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "FFmpeg installation failed"
    exit 1
fi

echo "FFmpeg installed successfully."

# Execute the application
exec "$@"