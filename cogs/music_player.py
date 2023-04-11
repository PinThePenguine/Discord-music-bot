from discord.ext import commands
from loguru import logger

import config
from audio_controller import Audio_controller, guild_controller
from downloader import Youtube_downloader
from playlist import Playlist


class Music_player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def get_guild_controller(self, ctx):
        current_guild = self.get_guild_player(ctx)
        if current_guild is not None:
            return guild_controller.get(current_guild)
        return None

    def get_guild_player(self, ctx):
        if ctx.guild is not None:
            return ctx.guild
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if ctx.author in channel.members:
                    return guild
        return None

    @commands.command(name="play", aliases=['p', 'song', 'sing', 'add'],
                      brief='Play music in a voice channel.',
                      description=config.PLAY_COMMAND_DESCRIPTION)
    @commands.cooldown(2, 1, commands.BucketType.user)
    @commands.guild_only()
    async def play(self, ctx, url: str = commands.parameter(description="The YouTube video or playlist link that you want to play.")):
        logger.debug(f"{config.BOT_PREFIX}play command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        author_voice_client = ctx.author.voice
        bot_voice_clients = self.bot.voice_clients

        if not author_voice_client:
            logger.debug(f"can't execute command, {ctx.author} not in a voice channel")
            return await ctx.send("You must be in a voice channel to play music.")

        for voice_client in bot_voice_clients:
            if voice_client.guild == ctx.guild and author_voice_client.channel != voice_client.channel:
                logger.debug(f"can't execute command, bot is already playing in different channel")
                return await ctx.send("Bot is already playing music in another channel.")

        if not await Youtube_downloader.is_valid_url(url):
            return await ctx.send("Invalid URL")

        if ctx.guild.voice_client:  # if already connected to a voice channel, add song to playlist
            await controller.add_to_playlist(ctx, url)
        else:  # connect to voice channel and start playing first song
            controller.playlist = Playlist()
            await controller.add_to_playlist(ctx, url)
            await author_voice_client.channel.connect()
            await controller.play_song(ctx, controller.playlist.head)

    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f"You did not provide a required argument. The correct syntax is: {config.BOT_PREFIX}play <youtube_url>")

    @commands.command(name="loop", aliases=['l', 'repeat'],
                      brief='Loop the currently playing song.',
                      description=config.LOOP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def loop(self, ctx):
        logger.debug(f"{config.BOT_PREFIX}loop command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        controller.is_loop = not controller.is_loop
        if controller.is_loop:
            logger.debug("Loop state: ON")
            await ctx.send(f"Music is now looping. To disable loop mode, send '{config.BOT_PREFIX}loop'")
        else:
            logger.debug("Loop state: OFF")
            await ctx.send("Music is no longer looping.")

    @commands.command(name="skip", aliases=['s', 'next'],
                      brief='Play the next song in the playlist.',
                      description=config.SKIP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def skip(self, ctx):
        logger.debug(f"{config.BOT_PREFIX}skip command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't skip, not in voice channel")
            return await ctx.send("I'm not in a voice channel.")

        if controller.is_loop:
            logger.debug("can't skip in loop state")
            return await ctx.send("Can't skip in loop state.")

        song = controller.playlist.next_song()

        if not song:
            logger.debug("can't skip, there are no next songs")
            return await ctx.send("No next song.")

        logger.debug('cleaning up audio source')
        voice_client.pause()
        controller.audio_source.cleanup()
        await controller.play_song(ctx, song)

    @commands.command(name="prev", aliases=['pr', 'last'],
                      brief='Play the previous song in the playlist.',
                      description=config.PREV_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def prev(self, ctx):
        logger.debug(f"{config.BOT_PREFIX}prev command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't prev, not in voice channel")
            return await ctx.send("I'm not in a voice channel.")

        if controller.is_loop:
            logger.debug("can't prev in loop state")
            return await ctx.send("Can't prev in loop state.")

        song = controller.playlist.previous_song()

        if not song:
            logger.debug("can't prev, there are no previous songs")
            return await ctx.send("No previous song.")

        ctx.voice_client.pause()
        controller.audio_source.cleanup()
        await controller.play_song(ctx, song)

    @commands.command(name="pause", aliases=['ps', 'break'],
                      brief="Pause audio in voice channel",
                      description=config.PAUSE_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def pause(self, ctx):
        logger.debug(f"{config.BOT_PREFIX}pause command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client or not voice_client.is_playing():
            logger.debug("can't pause")
            return await ctx.send("I'm not currently playing any audio.")

        voice_client.pause()
        logger.debug("audio source paused")

    @commands.command(name="resume", aliases=['rs', 'res'],
                      brief="Resume audio in voice channel",
                      description=config.RESUME_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def resume(self, ctx):
        logger.debug(f"{config.BOT_PREFIX}resume command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client or not voice_client.is_paused():
            logger.debug("can't resume")
            return await ctx.send("I'm not currently paused.")

        voice_client.resume()
        logger.debug("audio source resumed")

    @commands.command(name="playlist", aliases=['songs', 'songlist', 'list'],
                      brief="Get a list of songs from the playlist",
                      description=config.PLAYLIST_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def playlist(self, ctx):
        logger.debug(f"!playlist command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await ctx.send(controller.playlist.print_playlist())

    @commands.command(name="stop", aliases=['exit', 'quit', 'die', 'kill'],
                      brief="Stop audio and disconnect from server",
                      description=config.STOP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def stop(self, ctx):
        logger.debug(f"{config.BOT_PREFIX}stop command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        voice_client = ctx.voice_client

        if voice_client:
            logger.debug("cleaning up")
            await controller.exit(ctx)
        else:
            await ctx.send("I'm not currently in a voice channel.")


async def setup(bot):
    await bot.add_cog(Music_player(bot))
