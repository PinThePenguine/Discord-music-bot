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
                      brief='Play music in a voice channel',
                      description=config.PLAY_COMMAND_DESCRIPTION)
    @commands.cooldown(2, 1, commands.BucketType.user)
    @commands.guild_only()
    async def play(self, ctx, url: str = commands.parameter(description="The YouTube video or playlist link that you want to play.")):
        logger.info(f"{config.BOT_PREFIX}play command is executing by {ctx.author}\nurl = {url}")
        controller = self.get_guild_controller(ctx)
        author_voice_client = ctx.author.voice
        bot_voice_clients = self.bot.voice_clients

        if not author_voice_client:
            logger.debug(f"can't execute command, {ctx.author} not in a voice channel")
            return await ctx.channel.send("You must be in a voice channel to play music.")

        for voice_client in bot_voice_clients:
            if voice_client.guild == ctx.guild and author_voice_client.channel != voice_client.channel:
                logger.debug(f"can't execute command, bot is already playing in different channel")
                return await ctx.channel.send("Bot is already playing music in another channel.")

        if not await Youtube_downloader.is_valid_url(url):
            return await ctx.channel.send("Invalid URL")

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
            await ctx.channel.send(f"You did not provide a required argument. The correct syntax is: {config.BOT_PREFIX}play <youtube_url>")

    @commands.command(name="loop", aliases=['l', 'repeat'],
                      brief='Loop the currently playing song',
                      description=config.LOOP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def loop(self, ctx):
        logger.info(f"{config.BOT_PREFIX}loop command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.loop(ctx)

    @commands.command(name="skip", aliases=['s', 'next'],
                      brief='Play the next song in the playlist',
                      description=config.SKIP_COMMAND_DESCRIPTION)
    @commands.cooldown(3, 1, commands.BucketType.user)
    @commands.guild_only()
    async def skip(self, ctx):
        logger.info(f"{config.BOT_PREFIX}skip command is executing by {ctx.author}")
        controller = self.get_guild_controller(ctx)
        await controller.skip(ctx)

    @commands.command(name="prev", aliases=['pr', 'last'],
                      brief='Play the previous song in the playlist',
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
        logger.info(f"{config.BOT_PREFIX}playlist command is executing by {ctx.author}")
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


    if config.SLASH_COMMANDS:

        @app_commands.command(name="play", description="Play music in a voice channel")
        @app_commands.guild_only()
        async def slash_play(self, interaction: discord.Interaction, url: str):
            logger.info(f"/play command is executing by {interaction.user}")
            await interaction.response.defer()
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
            author_voice_client = ctx.author.voice
            bot_voice_clients = self.bot.voice_clients

            if not author_voice_client:
                logger.debug(f"can't execute command, {ctx.author} not in a voice channel")
                return await ctx.channel.send("You must be in a voice channel to play music.")

            for voice_client in bot_voice_clients:
                if voice_client.guild == ctx.guild and author_voice_client.channel != voice_client.channel:
                    logger.debug(f"can't execute command, bot is already playing in different channel")
                    return await ctx.channel.send("Bot is already playing music in another channel.")

            if not await Youtube_downloader.is_valid_url(url):
                return await ctx.channel.send("Invalid URL")

            if ctx.guild.voice_client:  # if already connected to a voice channel, add song to playlist
                await controller.add_to_playlist(ctx, url)
                await interaction.followup.send("Add to playlist", ephemeral=True)
            else:  # connect to voice channel and start playing first song
                controller.playlist = Playlist()
                if await controller.add_to_playlist(ctx, url):
                    await author_voice_client.channel.connect()
                    await controller.play_song(ctx, controller.playlist.head)
                    await interaction.followup.send("Audioplayer startup", ephemeral=True)

            
        @app_commands.command(name="loop", description="Loop the currently playing song")
        @app_commands.guild_only()
        async def slash_loop(self, interaction: discord.Interaction):
            logger.info(f"/loop command is executing by {interaction.user}")
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
        
            try:
                await controller.loop(ctx)
                await interaction.response.send_message(f"Loop mode: {controller.is_loop}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Can't loop", ephemeral=True)
        
        @app_commands.command(name="skip", description="Play the next song in the playlist")
        @app_commands.guild_only()
        async def slash_skip(self, interaction: discord.Interaction):
            logger.info(f"/skip command is executing by {interaction.user}")
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
            if await controller.skip(ctx):
                await interaction.response.send_message("Skip", ephemeral=True)
            else: 
                await interaction.response.send_message("Can't skip", ephemeral=True)

        @app_commands.command(name="prev", description="Play the previous song in the playlist")
        @app_commands.guild_only()
        async def slash_prev(self, interaction: discord.Interaction):
            logger.info(f"/prev command is executing by {interaction.user}")
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
            if await controller.prev(ctx):
                await interaction.response.send_message("Prev", ephemeral=True)
            else:
                await interaction.response.send_message("Can't play previous song", ephemeral=True)

        @app_commands.command(name="pause", description="Pause audio in voice channel")
        @app_commands.guild_only()
        async def slash_pause(self, interaction: discord.Interaction):
            logger.info(f"/pause command is executing by {interaction.user}")
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
            if await controller.pause(ctx):
                await interaction.response.send_message("Paused", ephemeral=True)
            else:
                await interaction.response.send_message("Can't pause", ephemeral=True)

        @app_commands.command(name="resume", description="Resume audio in voice channel")
        @app_commands.guild_only()
        async def slash_resume(self, interaction: discord.Interaction):
            logger.info(f"/resume command is executing by {interaction.user}")
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
            if await controller.resume(ctx):
                await interaction.response.send_message("Resumed", ephemeral=True)
            else:
                await interaction.response.send_message("Can't resume", ephemeral=True)

        @app_commands.command(name="playlist", description="Get a list of songs from the playlist")
        @app_commands.guild_only()
        async def slash_playlist(self, interaction: discord.Interaction):
            logger.info(f"/playlist command is executing by {interaction.user}")
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
            await controller.playlist(ctx)
            await interaction.response.send_message("Done", ephemeral=True)

        @app_commands.command(name="stop", description="Stop audio and disconnect from voice channel")
        @app_commands.guild_only()
        async def slash_stop(self, interaction: discord.Interaction):
            logger.info(f"/stop command is executing by {interaction.user}")
            ctx = await self.bot.get_context(interaction)
            controller = self.get_guild_controller(ctx)
            await controller.stop(ctx)
            await interaction.response.send_message("bye, see you later", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Music_player(bot))
