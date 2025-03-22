#!/bin/bash
set -euo pipefail

FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
LOCAL_BIN_DIR="/usr/local/bin/"
CACHE_DIR="/var/cache/ffmpeg"
CACHED_FFMPEG="${CACHE_DIR}/ffmpeg"
CACHED_TARBALL="${CACHE_DIR}/ffmpeg.tar.xz"

mkdir -p "${CACHE_DIR}"

# Check if we already have FFmpeg in cache
if [ -f "${CACHED_FFMPEG}" ]; then
    echo "Using cached FFmpeg binary..."
    cp "${CACHED_FFMPEG}" "${LOCAL_BIN_DIR}/ffmpeg"
    chmod +x "${LOCAL_BIN_DIR}/ffmpeg"
else
    echo "Downloading FFmpeg..."
    if ! wget -q "${FFMPEG_URL}" -O "${CACHED_TARBALL}"; then
        echo "Failed to download FFmpeg tarball"
        exit 1
    fi

    # Extract the tarball
    mkdir -p ffmpeg
    tar -xf "${CACHED_TARBALL}" -C ffmpeg --strip-components=1

    # Cache the binary
    cp ffmpeg/bin/ffmpeg "${CACHED_FFMPEG}"
    
    # Move the binary to /usr/local/bin
    mv ffmpeg/bin/ffmpeg "${LOCAL_BIN_DIR}"

    # Make the binary executable
    chmod +x "${LOCAL_BIN_DIR}/ffmpeg"
fi

# Verify installation
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "FFmpeg installation failed"
    exit 1
fi

echo "FFmpeg installed successfully."

# Run the command passed to the entrypoint
exec "$@"