import asyncio
import re
from io import StringIO

import aiohttp
import discord
import yt_dlp
from discord.ext import commands
from loguru import logger

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}

# add option for playing youtube playlists
# add to playlist with another thre
# next/prev in song and head/teil in playlist maybe use Optional or Union
# add error handling


class Song:
    def __init__(self, title=None, url=None, duration=None):
        self.title = title
        self.url = url
        self.duration = duration
        self.next = None
        self.prev = None


class Playlist:
    """
    A doubly linked list implementation to store and manage a playlist of songs.

    Attributes:
    head (Song): The first song in the playlist.
    tail (Song): The last song in the playlist.
    size (int): The number of songs in the playlist.

    Methods:
    push_song(self, song): Adds a song to the beginning of the playlist.
    append_song(self, song): Adds a song to the end of the playlist.
    next_song(self): Returns the URL of the next song in the playlist.
    previous_song(self): Returns the URL of the previous song in the playlist.
    print_playlist(self): Returns a string representation of the playlist.
    """

    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        logger.debug("initializing playlist")

    def push_song(self, song):
        """
        Adds a song to the beginning of the playlist.

        Parameters:
        song (Song): The song to be added.
        """
        song.next = self.head
        if self.head is not None:
            self.head.prev = song
        self.head = song
        self.size += 1
        logger.debug("Song pushed")

    def append_song(self, song):
        """
        Adds a song to the end of the playlist.

        Parameters:
        song (Song): The song to be added.
        """
        song.next = None
        if self.head is None:
            song.prev = None
            self.head = song
            logger.debug("Add first song to playlist")
            self.size = 1
            return
        last = self.head
        while last.next is not None:
            last = last.next
        last.next = song
        song.prev = last
        self.size += 1
        logger.debug("Add song to playlist")

    def next_song(self):
        """
        Returns the URL of the next song in the playlist.

        Returns:
        str: The URL of the next song in the playlist.
        """
        if self.head.next is None:
            logger.debug("There is no next song in the playlist")
            return None
        self.head = self.head.next
        logger.debug("Changin head to next song in the playlist")
        return self.head.url

    def previous_song(self):
        """
        Returns the URL of the previous song in the playlist.

        Returns:
        str: The URL of the previous song in the playlist.
        """
        if self.head.prev is None:
            logger.debug("Thre is no previous song in the playlist")
            return None
        self.head = self.head.prev
        logger.debug("Changin head to previous song in the playlist")
        return self.head.url

    def print_playlist(self):
        """
        Returns a string representation of the playlist.

        Returns:
        str: A string representation of the playlist.
        """
        ss = StringIO()
        ss.write("\tPlaylist:\n")
        while self.head is not None:
            ss.write(f"{self.head.title}\n")
            last = self.head
            self.head = self.head.next
        return ss.getvalue()


class Youtube_downloader:

    def __init__(self):
        self.downloader = yt_dlp.YoutubeDL(YDL_OPTIONS)
        logger.debug('init downloader')

    def is_youtube_url(self, url: str):
        return re.search(r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|\?v=)([^#\&\?]*).*", url)

    async def is_valid_youtube_url(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                text = await response.text()
                is_valid = not ("Video unavailable" in text)
                return is_valid

    def is_valid_url(self, url):
        if self.is_youtube_url(url) and asyncio.create_task(self.is_valid_youtube_url(url)):
            return True
        return False

    def create_song(self, url):
        try:
            song_info = self.downloader.extract_info(url, download=False)
        except Exception as e:
            logger.error(f"Can't extract info from {url}\n {e}")
            return None
        new_song = Song()
        new_song.title = song_info.get('title')
        new_song.url = song_info.get('url')
        new_song.duration = song_info.get('duration')
        logger.debug(f'New song: {new_song.title} with duration: {new_song.duration} are created')
        return new_song


class Music_player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.playlist = None
        self.audio_source = None
        self.is_loop = False
        self.downloader = Youtube_downloader()

    def resetting(self):
        self.is_loop = False
        self.playlist = None
        self.audio_source.cleanup()
        self.audio_source = None
        logger.debug("")

    async def exit(self, ctx):
        self.resetting()
        logger.debug("It's time to stop.")
        await ctx.send("My job here is done!")
        await ctx.guild.voice_client.disconnect()
        logger.debug("Disconnected from voice client")

    async def add_song_to_playlist(self, ctx, url):
        """
        Adds a song to the music player's playlist.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
            url (str): The URL of the song to be added.

        Returns:
            bool: Returns True if the song was successfully added to the playlist. Returns False otherwise.

        """

        # Create a song object from the given URL
        song = self.downloader.create_song(url)

        # If the song object is not None, append it to the playlist
        if song is not None:
            self.playlist.append_song(song)
            await ctx.send(f"Added {song.title} to the playlist.")
            return True

        # If the song object is None, return False
        return False

    async def play_song(self, ctx, song):
        logger.debug("Trying to play song")
        await ctx.send(f"Now playing: {self.playlist.head.title}")
        self.audio_source = discord.FFmpegPCMAudio(
            song,
            **FFMPEG_OPTIONS
        )
        ctx.voice_client.play(self.audio_source, after=lambda e: self.play_next_song(ctx))
        logger.debug("Audio stream started")

    def play_next_song(self, ctx):
        if self.playlist is None:
            return
        logger.debug("Changing song: check if loop state is active")
        if self.is_loop:
            logger.debug("loop state is active, playing same song")
            self.bot.loop.create_task(self.play_song(ctx, self.playlist.head.url))
        elif self.playlist.next_song() is not None:
            logger.debug("no loop state, changing song")
            self.bot.loop.create_task(self.play_song(ctx, self.playlist.head.url))
        else:
            self.bot.loop.create_task(self.exit(ctx))

    @commands.command()
    async def play(self, ctx, url):
        logger.debug(f"!play command is executing by {ctx.author}")

        if not self.downloader.is_valid_url(url):
            return await ctx.send("Invalid URL")

        author_voice_client = ctx.author.voice
        bot_voice_clients = self.bot.voice_clients

        if not author_voice_client:
            logger.debug(f"can't execute command, {ctx.author} not in a voice channel")
            return await ctx.send("You must be in a voice channel to play music.")

        if bot_voice_clients and author_voice_client.channel != bot_voice_clients[0].channel:
            logger.debug(f"can't execute command, bot is already playing in different channel")
            return await ctx.send("Bot is already playing music in another channel.")

        if ctx.guild.voice_client:  # if already connected to a voice channel, add song to playlist
            if not await self.add_song_to_playlist(ctx, url):
                return await ctx.send("Can't add song to playlist, please check your url")
        else:  # connect to voice channel and start playing first song
            self.playlist = Playlist()
            if not await self.add_song_to_playlist(ctx, url):
                return await ctx.send("Can't add song to playlist, please check your url")
            await author_voice_client.channel.connect()
            await self.play_song(ctx, self.playlist.head.url)

    @commands.command()
    async def loop(self, ctx):
        logger.debug(f"!loop command is executing by {ctx.author}")
        self.is_loop = not self.is_loop
        if self.is_loop:
            logger.debug("Loop state: ON")
            await ctx.send("Music is now looping. To disable loop mode, send '!loop'")
        else:
            logger.debug("Loop state: OFF")
            await ctx.send("Music is no longer looping.")

    @commands.command()
    async def skip(self, ctx):
        logger.debug(f"!skip command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't skip, not in voice channel")
            return await ctx.send("I'm not in a voice channel.")

        if self.is_loop:
            logger.debug("can't skip in loop state")
            return await ctx.send("Can't skip in loop state.")

        song = self.playlist.next_song()

        if not song:
            logger.debug("can't skip, there are no next songs")
            return await ctx.send("No next song.")

        logger.debug('cleaning up audio source')
        voice_client.pause()
        self.audio_source.cleanup()
        await self.play_song(ctx, song)

    @commands.command()
    async def prev(self, ctx):
        logger.debug(f"!prev command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't prev, not in voice channel")
            return await ctx.send("I'm not in a voice channel.")

        if self.is_loop:
            logger.debug("can't prev in loop state")
            return await ctx.send("Can't prev in loop state.")

        song = self.playlist.previous_song()

        if not song:
            logger.debug("can't prev, there are no previous songs")
            return await ctx.send("No previous song.")

        ctx.voice_client.pause()
        self.audio_source.cleanup()
        await self.play_song(ctx, song)

    @commands.command()
    async def pause(self, ctx):
        logger.debug(f"!pause command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client or not voice_client.is_playing():
            logger.debug("can't pause")
            return await ctx.send("I'm not currently playing any audio.")

        voice_client.pause()
        logger.debug("audio source paused")

    @commands.command()
    async def resume(self, ctx):
        logger.debug(f"!resume command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client or not voice_client.is_paused():
            logger.debug("can't resume")
            return await ctx.send("I'm not currently paused.")

        voice_client.resume()
        logger.debug("audio source resumed")

    @commands.command()
    async def playlist(self, ctx):
        logger.debug(f"!playlist command is executing by {ctx.author}")
        await ctx.send(self.playlist.print_playlist())

    @commands.command()
    async def stop(self, ctx):
        logger.debug(f"!stop command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if voice_client:
            logger.debug("cleaning up")
            await self.exit(ctx)
        else:
            await ctx.send("I'm not currently in a voice channel.")


async def setup(bot):
    await bot.add_cog(Music_player(bot))
