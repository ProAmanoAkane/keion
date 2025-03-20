# Discord Music Bot Setup

This document outlines the steps to set up the Discord music bot project using Poetry and Docker within a WSL environment on Windows.

## Prerequisites

* **WSL (Windows Subsystem for Linux):** Ensure you have WSL installed and a distribution (e.g., Ubuntu) set up.
* **Docker Desktop for Windows:** Install Docker Desktop for Windows. Make sure Docker is integrated with your WSL distribution.
* **Poetry:** Install Poetry within your WSL distribution. You can follow the official Poetry installation instructions: [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)
* **Python 3.8+:** Ensure you have Python 3.8 or a later version installed in your WSL distribution.
* **Git:** Install git in your WSL distribution.

## Project Setup

1.  **Create Project Directory:**

    ```bash
    mkdir discord-music-bot
    cd discord-music-bot
    ```

2.  **Initialize Poetry:**

    ```bash
    poetry init --name="discord-music-bot" --description="A Discord music bot" --author="Your Name <[email address removed]>" --python="^3.8"
    ```

    Follow the prompts to configure your project.

3.  **Add Dependencies:**

    ```bash
    poetry add discord.py yt-dlp pynacl python-dotenv
    ```

    * `discord.py`: For interacting with the Discord API.
    * `yt-dlp`: For downloading audio from YouTube and other sources.
    * `pynacl`: For voice functionality.
    * `python-dotenv`: For managing environment variables.
    * If you want spotify support, add `spotipy` with `poetry add spotipy`.

4.  **Create `main.py`:**

    Create a `main.py` file in your project directory. This will be the entry point for your bot.

    ```bash
    touch main.py
    ```

5.  **Create `.env` File:**

    Create a `.env` file to store your Discord bot token and other sensitive information.

    ```bash
    touch .env
    ```

    Add your bot token to the `.env` file:

    ```
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
    ```
    If you want to use spotify support, you will need to add your spotify client ID and secret into the .env file.
    ```
    SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET
    ```

6.  **Create `Dockerfile`:**

    Create a `Dockerfile` in your project directory for building the Docker image.

    ```bash
    touch Dockerfile
    ```

    Add the following content to your `Dockerfile`:

    ```dockerfile
    FROM python:3.9-slim-buster

    WORKDIR /app

    COPY poetry.lock pyproject.toml ./

    RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

    COPY . .

    CMD ["python", "main.py"]
    ```

7.  **Create `.dockerignore`:**

    Create a `.dockerignore` file to exclude unnecessary files from the Docker build.

    ```bash
    touch .dockerignore
    ```

    Add the following content to `.dockerignore`:

    ```
    __pycache__
    .venv
    .git
    *.log
    ```

8.  **Create `docker-compose.yml`:**

    Create a `docker-compose.yml` file for defining and running multi-container Docker applications.

    ```bash
    touch docker-compose.yml
    ```

    Add the following content to `docker-compose.yml`:

    ```yaml
    version: "3.8"
    services:
      bot:
        build: .
        volumes:
          - ./.env:/app/.env
        environment:
          - DISCORD_TOKEN=${DISCORD_TOKEN}
          - SPOTIFY_CLIENT_ID=${SPOTIFY_CLIENT_ID}
          - SPOTIFY_CLIENT_SECRET=${SPOTIFY_CLIENT_SECRET}
    ```

9.  **Build and Run with Docker Compose:**

    Before running the docker compose command, you must export the environment variables from the .env file into your shell. You can do this with the following command:

    ```bash
    export $(grep -v '^#' .env | xargs)
    ```

    Then, build and run the Docker container:

    ```bash
    docker-compose up --build
    ```

    This will build the Docker image and start the bot.

## Next Steps

* Start implementing the bot's functionality in `main.py`.
* Add more features and commands as needed.
* Test your bot thoroughly.

This setup provides a solid foundation for your Discord music bot project. Remember to replace `YOUR_DISCORD_BOT_TOKEN`, `YOUR_SPOTIFY_CLIENT_ID`, and `YOUR_SPOTIFY_CLIENT_SECRET` with your actual bot token and spotify credentials.