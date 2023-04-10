from io import StringIO

from loguru import logger

from song import Song


class Playlist:
    """
    A doubly linked list implementation to store and manage a playlist of songs.

    Attributes:
        head (Song): The first song in the playlist.
        tail (Song): The last song in the playlist.
        size (int): The number of songs in the playlist.

    Methods:
        push_song(self, song): Adds a song to the beginning of the playlist.
        append_song(self, song): Adds a song to the end of the playlist.
        next_song(self): Returns the URL of the next song in the playlist.
        previous_song(self): Returns the URL of the previous song in the playlist.
        print_playlist(self): Returns a string representation of the playlist.
    """

    def __init__(self):
        """Initializes a new instance of the Playlist class."""
        self.head = None
        self.tail = None
        self.size = 0
        logger.debug("initializing playlist")

    def push_song(self, song: Song):
        """
        Adds a song to the beginning of the playlist.

        Args:
            song (Song): The song to be added.
        """
        song.next = self.head
        if self.head is not None:
            self.head.prev = song
        self.head = song
        self.size += 1
        logger.debug("Song pushed")

    def append_song(self, song: Song):
        """
        Adds a song to the end of the playlist.

        Args:
            song (Song): The song to be added.
        """
        song.next = None
        if self.head is None:
            song.prev = None
            self.head = song
            logger.debug(f"Add first song {song.title} to playlist")
            self.size = 1
            return
        last = self.head
        while last.next is not None:
            last = last.next
        last.next = song
        song.prev = last
        self.size += 1
        logger.debug(f"Add {song.title} to playlist")

    def next_song(self):
        """
        Returns the next song in the playlist.

        Returns:
            song (Song): The next song in the playlist.
        """
        if self.head.next is None:
            logger.debug("There is no next song in the playlist")
            return None
        self.head = self.head.next
        logger.debug("Changing head to next song in the playlist")
        return self.head

    def previous_song(self):
        """
        Returns the previous song in the playlist.

        Returns:
            song (Song): The previous song in the playlist.
        """
        if self.head.prev is None:
            logger.debug("There is no previous song in the playlist")
            return None
        self.head = self.head.prev
        logger.debug("Changing head to previous song in the playlist")
        return self.head

    def print_playlist(self):
        """
        Returns a string representation of the playlist.

        Returns:
            str: A string representation of the playlist.
        """
        ss = StringIO()
        ss.write("\tPlaylist:\n")
        pointer = self.head
        while pointer is not None:
            ss.write(f"{pointer.title}\n")
            last = pointer
            pointer = pointer.next
        return ss.getvalue()
