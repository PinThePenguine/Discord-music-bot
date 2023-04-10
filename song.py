class Song:
    def __init__(self, title=None, url=None, duration=None):
        self.title = title
        self.url = url
        self.duration = duration
        self.next = None
        self.prev = None
