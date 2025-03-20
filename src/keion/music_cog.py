import asyncio
import yt_dlp
from discord.ext import commands
from discord.ext.commands import Context
from discord import FFmpegPCMAudio, PCMVolumeTransformer, VoiceClient


youtube_dl_options = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "quiet": True,
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "no_warnings": True,
    "source_address": "0.0.0.0",
}

ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.downloader = yt_dlp.YoutubeDL(youtube_dl_options)
        self.voice_clients: dict[int, VoiceClient] = {}
        self.playlist: list[dict] = []  # Store song info in playlist
        self.loop_queue = False
        self.loop_song = False
        self.current_song = None

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print(f"logged in as {self.bot.user}")

    async def get_music_info(self, query: str) -> dict:
        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, self.downloader.extract_info, query, False)
        except yt_dlp.DownloadError:
            search = await loop.run_in_executor(None, self.downloader.extract_info, f"ytsearch:{query}", False)
            info = search['entries'][0]
        return info

    async def play_song(self, context: Context, song_info: dict) -> None:
        url = song_info['url']
        title = song_info['title']
        webpage_url = song_info['webpage_url']

        audio_stream = PCMVolumeTransformer(FFmpegPCMAudio(url, **ffmpeg_opts), volume=0.5)
        self.current_song = song_info

        self.voice_clients[context.guild.id].play(
            audio_stream,
            after=lambda error: self.play_next(context, error)
        )
        await context.send(f"🎸 Now playing [{title}]({webpage_url})!")

    def play_next(self, context: Context, error: Exception = None) -> None:
        if error:
            print(f"An error occurred while playing the music: {error}")

        if self.loop_song:
            asyncio.run_coroutine_threadsafe(self.play_song(context, self.current_song), self.bot.loop)
            return

        if self.playlist:
            song_info = self.playlist.pop(0)
            asyncio.run_coroutine_threadsafe(self.play_song(context, song_info), self.bot.loop)
        elif self.loop_queue:
            self.playlist = self.playlist_backup.copy()
            self.play_next(context)
        else:
            asyncio.run_coroutine_threadsafe(self.voice_clients[context.guild.id].disconnect(), self.bot.loop)

    @commands.command()
    async def play(self, context: Context, *, query: str) -> None:
        info = await self.get_music_info(query)
        self.playlist.append(info)
        if not self.voice_clients[context.guild.id].is_playing():
            await self.play_song(context, self.playlist.pop(0))
        else:
            await context.send(f"🎸 Added [{info['title']}]({info['webpage_url']}) to the queue!")

    @commands.command()
    async def skip(self, context: Context) -> None:
        if self.voice_clients[context.guild.id].is_playing():
            self.voice_clients[context.guild.id].stop()
            await context.send("Skipped!")
        else:
            await context.send("🎸 No music is currently playing!")

    @commands.command()
    async def pause(self, context: Context) -> None:
        if context.voice_client is not None:
            self.voice_clients[context.guild.id].pause()

    @commands.command()
    async def resume(self, context: Context) -> None:
        if context.voice_client is not None:
            self.voice_clients[context.guild.id].resume()

    @commands.command()
    async def stop(self, context: Context) -> None:
        if context.voice_client is not None:
            await context.voice_client.disconnect()

    @commands.command()
    async def queue(self, context: Context) -> None:
        if not self.playlist:
            await context.send("🎸 The queue is empty.")
            return

        queue_list = "\n".join(f"{i + 1}. [{song['title']}]({song['webpage_url']})" for i, song in enumerate(self.playlist))
        await context.send(f"🎸 **Queue:**\n{queue_list}")

    @commands.command()
    async def loop(self, context: Context, mode: str = "queue") -> None:
        if mode == "queue":
            self.loop_queue = not self.loop_queue
            self.loop_song = False
            await context.send(f"🎸 Queue loop {'enabled' if self.loop_queue else 'disabled'}.")
            self.playlist_backup = self.playlist.copy()
        elif mode == "song":
            self.loop_song = not self.loop_song
            self.loop_queue = False
            await context.send(f"🎸 Song loop {'enabled' if self.loop_song else 'disabled'}.")
        else:
            await context.send("🎸 Invalid loop mode. Use 'queue' or 'song'.")

    @play.before_invoke
    @skip.before_invoke
    @pause.before_invoke
    @resume.before_invoke
    @stop.before_invoke
    @queue.before_invoke
    @loop.before_invoke
    async def ensure_voice(self, context: Context) -> None:
        if context.voice_client is None:
            if context.author.voice:
                self.voice_clients[context.guild.id] = await context.author.voice.channel.connect()
            else:
                await context.send("🎸 You are not connected to a voice channel!")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif self.voice_clients[context.guild.id].channel != context.author.voice.channel:
            await context.send("🎸 You are not in the same voice channel!")
            raise commands.CommandError("Author not in the same voice channel.")