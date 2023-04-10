class Song:
    """
    Represents a song with a title, URL, and duration.
    """

    def __init__(self, title=None, url=None, duration=None):
        """
        Initializes a new instance of the Song class.

        :param title: The title of the song.
        :type title: str
        :param url: The URL of the song.
        :type url: str
        :param duration: The duration of the song in seconds.
        :type duration: int
        """
        self.title = title
        self.url = url
        self.duration = duration
        self.next = None
        self.prev = None
