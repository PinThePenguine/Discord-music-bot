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
                pattern_unavailable_video = '"playabilityStatus":{"status":"ERROR","reason":'
                pattern_unavailable_playlist = '{"type":"ERROR","text":{"runs":[{"text":'
                pattern_available_music = 'content="YouTube Music">'
                pattern_private_video = '"errorScreen":{"playerErrorMessageRenderer":{"subreason":{"simpleText":'
                text = await response.text()
                if pattern_unavailable_video in text or pattern_unavailable_playlist in text or pattern_private_video in text : return False
                if 'href="https://music.youtube.com/favicon.ico' in text and pattern_available_music not in text: return False
                return True
    
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
    def get_youtube_media_type(url: str) -> str:
        """
        Determine the type of media associated with a YouTube URL.

        This method analyzes the given YouTube URL and returns the type of media it represents,
        such as music, mix, short, playlist, or video.

        Args:
            url (str): The YouTube URL to be analyzed.

        Returns:
            str: A string representing the type of media associated with the URL. Possible values are:
                - "music" if the URL contains "music".
                - "mix" if the URL contains "radio".
                - "short" if the URL contains "short".
                - "playlist" if the URL contains "playlist".
                - "video" if none of the above conditions match.
        """
        if "music" in url: return "music"
        if "radio" in url: return "mix"
        if "short" in url: return "short"
        if "playlist" in url: return "playlist"
        return "video"

    @staticmethod
    def normalize_youtube_playlist_url(url):
        """
        Normalizes a YouTube playlist URL.

        This method takes a YouTube URL and returns a normalized version of it if it represents a playlist.
        If the input URL is not a playlist URL, it returns None.

        Args:
            url (str): The URL to be normalized.

        Returns:
            Union[str, None]: A normalized YouTube playlist URL if the input URL represents a playlist, 
            otherwise None.
        """
        playlist_id = re.search(r"list=([^&]+)", url)
        if playlist_id is not None:
            playlist_id = playlist_id.group(1)
            print("playlist_id")
            return f"https://www.youtube.com/playlist?list={playlist_id}"
        else:
            print("None")
            return None
        
    @staticmethod
    def normalize_youtube_video_url(url: str) -> str:
        """
        Normalize a YouTube video URL.

        This method takes a YouTube URL and returns a normalized version of it, 
        ensuring that it is in the format of 'https://www.youtube.com/watch?v=VIDEO_ID'.

        Args:
            url (str): The YouTube URL to be normalized.

        Returns:
            str: A normalized YouTube video URL in the format 'https://www.youtube.com/watch?v=VIDEO_ID'.
        """
        video_id = re.findall(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        return f"https://www.youtube.com/watch?v={video_id[0]}"