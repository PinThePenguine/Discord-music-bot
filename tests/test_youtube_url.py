import pytest

from downloader import Youtube_downloader

youtube_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley"
youtube_video_short_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
youtube_stream_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk&ab_channel=LofiGirl"
youtube_radio_url = "https://www.youtube.com/watch?v=eOii1YaxRK8&list=RDeOii1YaxRK8&start_radio=1&ab_channel=Cringelord"
youtube_playlist_url = "https://www.youtube.com/playlist?list=PLaIpgnL0MSIpQV5mBSMk73V4-1KS5IGpO"
youtube_music_url = "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
youtube_short_url = "https://www.youtube.com/shorts/RMiOtRFwbAg"


def test_valid_youtube_url() -> None:
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

@pytest.mark.asyncio
async def test_available_youtube_url() -> None:
    assert await Youtube_downloader.is_valid_youtube_url(youtube_video_url) == True
    assert await Youtube_downloader.is_valid_youtube_url(youtube_video_short_url) == True
    assert await Youtube_downloader.is_valid_youtube_url(youtube_stream_url) == True
    assert await Youtube_downloader.is_valid_youtube_url(youtube_radio_url) == True
    assert await Youtube_downloader.is_valid_youtube_url(youtube_playlist_url) == True 
    assert await Youtube_downloader.is_valid_youtube_url(youtube_music_url) == True
    assert await Youtube_downloader.is_valid_youtube_url(youtube_short_url) == True

@pytest.mark.asyncio
async def test_unavailable_youtube_url() -> None:
    youtube_unavailable_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcX&ab_channel=RickAstley"
    youtube_unavailable_video_short_url = "https://www.youtube.com/watch?v=dQw4w9WgXcX"
    youtube_unavailable_stream_url = "https://www.youtube.com/watch?v=jfKfPfyJXdk&ab_channel=LofiGirl"
    youtube_unavailable_radio_url = "https://www.youtube.com/watch?v=eOiXXYaxRK8&list=RDeOii1YaxRK8&start_radio=1&ab_channel=Cringelord"
    youtube_unavailable_playlist_url = "https://www.youtube.com/playlist?list=PLaIpgnL0MXXpQV5mBSMk73V4-1KS5IGpO"
    youtube_unavailable_music_url = "https://music.youtube.com/watch?v=dQw4w9WgXcX"
    youtube_unavailable_short_url = "https://www.youtube.com/shorts/RMiXXAFCbAg"
    youtube_private_video_url = "https://www.youtube.com/watch?v=QayMbsOC5q4"
    assert await Youtube_downloader.is_valid_youtube_url(youtube_unavailable_video_url) == False
    assert await Youtube_downloader.is_valid_youtube_url(youtube_unavailable_video_short_url) == False
    assert await Youtube_downloader.is_valid_youtube_url(youtube_unavailable_stream_url) == False
    assert await Youtube_downloader.is_valid_youtube_url(youtube_unavailable_radio_url) == False
    assert await Youtube_downloader.is_valid_youtube_url(youtube_unavailable_playlist_url) == False
    assert await Youtube_downloader.is_valid_youtube_url(youtube_unavailable_music_url) == False
    assert await Youtube_downloader.is_valid_youtube_url(youtube_unavailable_short_url) == False
    assert await Youtube_downloader.is_valid_youtube_url(youtube_private_video_url) == False

def test_get_youtube_media_type() -> None:
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley") is "video"
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is "video"
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/watch?v=jfKfPfyJRdk&ab_channel=LofiGirl") is "video"
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/watch?v=eOii1YaxRK8&list=RDeOii1YaxRK8&start_radio=1&ab_channel=Cringelord") is "mix"
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/playlist?list=PLaIpgnL0MSIpQV5mBSMk73V4-1KS5IGpO") is "playlist"
    assert Youtube_downloader.get_youtube_media_type("https://music.youtube.com/watch?v=dQw4w9WgXcQ") is "music"
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/shorts/RMiOtRFwbAg") is "short"
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/playlist?list=PLMO3zUYl0xd2Zbrkx1ERFFrU6Z48DWTFC") is "playlist"
    assert Youtube_downloader.get_youtube_media_type("https://www.youtube.com/watch?v=Ph4BZqB7yr4&list=PLETrjXbz9eLX_QaeiE-Jx2uFyJTffFcu3&index=53") is "video"
    
def test_valid_youtube_urls() -> None:
    file = open('tests\\youtube_urls.txt', 'r')
    lines = file.readlines()
    for line in lines:
        assert Youtube_downloader.is_youtube_url(line) is True

def test_normalize_youtube_video_url() -> None:
    assert Youtube_downloader.normalize_youtube_video_url('http://youtu.be/SA2iWivDJiE') is "https://www.youtube.com/watch?v=SA2iWivDJiE"
    assert Youtube_downloader.normalize_youtube_video_url('http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu') is "https://www.youtube.com/watch?v=_oPAwA_Udwc"
    assert Youtube_downloader.normalize_youtube_video_url('http://www.youtube.com/embed/SA2iWivDJiE') is "https://www.youtube.com/watch?v=SA2iWivDJiE"
    assert Youtube_downloader.normalize_youtube_video_url('http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US') is "https://www.youtube.com/watch?v=SA2iWivDJiE"
    assert Youtube_downloader.normalize_youtube_video_url('https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6') is "https://www.youtube.com/watch?v=rTHlyTphWP0"
    assert Youtube_downloader.normalize_youtube_video_url('youtube.com/watch?v=_lOT2p_FCvA') is "https://www.youtube.com/watch?v=_lOT2p_FCvA"
    assert Youtube_downloader.normalize_youtube_video_url('youtu.be/watch?v=_lOT2p_FCvA') is "https://www.youtube.com/watch?v=_lOT2p_FCvA"
    assert Youtube_downloader.normalize_youtube_video_url('https://www.youtube.com/watch?time_continue=9&v=n0g-Y0oo5Qs&feature=emb_logo') is "https://www.youtube.com/watch?v=n0g-Y0oo5Qs"

def test_normalize_youtube_playlist_url() -> None:
    result = "https://www.youtube.com/playlist?list=PLMO3zUYl0xd2Zbrkx1ERFFrU6Z48DWTFC"
    assert Youtube_downloader.normalize_youtube_playlist_url("https://www.youtube.com/playlist?list=PLMO3zUYl0xd2Zbrkx1ERFFrU6Z48DWTFC") == result
    assert Youtube_downloader.normalize_youtube_playlist_url("https://www.youtube.com/watch?v=Jo9Mmx7AqDQ&list=PLMO3zUYl0xd2Zbrkx1ERFFrU6Z48DWTFC") == result
    assert Youtube_downloader.normalize_youtube_playlist_url("https://www.youtube.com/watch?v=Jo9Mmx7AqDQ&list=PLMO3zUYl0xd2Zbrkx1ERFFrU6Z48DWTFC&ab_channel=AIClips") == result