# Keion Discord Music Bot 🎸🍰

Hey there! 👋 Welcome to the Keion Discord Music Bot, your personal Yui Hirasawa (from K-On!) inspired companion for bringing music and fun to your Discord server! This bot strums its way into voice channels to play your favorite tunes from YouTube, all while keeping the spirit of the Light Music Club alive!

## Features ✨

-   Plays music from YouTube URLs or search queries (just like finding the perfect guitar riff!)
-   Manages a queue system with loop functionality (for those songs you just can't get enough of!)
-   Offers basic playback controls: play, pause, resume, skip, stop (because even Yui needs to control the music sometimes!)
-   Includes volume control (gotta make sure everyone can hear Giita!)
-   Handles queue management (organizing songs is almost as important as cake!)

## Prerequisites 📝

Before we get started, make sure you have these installed:

-   Python 3.12 or higher (gotta have the right tools!)
-   Docker and Docker Compose (for easy deployment!)
-   Poetry (for managing dependencies like a pro!)

## Setup 🚀

Let's get this show on the road!

1.  **Clone the repository and navigate to the project directory**

    ```bash
    git clone [repository URL]
    cd keion
    ```

2.  **Configure the bot token**

    Grab your Discord bot token and add it to the `.env` file:

    ```bash
    cp .env.example .env
    ```

    Edit `.env` and add your Discord bot token:

    ```
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
    ```

3.  **Running with Docker Compose**

    Build and start the bot with a single command:

    ```bash
    docker compose up --build
    ```

    To run in detached mode (so it keeps playing even when you close the terminal!):

    ```bash
    docker compose up -d
    ```

## Development - Let's Jam! 🎶

Want to contribute or tweak the bot? Awesome! Here's how to get started:

1.  **Install Poetry**

    If you don't have Poetry yet, get it here:

    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

2.  **Install dependencies**

    Use Poetry to install all the required packages:

    ```bash
    poetry install
    ```

3.  **Run the bot**

    Now you're ready to launch the bot!

    ```bash
    poetry run python src/main.py
    ```

## Bot Commands 🎤

Here's a list of commands you can use with the bot (prefix can be either `!` or `/`):

-   `play <url/query>` - Play a song from YouTube or Spotify (let's find some awesome tunes!)
-   `pause` - Pause the current song (time for a tea break!)
-   `resume` - Resume playback (back to the music!)
-   `skip` - Skip the current song (not feeling this one? No problem!)
-   `stop` - Stop playback and clear the queue (time for a break!)
-   `queue` - Show the current queue and loop status (what's coming up next?)
-   `loop [queue/song]` - Toggle loop mode for queue or current song (repeat after me!)

## Project Structure 🏗️

```
keion/
├── src/
│   ├── main.py              # Entry point
│   └── keion/
│       ├── __init__.py      # Bot initialization
│       ├── cogs/
│       │   ├── __init__.py
│       │   └── music/       # Music functionality
│       │       ├── __init__.py
│       │       ├── cog.py
│       │       ├── player_manager.py
│       │       ├── playlist_manager.py
│       │       └── voice_manager.py
│       ├── resources/
│       │   └── messages.json # Bot messages and responses
│       └── utils/
│           ├── __init__.py
│           ├── audio.py     # Audio processing utilities
│           ├── cache.py     # Caching system
│           ├── embed.py     # Discord embed builders
│           ├── logging.py   # Logging configuration
│           └── spotify_client.py  # Spotify integration
```

## Technical Details

- Built with discord.py 2.5+
- Uses yt-dlp for YouTube integration
- Spotify integration for playing tracks from Spotify links
- Smart voice channel management with auto-disconnect
- Queue and song loop functionality
- FFmpeg for audio processing
- Docker multi-stage build for optimized container size
- Poetry for dependency management
- Custom caching system for improved performance

## License

This project is open source and available under the MIT License.