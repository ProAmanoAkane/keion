# Keion Discord Music Bot

A Discord music bot built with discord.py that plays music from YouTube in voice channels.

## Features

- Play music from YouTube URLs or search queries
- Queue system with loop functionality (queue/song)
- Basic playback controls (play, pause, resume, skip, stop)
- Volume control
- Queue management

## Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose
- Poetry (for development)

## Setup

1. **Clone the repository and navigate to the project directory**

2. **Configure the bot token**

   Copy the example environment file and add your Discord bot token:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Discord bot token:
   ```
   DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
   ```

3. **Running with Docker Compose**

   Build and start the bot:
   ```bash
   docker compose up --build
   ```

   To run in detached mode:
   ```bash
   docker compose up -d
   ```

## Development Setup

1. **Install Poetry**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Run the bot**
   ```bash
    docker compose up -d
   ```

## Bot Commands

- `/play <url/query>` - Play a song from YouTube
- `/pause` - Pause the current song
- `/resume` - Resume playback
- `/skip` - Skip the current song
- `/stop` - Stop playback and leave the voice channel
- `/queue` - Show the current queue
- `/loop [queue/song]` - Toggle loop mode for queue or current song

## Project Structure

```
keion/
├── src/
│   ├── keion/
│   │   ├── __init__.py      # Bot initialization
│   │   └── music_cog.py     # Music player implementation
│   └── main.py              # Entry point
├── docker-compose.yaml
├── Dockerfile
├── entrypoint.sh
├── pyproject.toml
└── poetry.lock
```

## Technical Details

- Built with discord.py 2.5+
- Uses yt-dlp for YouTube integration
- FFmpeg for audio processing
- Docker multi-stage build for optimized container size
- Poetry for dependency management

## License

This project is open source and available under the MIT License.