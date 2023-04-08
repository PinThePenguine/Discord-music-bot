import asyncio
from io import StringIO

import discord
import yt_dlp
from discord.ext import commands
from loguru import logger

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}

# add option for playing youtube playlists
# add to playlist with another thread


class Song():
    def __init__(self, title=None, url=None, duration=None):
        self.title = title
        self.url = url
        self.duration = duration
        self.next = None
        self.prev = None


class Playlist():
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        logger.debug("initializing playlist")

    def push_song(self, song):
        song.next = self.head
        if self.head is not None:
            self.head.prev = song
        self.head = song
        self.size += 1
        logger.debug("Song pushed")

    def append_song(self, song):
        song.next = None
        if self.head is None:
            song.prev = None
            self.head = song
            return
        last = self.head
        while (last.next is not None):
            last = last.next
        last.next = song
        song.prev = last
        logger.debug("Song appended")

    def next_song(self):
        if self.head.next is None:
            logger.debug("There is no next song in the playlist")
            return None
        self.head = self.head.next
        logger.debug("Changin head to next song in the playlist")
        return self.head.url

    def get_next_song_title(self):
        if self.head.next is None:
            return None
        return self.head.next.title

    def previous_song(self):
        if self.head.prev is None:
            logger.debug("Thre is no previous song in the playlist")
            return None
        self.head = self.head.prev
        logger.debug("Changin head to previous song in the playlist")
        return self.head.url

    def print_playlist(self, head):
        ss = StringIO()
        ss.write('\tPlaylist:\n')
        while (head is not None):
            ss.write(f'{head.title}\n')
            last = head
            head = head.next
        return ss.getvalue()


class Youtube_downloader():

    def __init__(self):
        self.downloader = yt_dlp.YoutubeDL(YDL_OPTIONS)
        logger.debug('init downloader')

    def create_song(self, url):
        song_info = self.downloader.extract_info(url, download=False)
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
        self.song_changer_task = None
        self.is_loop = False

    async def exit(self, ctx):
        self.is_loop = False
        self.song_changer_task = None
        self.playlist = None
        self.audio_source.cleanup()
        logger.debug("There are no more songs, processing to exit.")
        await ctx.send("My job here is done!")
        await ctx.guild.voice_client.disconnect()
        logger.debug("Disconnected from voice client")

    async def add_song_to_playlist(self, ctx, url):
        song = Youtube_downloader().create_song(url)
        self.playlist.append_song(song)
        await ctx.send(f"Add {song.title} to playlist")

    async def play_song(self, ctx, song):
        logger.debug("Trying to play song")
        if song is not None:
            await ctx.send(f"Now playing: {self.playlist.head.title}")
            self.audio_source = discord.FFmpegPCMAudio(
                song,
                **FFMPEG_OPTIONS)
            ctx.voice_client.play(self.audio_source, after=lambda e: self.play_next_song(ctx))
            logger.debug("Audio stream started")

    def play_next_song(self, ctx):
        if self.playlist is None: return
        logger.debug("Changing song: check if loop state is active")
        if self.is_loop:
            logger.debug("loop state is active, playing same song")
            self.song_changer_task = self.bot.loop.create_task(self.play_song(ctx, self.playlist.head.url))
        else:
            if self.playlist.next_song() is not None:
                logger.debug("no loop state, changing song")
                self.song_changer_task = self.bot.loop.create_task(self.play_song(ctx, self.playlist.head.url))
            else:
                self.bot.loop.create_task(self.exit(ctx))

    @commands.command()
    async def play(self, ctx, url):
        logger.debug(f"!play command is executing by {ctx.author}")
        if ctx.author.voice is None:
            await ctx.send("You must be in a voice channel to play music.")
            logger.debug(f"can't execute command, {ctx.author} not in a voice channel")
            return

        if self.bot.voice_clients:
            if ctx.author.voice.channel != self.bot.voice_clients[0].channel:
                logger.debug(f"can't execute command, bot is already playing in different channel")
                await ctx.send("Bot is already playing music in another channel.")
                return

        if ctx.guild.voice_client: #if already connected to a voice channel, add song to playlist
            await self.add_song_to_playlist(ctx, url) 
        else: #or connect to voice channel and start playing first song
            await ctx.author.voice.channel.connect()
            self.playlist = Playlist()
            song = Youtube_downloader().create_song(url)
            self.playlist.push_song(song)
            await self.play_song(ctx, self.playlist.head.url)

    @commands.command()
    async def loop(self, ctx):
        logger.debug(f"!loop command is executing by {ctx.author}")
        if not self.is_loop:
            self.is_loop = True
            logger.debug("Loop state: ON")
            await ctx.send("Music is now looping. To disable loop mode send '!loop'")
        else:
            self.is_loop = False
            logger.debug("Loop state: OFF")
            await ctx.send("Music is no longer looping.")

    @commands.command()
    async def skip(self, ctx):  # todo: skip in loop state
        logger.debug(f"!skip command is executing by {ctx.author}")
        voice_client = ctx.voice_client
        if not voice_client:
            logger.debug("can't skip, not in voice channel")
            await ctx.send("I'm not in voice channel")
            return

        if self.is_loop:
            logger.debug("can't skip in loop state")
            await ctx.send("Can't skip in loop state")
            return

        song = self.playlist.next_song()
        if song is not None:
            logger.debug('cleanup audio source')
            ctx.voice_client.pause()
            self.audio_source.cleanup()
            await self.play_song(ctx, song)
        else:
            logger.debug("can't skip, there are no next song")
            await ctx.send("No next song.")

    @commands.command()
    async def prev(self, ctx):  # todo skip in loop
        logger.debug(f"!prev command is executing by {ctx.author}")
        voice_client = ctx.voice_client
        if not voice_client:
            logger.debug("can't prev, not in voice channel")
            await ctx.send("I'm not in voice channel")
            return

        if self.is_loop:
            logger.debug("can't prev in loop state")
            await ctx.send("Can't prev in loop state")
            return

        song = self.playlist.previous_song()
        if song is not None:

            if self.song_changer_task is not None:
                self.song_changer_task.cancel()
                logger.debug("cancel changing task")

            ctx.voice_client.pause()
            await self.play_song(ctx, song)
        else:
            logger.debug("can't prev, there are no previous song")
            await ctx.send("No previous song.")

    @commands.command()
    async def pause(self, ctx):
        logger.debug(f"!pause command is executing by {ctx.author}")
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            logger.debug("audio source paused")
        else:
            logger.debug(f"can't pause")
            await ctx.send("I'm not currently playing any audio.")

    @commands.command()
    async def resume(self, ctx):
        logger.debug(f"!resume command is executing by {ctx.author}")
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            logger.debug("audio source resumed")
        else:
            logger.debug("can't resume")
            await ctx.send("I'm not currently paused.")

    @commands.command()
    async def playlist(self, ctx):
        logger.debug(f"!playlist command is executing by {ctx.author}")
        await ctx.send(self.playlist.print_playlist(self.playlist.head))

    @commands.command()
    async def stop(self, ctx):
        logger.debug(f"!stop command is executing by {ctx.author}")
        voice_client = ctx.voice_client
        if voice_client:
            logger.debug("cleaning up")
            await self.exit(ctx)
        else:
            await ctx.send("I'm not currently in voice channel.")


async def setup(bot):
    await bot.add_cog(Music_player(bot))
