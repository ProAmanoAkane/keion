#!/bin/bash
set -euo pipefail

# Download FFmpeg tarball
FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
LOCAL_BIN_DIR="/usr/local/bin/"

if ! wget -q "${FFMPEG_URL}" -O "ffmpeg.tar.xz"; then
    echo "Failed to download FFmpeg tarball"
    exit 1
fi

# Extract the tarball
mkdir -p ffmpeg
tar -xf ffmpeg.tar.xz -C ffmpeg --strip-components=1

# Move the binary to /usr/local/bin
mv ffmpeg/bin/ffmpeg "${LOCAL_BIN_DIR}"

# Make the binary executable
chmod +x "${LOCAL_BIN_DIR}/ffmpeg"

# Verify installation
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "FFmpeg installation failed"
    exit 1
fi

echo "FFmpeg installed successfully."

# Run the command passed to the entrypoint
exec "$@"