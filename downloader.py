import asyncio
import itertools
import re
import threading
from queue import Queue

import aiohttp
import yt_dlp
from loguru import logger

from song import Song
from playlist import Playlist

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'socket_timeout': 10,
    'cachedir': False,
    'noresizebuffer': True,
    "extract_flat": "in_playlist",
}


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

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """
        Determines whether the given URL is a valid YouTube URL.

        Args:
            url (str): The URL to be checked.

        Returns:
            bool: True if the URL is a valid YouTube URL, False otherwise.
        """
        if re.search(r"^((?:https?:)\/\/)((?:www|m)\.)?(music.)?((?:youtube(-nocookie)?\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$", url):
            return True
        return False

    @staticmethod
    async def is_valid_youtube_url(url: str) -> bool:
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

    @staticmethod
    async def is_valid_url(url: str) -> bool:
        """
        Determines whether the given URL is a valid YouTube URL and the video is not unavailable.

        Args:
            url (str): The URL to be checked.

        Returns:
            bool: True if the URL is a valid YouTube URL and the video is not unavailable, False otherwise.
        """
        if Youtube_downloader.is_youtube_url(url) and await Youtube_downloader.is_valid_youtube_url(url):
            return True
        return False

    @staticmethod
    def normalize_youtube_playlist_url(url):
        playlist_id = re.search(r"list=([^&]+)", url)
        if playlist_id is not None:
            playlist_id = playlist_id.group(1)
            print("playlist_id")
            return f"https://www.youtube.com/playlist?list={playlist_id}"
        else:
            print("None")
            return None
