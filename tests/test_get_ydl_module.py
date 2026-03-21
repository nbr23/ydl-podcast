from ydl_podcast import get_ydl_module


def test_explicit_module():
    mod = get_ydl_module({"youtube-dl-module": "yt-dlp"})
    assert mod.__name__ == "yt_dlp"


def test_default_finds_yt_dlp():
    mod = get_ydl_module({})
    assert mod.__name__ in ("youtube_dl", "yt_dlp")
