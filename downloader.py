import asyncio
import re
from queue import Queue

import aiohttp
import yt_dlp
from loguru import logger

from song import Song

YDL_OPTIONS = {'format': 'bestaudio/best'}


class Youtube_downloader:
    """
    A class for downloading and extracting information about songs or playlists from YouTube URLs.
    Attributes:
    downloader (YoutubeDL): A YoutubeDL object for downloading and extracting information.

    Methods:
        is_youtube_url(url): Determines whether the given URL is a YouTube URL.
        is_valid_youtube_url(url): Determines whether the given YouTube URL is valid and the video is not unavailable.
        is_valid_url(url): Determines whether the given URL is a valid YouTube URL and the video is not unavailable.
        create_song(url, result_queue, is_playlist=False): Downloads and extracts information about a song or playlist from the given URL, creates Song objects, and adds them to the result queue.
    """

    def __init__(self):
        """
        Initializes the Youtube_downloader class and creates a YoutubeDL object for downloading and extracting information.
        """
        self.downloader = yt_dlp.YoutubeDL(YDL_OPTIONS)

    def is_youtube_url(self, url: str) -> bool:
        """
        Determines whether the given URL is a valid YouTube URL.

        Args:
            url (str): The URL to be checked.

        Returns:
            bool: True if the URL is a valid YouTube URL, False otherwise.
        """
        if re.search(r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|\?v=)([^#\&\?]*).*", url) or "https://www.youtube.com/playlist?list=" in url:
            return True
        return False

    async def is_valid_youtube_url(self, url: str) -> bool:
        """
        Determines whether the given YouTube URL is valid and the video is not unavailable.

        Args:
            url (str): The YouTube URL to be checked.

        Returns:
            bool: True if the YouTube URL is valid and the video is not unavailable, False otherwise.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                text = await response.text()
                is_valid = not ("Video unavailable" in text)
                return is_valid

    def is_valid_url(self, url: str) -> bool:
        """
        Determines whether the given URL is a valid YouTube URL and the video is not unavailable.

        Args:
            url (str): The URL to be checked.

        Returns:
            bool: True if the URL is a valid YouTube URL and the video is not unavailable, False otherwise.
        """
        if self.is_youtube_url(url) and asyncio.create_task(self.is_valid_youtube_url(url)):
            return True
        return False

    def create_song(self, url: str, result_queue: Queue, is_playlist=False):
        """
        Downloads and extracts information about a song or playlist from a given URL, creates Song objects and adds them to the result queue.

        Args:
            url (str): The URL of the song or playlist to be downloaded and extracted.
            result_queue (Queue): The queue where the Song objects will be added.
            is_playlist (bool, optional): Indicates whether the URL is for a playlist or not. Defaults to False.

        Example:
            create_song('https://www.youtube.com/watch?v=dQw4w9WgXcQ', my_queue)
            create_song('https://www.youtube.com/playlist?list=PLw-VjHDlEOguGHBf1BV-XS4pmt9wR1cBC', my_queue, is_playlist=True)
        """
        try:
            if is_playlist:
                playlist_info = self.downloader.extract_info(url, download=False, process=False)
                if 'entries' not in playlist_info:
                    logger.error("No entries found in the playlist")
                    return None
                for song in playlist_info['entries']:
                    song_info = self.downloader.extract_info(song.get('url'), download=False)
                    new_song = Song()
                    new_song.title = song_info.get('title')
                    new_song.url = song_info.get('url')
                    new_song.duration = song_info.get('duration')
                    logger.debug(f'New song: {new_song.title} with duration: {new_song.duration} are created')
                    result_queue.put(new_song)
            else:
                song_info = self.downloader.extract_info(url, download=False)
                new_song = Song()
                new_song.title = song_info.get('title')
                new_song.url = song_info.get('url')
                new_song.duration = song_info.get('duration')
                logger.debug(f'New song: {new_song.title} with duration: {new_song.duration} are created')
                result_queue.put(new_song)

        except Exception as e:
            logger.error(f"Can't extract info from {url}\n {e}")
            return None
