import queue
import threading

import discord
from loguru import logger

from playlist_manager import Playlist_manager
from song import Song

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
guild_controller = {}


class Audio_controller():
    """
    This is a Python class called Audio_controller() that appears to be part of a music player bot for Discord. Let's go through the methods and attributes of this class:

    Attributes:
        bot: A Discord bot object.
        playlist: A playlist object that stores the list of songs to be played.
        audio_source: An audio source object that represents the current playing song.
        is_loop: A boolean flag that indicates whether the playlist is set to loop or not.
        playlist_manager: A Playlist_manager object that manage adding song to the playlist

    Methods:
        init(self, bot): Constructor method that initializes the object with the bot object and sets other attributes to default values.
        _resetting(self): Resets the playlist and audio_source attributes and sets is_loop to False.
        exit(self, ctx): Resets the attributes, sends a message to the Discord server, and disconnects the bot from the voice client.
    #add_to_playlist(self, ctx, url): Adds a song or playlist to the playlist object by calling either add_playlist_to_playlist() or add_song_to_playlist() methods depending on the URL provided.
    #add_playlist_to_playlist(self, ctx, url: str): Gets all the songs in a YouTube playlist and adds them to the playlist object.
    #add_song_to_playlist(self, ctx, url: str): Gets a single song from YouTube and adds it to the playlist object.
        play_song(self, ctx, song): Plays the song by setting up an audio stream and playing it through the voice client.
        play_next_song(self, ctx): Changes the current playing song to the next song in the playlist if there is one. If there is no next song and is_loop is False, it exits the bot by calling the exit() method. If is_loop is True, it starts playing the same song again.
    """

    def __init__(self, bot):
        """
        Initializes the Audio_controller class.

        Parameters:
            bot (discord.ext.commands.Bot): The bot instance.
        """
        self.bot = bot
        self.playlist = None
        self.audio_source = None
        self.is_loop = False
        self.playlist_manager = Playlist_manager()

    def _resetting(self):
        """
        Resets the music player to its default state.
        """
        self.is_loop = False
        self.playlist_manager.time_to_shutdown = True
        self.playlist = None
        self.audio_source.cleanup()
        self.audio_source = None

    async def exit(self, ctx):
        """
        Stops the music player and disconnects it from the voice channel.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
        """
        self._resetting()
        logger.debug("It's time to stop.")
        await ctx.send("My job here is done!")
        await ctx.guild.voice_client.disconnect()
        logger.debug("Disconnected from voice client")

    async def add_to_playlist(self, ctx, url: str):
        """
        Adds a song or playlist to the MusicPlayer instance's playlist.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
            url (str): The URL of the song or playlist to be added.
        """
        if "list" in url:
            await ctx.send("Adding playlist, it may take some time")
            if not await self._add_playlist_to_playlist(ctx, url):
                return await ctx.send("Can't add playlist, something went wrong :(")
        else:
            if not await self._add_song_to_playlist(ctx, url):
                return await ctx.send("Can't add song to playlist, please check your url")

    async def _add_playlist_to_playlist(self, ctx, url: str):
        """
        Adds a playlist to the Audio_controller instance's playlist.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
            url (str): The URL of the playlist to be added.

        Returns:
            bool: Returns True if the playlist was successfully added to the MusicPlayer instance's playlist. Returns False otherwise.
        """
        logger.debug("Add playlist")
        try:
            await self.playlist_manager.add_playlist(url, self.playlist)
        except Exception as e:
            logger.error(f"Can't add playlist to {url}\n {e}")
            return False
        return True

    async def _add_song_to_playlist(self, ctx, url: str):

        try:
            await self.playlist_manager.add_song(url, self.playlist)
        except Exception as e:
            logger.error(f"Can't add song {url}\n {e}")
            return False
        return True

    async def play_song(self, ctx, song: Song):
        """
        Plays a song.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
            song (str): The song to be played.
        """
        logger.debug("Trying to play song")
        await ctx.send(f"Now playing: {song.title}")
        self.audio_source = discord.FFmpegPCMAudio(
            song.url,
            **FFMPEG_OPTIONS
        )
        ctx.voice_client.play(self.audio_source, after=lambda e: self.play_next_song(ctx))
        logger.debug("Audio stream started")

    def play_next_song(self, ctx):
        """
        Plays the next song in the playlist.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
        """
        if self.playlist is None:
            return
        logger.debug("Changing song: check if loop state is active")
        if self.is_loop:
            logger.debug("loop state is active, playing same song")
            self.bot.loop.create_task(self.play_song(ctx, self.playlist.head))
        elif self.playlist.next_song() is not None:
            logger.debug("no loop state, changing song")
            self.bot.loop.create_task(self.play_song(ctx, self.playlist.head))
        else:
            self.bot.loop.create_task(self.exit(ctx))
