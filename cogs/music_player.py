from discord.ext import commands
from loguru import logger

import config
from audio_controller import Audio_controller
from playlist import Playlist


class Music_player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.controller = Audio_controller(bot)

    @commands.command(name="play", aliases=['p', 'song', 'sing', 'add'],
                      brief='Play music in a voice channel.',
                      description=config.PLAY_COMMAND_DESCRIPTION)
    @commands.cooldown(2, 1, commands.BucketType.user)
    @commands.guild_only()
    async def play(self, ctx, url: str = commands.parameter(description="The YouTube video or playlist link that you want to play.")):
        logger.debug(f"!play command is executing by {ctx.author}")

        author_voice_client = ctx.author.voice
        bot_voice_clients = self.bot.voice_clients

        if not author_voice_client:
            logger.debug(f"can't execute command, {ctx.author} not in a voice channel")
            return await ctx.send("You must be in a voice channel to play music.")

        if bot_voice_clients and author_voice_client.channel != bot_voice_clients[0].channel:
            logger.debug(f"can't execute command, bot is already playing in different channel")
            return await ctx.send("Bot is already playing music in another channel.")

        if not self.controller.downloader.is_valid_url(url):
            return await ctx.send("Invalid URL")

        if ctx.guild.voice_client:  # if already connected to a voice channel, add song to playlist
            await self.controller.add_to_playlist(ctx, url)
        else:  # connect to voice channel and start playing first song
            self.controller.playlist = Playlist()
            await self.controller.add_to_playlist(ctx, url)
            await author_voice_client.channel.connect()
            await self.controller.play_song(ctx, self.controller.playlist.head)

    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('You did not provide a required argument. The correct syntax is: >play <youtube_url>')

    @commands.command(name="loop", aliases=['l', 'repeat'],
                      brief='Loop the currently playing song.',
                      description=config.LOOP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def loop(self, ctx):
        logger.debug(f"!loop command is executing by {ctx.author}")
        self.controller.is_loop = not self.controller.is_loop
        if self.controller.is_loop:
            logger.debug("Loop state: ON")
            await ctx.send("Music is now looping. To disable loop mode, send '>loop'")
        else:
            logger.debug("Loop state: OFF")
            await ctx.send("Music is no longer looping.")

    @commands.command(name="skip", aliases=['s', 'next'],
                      brief='Play the next song in the playlist.',
                      description=config.SKIP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def skip(self, ctx):
        logger.debug(f"!skip command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't skip, not in voice channel")
            return await ctx.send("I'm not in a voice channel.")

        if self.controller.is_loop:
            logger.debug("can't skip in loop state")
            return await ctx.send("Can't skip in loop state.")

        song = self.controller.playlist.next_song()

        if not song:
            logger.debug("can't skip, there are no next songs")
            return await ctx.send("No next song.")

        logger.debug('cleaning up audio source')
        voice_client.pause()
        self.controller.audio_source.cleanup()
        await self.controller.play_song(ctx, song)

    @commands.command(name="prev", aliases=['pr', 'last'],
                      brief='Play the previous song in the playlist.',
                      description=config.PREV_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def prev(self, ctx):
        logger.debug(f"!prev command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if not voice_client:
            logger.debug("can't prev, not in voice channel")
            return await ctx.send("I'm not in a voice channel.")

        if self.controller.is_loop:
            logger.debug("can't prev in loop state")
            return await ctx.send("Can't prev in loop state.")

        song = self.controller.playlist.previous_song()

        if not song:
            logger.debug("can't prev, there are no previous songs")
            return await ctx.send("No previous song.")

        ctx.voice_client.pause()
        self.controller.audio_source.cleanup()
        await self.controller.play_song(ctx, song)

    @commands.command(name="pause", aliases=['ps', 'break'],
                      brief="Pause audio in voice channel",
                      description=config.PAUSE_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def pause(self, ctx):
        logger.debug(f"!pause command is executing by {ctx.author}")
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
        logger.debug(f"!resume command is executing by {ctx.author}")
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
        await ctx.send(self.controller.playlist.print_playlist())


    @commands.command(name="stop", aliases=['exit', 'quit', 'die', 'kill'],
                      brief="Stop audio and disconnect from server",
                      description=config.STOP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def stop(self, ctx):
        logger.debug(f"!stop command is executing by {ctx.author}")
        voice_client = ctx.voice_client

        if voice_client:
            logger.debug("cleaning up")
            await self.controller.exit(ctx)
        else:
            await ctx.send("I'm not currently in a voice channel.")


async def setup(bot):
    await bot.add_cog(Music_player(bot))
