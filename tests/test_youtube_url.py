from downloader import Youtube_downloader

def test_valid_youtube_url() -> None:
    youtube_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley"
    youtube_video_short_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    youtube_stream_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk&ab_channel=LofiGirl"
    youtube_radio_url = "https://www.youtube.com/watch?v=eOii1YaxRK8&list=RDeOii1YaxRK8&start_radio=1&ab_channel=Cringelord"
    youtube_playlist_url = "https://www.youtube.com/playlist?list=PLaIpgnL0MSIpQV5mBSMk73V4-1KS5IGpO"
    youtube_music_url = "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
    youtube_short_url = "https://www.youtube.com/shorts/RMiOtRFwbAg"
    assert Youtube_downloader.is_youtube_url(youtube_video_url) == True
    assert Youtube_downloader.is_youtube_url(youtube_video_short_url) == True
    assert Youtube_downloader.is_youtube_url(youtube_stream_url) == True
    assert Youtube_downloader.is_youtube_url(youtube_radio_url) == True
    assert Youtube_downloader.is_youtube_url(youtube_playlist_url) == True 
    assert Youtube_downloader.is_youtube_url(youtube_music_url) == True
    assert Youtube_downloader.is_youtube_url(youtube_short_url) == True

def test_not_valid_url() -> None:
    not_url = "Test"
    spotify_url = "https://open.spotify.com/track/4NsPgRYUdHu2Q5JRNgXYU5"
    link_without_protocol = "www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley"
    link_without_protocol_and_www = "youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley"
    assert Youtube_downloader.is_youtube_url(not_url) == False
    assert Youtube_downloader.is_youtube_url(spotify_url) == False
    assert Youtube_downloader.is_youtube_url(link_without_protocol) == False
    assert Youtube_downloader.is_youtube_url(link_without_protocol_and_www) == False

