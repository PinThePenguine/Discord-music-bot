import queue
import threading

import discord
from discord.ext import commands
from loguru import logger

import config
from downloader import Youtube_downloader
from playlist_manager import Playlist_manager
from song import Song

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
guild_controller = {}


class Audio_controller():

    def __init__(self, bot):
     
        self.bot = bot
        self.playlist = None
        self.audio_source = None
        self.is_loop = False
        self.playlist_manager = Playlist_manager()
        self.view = AudioPlayerView(bot, self)
        self.message = None

    def _resetting(self):
        """
        Resets the music player to its default state.
        """
        self.is_loop = False
        self.playlist_manager.time_to_shutdown = True
        self.playlist = None
        self.audio_source.cleanup()
        self.audio_source = None
        self.message = None
        self.playlist_manager = Playlist_manager()
        self.view = AudioPlayerView(self.bot, self)

    async def exit(self, ctx):
        """
        Stops the music player and disconnects it from the voice channel.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
        """
        try:
            await self.message.delete()
        except discord.NotFound:
            logger.warning(f"Failed to delete message, message not found")

        self._resetting()
        await ctx.channel.send("My job here is done!")
        await ctx.guild.voice_client.disconnect()
        logger.debug("Disconnected from voice client")

    async def add_to_playlist(self, ctx, url: str):
        """
        Adds a song or playlist to the MusicPlayer instance's playlist.

        Parameters:
            ctx (discord.ext.commands.Context): The context of the command.
            url (str): The URL of the song or playlist to be added.
        """
        media_type = Youtube_downloader.get_youtube_media_type(url)
        match media_type:
            case "playlist":
                normalized_url = Youtube_downloader.normalize_youtube_playlist_url(url)
                await ctx.channel.send("Adding playlist, it may take some time")
                if not await self._add_playlist_to_playlist(ctx, normalized_url):
                    await ctx.channel.send("Can't add playlist, error in add_to_playlist method")
                    return False
            case "video":
                normalized_url = Youtube_downloader.normalize_youtube_video_url(url)
                if not await self._add_song_to_playlist(ctx, normalized_url):
                    await ctx.channel.send(f"Can't add {media_type} to playlist, please check your url")
                    return False
            case _:
                if not await self._add_song_to_playlist(ctx, url):
                    await ctx.channel.send(f"Can't add {media_type} to playlist, please check your url")
                    return False
        return True

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

        if not self.message:
            if config.AUDIOPLAYER_UI:
                self.message = await ctx.channel.send(f"Now playing: {song.title}", view=self.view)
            else:
                self.message = await ctx.channel.send(f"Now playing: {song.title}")
        else:
            await self.message.edit(content=f"Now playing: {song.title}")

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

    async def loop(self, ctx):
        self.is_loop = not self.is_loop

        if config.AUDIOPLAYER_UI:
            await self.view.update_view(ctx)

    async def skip(self, ctx):
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't skip, not in voice channel")
            await ctx.channel.send("I'm not in a voice channel.")
            return False

        song = self.playlist.next_song()
        if not song:
            logger.debug("can't skip, there are no next songs")
            await ctx.channel.send("No next song.")
            return False

        logger.debug('cleaning up audio source')
        voice_client.pause()
        self.audio_source.cleanup()
        await self.play_song(ctx, song)

        if config.AUDIOPLAYER_UI:
            await self.view.update_view(ctx)

        return True

    async def prev(self, ctx):
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't prev, not in voice channel")
            await ctx.channel.send("I'm not in a voice channel.")
            return False

        song = self.playlist.previous_song()
        if not song:
            logger.debug("can't prev, there are no previous songs")
            await ctx.channel.send("No previous song.")
            return False

        voice_client.pause()
        self.audio_source.cleanup()
        await self.play_song(ctx, song)

        if config.AUDIOPLAYER_UI:
            await self.view.update_view(ctx)

        return True

    async def pause(self, ctx):
        voice_client = ctx.voice_client

        if not voice_client or not voice_client.is_playing():
            logger.debug("can't pause")
            await ctx.channel.send("I'm not currently playing any audio.")
            return False

        voice_client.pause()

        if config.AUDIOPLAYER_UI:
            await self.view.update_view(ctx)

        logger.debug("audio source paused")
        return True

    async def resume(self, ctx):
        voice_client = ctx.voice_client

        if not voice_client or not voice_client.is_paused():
            logger.debug("can't resume")
            await ctx.channel.send("I'm not currently paused.")
            return False

        voice_client.resume()

        if config.AUDIOPLAYER_UI:
            await self.view.update_view(ctx)

        logger.debug("audio source resumed")
        return True

    async def stop(self, ctx):
        voice_client = ctx.voice_client

        if voice_client:
            logger.debug("cleaning up")
            await self.exit(ctx)
        else:
            await ctx.channel.send("I'm not currently in a voice channel.")

    async def get_playlist(self, ctx):
        await ctx.channel.send(self.playlist.print_playlist())

    async def on_message(self, message):
        """
        Method called when the bot receives a message.
        """

        if not self.message:
            return

        if message.content == self.message.content:
            return

        try:
            output_message = self.message.content
            await self.message.delete()
        except discord.NotFound:
            logger.warning(f"Failed to delete message, message not found")

        if config.AUDIOPLAYER_UI:
            self.message = await message.channel.send(output_message, view=self.view)
        else:
            self.message = await message.channel.send(output_message)


class AudioPlayerView(discord.ui.View):

    def __init__(self, bot, controller):
        super().__init__(timeout=None)
        self.bot = bot
        self.controller = controller

    async def update_view(self, ctx):
        playpause_button = self.children[1]  # access playpause_button through self

        if ctx.voice_client.is_playing():
            playpause_button.label = config.BUTTON_PAUSE_SYMBOL
        else:
            playpause_button.label = config.BUTTON_PLAY_SYMBOL

        loop_button = self.children[3]  # access loop_button through self

        if self.controller.is_loop:
            loop_button.style = discord.ButtonStyle.success
        else:
            loop_button.style = discord.ButtonStyle.gray

        await self.controller.message.edit(view=self)

    @discord.ui.button(label=config.BUTTON_PREV_SYMBOL, style=discord.ButtonStyle.blurple)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        await self.controller.prev(ctx)
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(label=config.BUTTON_PAUSE_SYMBOL, style=discord.ButtonStyle.blurple)
    async def playpause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)

        if button.label == config.BUTTON_PAUSE_SYMBOL:
            await self.controller.pause(ctx)
        else:
            await self.controller.resume(ctx)

        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(label=config.BUTTON_SKIP_SYMBOL, style=discord.ButtonStyle.blurple)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        await self.controller.skip(ctx)
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(label=config.BUTTON_LOOP_SYMBOL, style=discord.ButtonStyle.gray)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        await self.controller.loop(ctx)
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(label=config.BUTTON_KILL_SYMBOL, style=discord.ButtonStyle.danger)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        await self.controller.exit(ctx)
        await interaction.response.defer(ephemeral=True)
