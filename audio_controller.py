import queue
import threading

import discord
from loguru import logger

from downloader import Youtube_downloader

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


class Audio_controller():

    def __init__(self, bot):
        self.bot = bot
        self.playlist = None
        self.audio_source = None
        self.is_loop = False
        self.downloader = Youtube_downloader()

    def _resetting(self):
        self.is_loop = False
        self.playlist = None
        self.audio_source.cleanup()
        self.audio_source = None

    async def exit(self, ctx):
        self._resetting()
        logger.debug("It's time to stop.")
        await ctx.send("My job here is done!")
        await ctx.guild.voice_client.disconnect()
        logger.debug("Disconnected from voice client")

    async def add_to_playlist(self, ctx, url):
        if "playlist" in url:
            await ctx.send("Adding playlist, it may take some time")
            if not await self.add_playlist_to_playlist(ctx, url):
                return await ctx.send("Can't add playlist, something went wrong :(")
        else:
            if not await self.add_song_to_playlist(ctx, url):
                return await ctx.send("Can't add song to playlist, please check your url")

    async def add_playlist_to_playlist(self, ctx, url: str):
        logger.debug("Add playlist")
        try:
            result_queue = queue.Queue()
            thread = threading.Thread(target=self.downloader.create_song, args=(url, result_queue, True))
            thread.start()
            thread.join()
            while not result_queue.empty():
                song = result_queue.get()
                self.playlist.append_song(song)
        except Exception as e:
            logger.error(f"Can't add playlist to {url}\n {e}")
            return False
        await ctx.send("Playlist added successfully")
        return True

    async def add_song_to_playlist(self, ctx, url: str):
        """
        Adds a song to the music player's playlist.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
            url (str): The URL of the song to be added.

        Returns:
            bool: Returns True if the song was successfully added to the playlist. Returns False otherwise.

        """

        # Create a song object from the given URL
        result_queue = queue.Queue()
        thread = threading.Thread(target=self.downloader.create_song, args=(url, result_queue))
        thread.start()
        thread.join()
        song = result_queue.get()

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
