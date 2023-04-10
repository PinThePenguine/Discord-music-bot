class Song:
    """Represents a single song.

    Attributes:
        title (str): The title of the song.
        url (str): The URL of the song.
        duration (int): The duration of the song in seconds.
        next (Song): The next song in the playlist.
        prev (Song): The previous song in the playlist.
    """

    def __init__(self, title=None, url=None, duration=None):
        """Initializes a new instance of the Song class.

        Args:
            title (str): The title of the song.
            url (str): The URL of the song.
            duration (int): The duration of the song in seconds.
        """
        self.title = title
        self.url = url
        self.duration = duration
        self.next = None
        self.prev = None
