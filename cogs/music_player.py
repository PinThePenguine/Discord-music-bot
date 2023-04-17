import discord
from discord import app_commands
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
        logger.info(f"{config.BOT_PREFIX}play command is executing by {ctx.author}")
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
            if await controller.add_to_playlist(ctx, url):
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
        logger.info(f"{config.BOT_PREFIX}loop command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.loop(ctx)

    @commands.command(name="skip", aliases=['s', 'next'],
                      brief='Play the next song in the playlist.',
                      description=config.SKIP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def skip(self, ctx):
        logger.info(f"{config.BOT_PREFIX}skip command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.skip(ctx)

    @commands.command(name="prev", aliases=['pr', 'last'],
                      brief='Play the previous song in the playlist.',
                      description=config.PREV_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def prev(self, ctx):
        logger.info(f"{config.BOT_PREFIX}prev command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.prev(ctx)

    @commands.command(name="pause", aliases=['ps', 'break'],
                      brief="Pause audio in voice channel",
                      description=config.PAUSE_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def pause(self, ctx):
        logger.info(f"{config.BOT_PREFIX}pause command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.pause(ctx)

    @commands.command(name="resume", aliases=['rs', 'res'],
                      brief="Resume audio in voice channel",
                      description=config.RESUME_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def resume(self, ctx):
        logger.info(f"{config.BOT_PREFIX}resume command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.resume(ctx)

    @commands.command(name="playlist", aliases=['songs', 'songlist', 'list'],
                      brief="Get a list of songs from the playlist",
                      description=config.PLAYLIST_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def playlist(self, ctx):
        logger.info(f"!playlist command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.playlist(ctx)

    @commands.command(name="stop", aliases=['exit', 'quit', 'die', 'kill'],
                      brief="Stop audio and disconnect from voice channel",
                      description=config.STOP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def stop(self, ctx):
        logger.info(f"{config.BOT_PREFIX}stop command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.stop(ctx)


async def setup(bot):
    await bot.add_cog(Music_player(bot))
