"""API routes for Keion web interface."""

from datetime import UTC, datetime
from typing import Any

# FastAPI Imports
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response

# discord.py Imports (assuming available)
# Make sure discord.py is installed in the same environment
try:
    from discord import Colour, Embed
except ImportError:
    # Define dummy classes if discord.py is not available in this specific context
    # This might happen if running the web server separately without the bot's venv
    # For full functionality, ensure discord.py is available.
    print("Warning: discord.py not found. Embed sending will be skipped.")
    Embed = None
    Colour = None

# Project Imports
from ...cogs.music import MusicCog  # Adjust path as needed
from ...utils.cache import TimeCache  # Adjust path as needed

router = APIRouter()
stats_cache = TimeCache(ttl=30)  # Cache stats for 30 seconds


@router.get("/stats")
async def get_stats_api(
    request: Request,
) -> dict[str, Any]:  # Renamed to avoid conflict with utils.get_stats
    """Get bot statistics (API Endpoint)."""
    # Try to get from cache first
    if cached_stats := stats_cache.get("bot_stats"):
        return cached_stats

    # Get bot and cog instances from app state
    bot = request.app.state.bot
    music_cog: MusicCog = bot.get_cog("MusicCog")

    if not music_cog:
        # Handle case where cog might not be loaded
        raise HTTPException(status_code=503, detail="Music Cog not loaded.")

    # Calculate uptime using start_time (falls back to current time if not set)
    start_time = getattr(bot, "start_time", datetime.now(UTC))
    uptime_seconds = (datetime.now(UTC) - start_time).total_seconds()

    # --- Uptime formatting ---
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    if hours > 0:
        uptime_str = f"{hours}h {minutes}m"
    else:
        uptime_str = f"{minutes}m"
    # --- End uptime formatting ---

    stats = {
        "servers": len(bot.guilds),
        "active_voice": len(music_cog.voice_manager.voice_clients),
        "total_songs": len(
            music_cog.playlist_manager.playlist
        ),  # Assuming global playlist length? Or should be per-player?
        "uptime": uptime_str,
    }

    stats_cache.set("bot_stats", stats)
    return stats


@router.get("/players")
async def get_players_api(
    request: Request,
) -> list[dict[str, Any]]:  # Renamed to avoid conflict
    """Get all active music players (API Endpoint)."""
    bot = request.app.state.bot
    music_cog: MusicCog = bot.get_cog("MusicCog")

    if not music_cog:
        raise HTTPException(status_code=503, detail="Music Cog not loaded.")

    players_data = []
    for guild_id, voice_client in music_cog.voice_manager.voice_clients.items():
        guild = bot.get_guild(guild_id)
        if guild and voice_client.is_connected():
            current_song = (
                music_cog.playlist_manager.current_song
            )  # Adapt if playlist is per-guild
            playlist = list(
                music_cog.playlist_manager.playlist
            )  # Adapt if playlist is per-guild

            players_data.append(
                {
                    "guild_name": guild.name,
                    "guild_id": guild_id,
                    "current_song": current_song["title"] if current_song else None,
                    "playlist": playlist,  # Include playlist
                    "queue_length": len(playlist),
                    "is_playing": voice_client.is_playing(),
                    "is_paused": voice_client.is_paused(),
                }
            )
    return players_data


@router.post("/player/{guild_id}/control/{action}")
async def control_player(
    request: Request, guild_id: int, action: str
) -> (
    Response
):  # Return type is Response (can be specific like JSONResponse or just Response)
    """Control a specific player via API and send Discord feedback."""
    valid_actions = {"play", "pause", "skip", "stop"}
    if action not in valid_actions:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Invalid action '{action}' specified."},
        )

    bot = request.app.state.bot
    music_cog: MusicCog = bot.get_cog("MusicCog")

    if not music_cog:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Music Cog not loaded."},
        )

    if guild_id not in music_cog.voice_manager.voice_clients:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "No active player found for this server."},
        )

    voice_client = music_cog.voice_manager.voice_clients[guild_id]
    guild = bot.get_guild(guild_id)

    if not guild:
        # If bot is not in the guild anymore but voice client lingered?
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Bot is not in the specified server."},
        )

    message = ""  # For potential non-error feedback if needed
    embed_description = ""
    success = False  # Flag to track if action was effectively performed

    try:
        if action == "play":
            if voice_client.is_paused():
                voice_client.resume()
                message = "Player resumed."
                embed_description = "▶️ Music playback resumed via web UI."
                success = True
            elif not voice_client.is_playing():
                # Handle case where nothing is playing and queue might be empty
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Nothing to play."},
                )
            else:
                message = "Player is already playing."
                success = True  # Indicate the state matches the request intent

        elif action == "pause":
            if voice_client.is_playing():
                voice_client.pause()
                message = "Player paused."
                embed_description = "⏸️ Music playback paused via web UI."
                success = True
            elif voice_client.is_paused():
                message = "Player is already paused."
                success = True  # State matches request intent
            else:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Player is not playing."},
                )

        elif action == "skip":
            if (
                voice_client.is_playing() or voice_client.is_paused()
            ):  # Allow skipping even if paused
                current_song = (
                    music_cog.playlist_manager.current_song
                )  # Adapt if per-guild
                voice_client.stop()  # Triggers next song potentially
                message = "Skipped to the next song."
                song_title = (
                    f"**{current_song['title']}**"
                    if current_song
                    else "the current song"
                )
                embed_description = f"⏭️ Skipped {song_title} via web UI."
                success = True
            else:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Nothing to skip."},
                )

        elif action == "stop":
            # This usually implies stop playback and disconnect
            # Ensure this matches your cog's stop logic
            await music_cog.voice_manager.disconnect(guild_id)
            # Optionally clear the queue here if that's desired behavior for "stop"
            # music_cog.playlist_manager.clear_queue(guild_id) # If per-guild queue
            message = "Player stopped and disconnected."
            embed_description = "⏹️ Music playback stopped via web UI."
            success = True

        if success:
            # --- Send Discord Embed ---
            if (
                Embed and Colour and guild and embed_description
            ):  # Check if discord.py loaded
                try:
                    cmd_channel = None
                    if hasattr(music_cog, "get_command_channel_for_guild"):
                        cmd_channel_id = music_cog.get_command_channel_for_guild(
                            guild_id
                        )
                        if cmd_channel_id:
                            cmd_channel = guild.get_channel(cmd_channel_id)
                    elif hasattr(
                        music_cog, "guild_settings"
                    ):  # Alternative: check settings object
                        settings = music_cog.guild_settings.get(guild_id)
                        if settings and settings.get("command_channel_id"):
                            cmd_channel = guild.get_channel(
                                settings["command_channel_id"]
                            )

                    if cmd_channel:
                        embed = Embed(
                            description=embed_description, color=Colour.blurple()
                        )  # Use your bot's color
                        await cmd_channel.send(embed=embed)
                    else:
                        print(
                            f"Warning: Could not find command channel for guild {guild_id} to send web UI feedback."
                        )
                except Exception as e:
                    print(
                        f"Error sending Discord message for guild {guild_id}: {e}"
                    )  # Log discord sending errors
            # --- End Discord Embed ---

            # Return No Content on Success
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            # If no specific error was raised but success is false (shouldn't normally happen here)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": message or "Action could not be performed."},
            )

    except Exception as e:
        # Catch potential errors during voice client interaction or Discord sending
        print(
            f"Error controlling player for guild {guild_id} (action: {action}): {e}"
        )  # Log the error server-side
        # Provide a generic error to the user
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"An internal error occurred while trying to '{action}'."
            },
        )


@router.post("/player/add")
async def add_song(
    request: Request, query: str = Form(...), guild_id: int = Form(...)
) -> JSONResponse:  # Added guild_id
    """Add a song to the queue for a specific guild."""
    bot = request.app.state.bot
    music_cog: MusicCog = bot.get_cog("MusicCog")

    if not music_cog:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": "Music Cog not loaded."},
        )

    # Check if the bot is connected in that guild - needed to play immediately
    voice_client = music_cog.voice_manager.voice_clients.get(guild_id)

    try:
        # Get song info (assuming this is async)
        # You might need to pass guild_id if relevant for searching/adding
        info = await music_cog.player_manager.get_music_info(query)

        if not info:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Could not find a song matching the query.",
                },
            )

        # Add to queue (assuming add_to_queue handles guild_id if needed)
        # You might need to adapt this if your playlist is per-guild
        music_cog.playlist_manager.add_to_queue(
            info, guild_id=guild_id
        )  # Pass guild_id if necessary

        response_message = f"Added '{info.get('title', 'song')}' to the queue."
        status_message = "success"

        if (
            voice_client
            and not voice_client.is_playing()
            and not voice_client.is_paused()
        ):
            # Get next song (potentially for this guild_id)
            next_song = music_cog.playlist_manager.get_next_song(
                guild_id=guild_id
            )  # Pass guild_id if necessary
            if next_song:
                await music_cog.player_manager.play_song(guild_id, next_song)
                response_message = f"Playing '{next_song.get('title', 'song')}' now."
            else:
                # Added but couldn't get next song? Should not happen if just added.
                response_message = (
                    f"Added '{info.get('title', 'song')}', but couldn't start playback."
                )

        # Send feedback embed (similar to control_player)
        if Embed and Colour:
            guild = bot.get_guild(guild_id)
            if guild:
                try:
                    cmd_channel = None
                    if hasattr(music_cog, "get_command_channel_for_guild"):
                        cmd_channel_id = music_cog.get_command_channel_for_guild(
                            guild_id
                        )
                        if cmd_channel_id:
                            cmd_channel = guild.get_channel(cmd_channel_id)

                    if cmd_channel:
                        embed = Embed(
                            description=f"🎵 {response_message} (Added via Web UI)",
                            color=Colour.green(),
                        )
                        await cmd_channel.send(embed=embed)
                    else:
                        print(
                            f"Warning: Could not find command channel for guild {guild_id} to send add song feedback."
                        )
                except Exception as e:
                    print(
                        f"Error sending Discord message for guild {guild_id} (add song): {e}"
                    )

        return JSONResponse(
            status_code=200,
            content={"status": status_message, "message": response_message},
        )

    except Exception as e:
        print(
            f"Error adding song (query: {query}, guild: {guild_id}): {e}"
        )  # Log detailed error
        # Provide a user-friendly error
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error adding song: {e}"},
        )
