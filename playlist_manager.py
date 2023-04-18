import itertools
import re
import threading
from queue import Queue

from loguru import logger

from downloader import Youtube_downloader
from playlist import Playlist
from song import Song


class Playlist_manager():

    def __init__(self):
        self.downloader = Youtube_downloader()
        self.time_to_shutdown = False

    # push song to playlist

    def create_song(self, url: str):
        """
        Downloads and extracts information about a song from a given URL, creates Song objects and returns it.

        Args:
            url (str): The URL of the song or playlist to be downloaded and extracted.

        Returns:
            Song: Returns a Song object

        Example:
            create_song('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        """
        try:
            song_info = self.downloader.downloader.extract_info(url, download=False)
            song = Song()
            song.title = song_info.get('title')
            song.url = song_info.get('url')
            song.duration = song_info.get('duration')
            logger.debug(f'New song: {song.title} with duration: {song.duration} are created')
            return song
        except Exception as e:
            logger.warning(f"Can't extract info from {url}\n {e}")
            return None

    async def add_song(self, url: str, playlist: Playlist):
        thread = threading.Thread(target=self._add_song, args=(url, playlist))
        thread.start()
        thread.join()

    async def add_playlist(self, url: str, playlist: Playlist):
        
        playlist_info = self.downloader.downloader.extract_info(url, download=False, process=False)
        if 'entries' not in playlist_info: # https://www.youtube.com/watch?v=Jo9Mmx7AqDQ&list=PLMO3zUYl0xd2Zbrkx1ERFFrU6Z48DWTFC&ab_channel=AIClips type link, need normalization
            url = Youtube_downloader.normalize_youtube_playlist_url(url)
            playlist_info = self.downloader.downloader.extract_info(url, download=False, process=False)
            if 'entries' not in playlist_info:
                return False
             
        thread = threading.Thread(target=self._add_first_playlist_song, args=(playlist_info, playlist))
        thread.start()
        thread.join()
        thread = threading.Thread(target=self._add_other_playlist, args=(playlist_info, playlist))
        thread.start()

    def _add_first_playlist_song(self, playlist_info, playlist: Playlist):
        for song in itertools.islice(playlist_info['entries'], 1):
            song = self.create_song(song.get('url'))
            if song:
                playlist.append_song(song)

    def _add_song(self, url: str, playlist: Playlist):
        song = self.create_song(url)
        if song:
            playlist.append_song(song)

    def _add_other_playlist(self, playlist_info, playlist: Playlist):
        for song in itertools.islice(playlist_info['entries'], 0, None):
            if self.time_to_shutdown:  # kill when audio_controller is resetting
                self.time_to_shutdown = False
                return
            song = self.create_song(song.get('url'))
            if song:    
                playlist.append_song(song)
