#!/bin/bash
set -euo pipefail

# Create temporary working directory
TEMP_DIR=$(mktemp -d)
cd "${TEMP_DIR}"

# Download FFmpeg build
FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
if ! wget -q "${FFMPEG_URL}"; then
    echo "Failed to download FFmpeg"
    exit 1
fi

# Extract the archive
tar xf ffmpeg-master-latest-linux64-gpl.tar.xz

# Move FFmpeg executable to /usr/local/bin
mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg /usr/local/bin/

# Verify installation
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "FFmpeg installation failed"
    exit 1
fi

# Clean up
cd /
rm -rf "${TEMP_DIR}"