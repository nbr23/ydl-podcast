import os
from datetime import date, timedelta

from ydl_podcast import process_options


def test_defaults(mock_ydl_mod, base_sub):
    opts = process_options(mock_ydl_mod, base_sub)
    assert "outtmpl" in opts
    assert "writeinfojson" in opts
    assert "daterange" not in opts
    assert "max_downloads" not in opts
    assert "format" not in opts


def test_retention_days(mock_ydl_mod, base_sub):
    base_sub["retention_days"] = 7
    opts = process_options(mock_ydl_mod, base_sub)
    dr = opts["daterange"]
    expected_start = (date.today() - timedelta(days=7)).strftime("%Y%m%d")
    assert dr.start == expected_start
    assert dr.end == "99991231"


def test_retention_skipped_on_initialize(mock_ydl_mod, base_sub):
    base_sub["retention_days"] = 7
    base_sub["initialize"] = True
    opts = process_options(mock_ydl_mod, base_sub)
    assert "daterange" not in opts


def test_download_last(mock_ydl_mod, base_sub):
    base_sub["download_last"] = 5
    opts = process_options(mock_ydl_mod, base_sub)
    assert opts["max_downloads"] == 5


def test_download_last_skipped_on_initialize(mock_ydl_mod, base_sub):
    base_sub["download_last"] = 5
    base_sub["initialize"] = True
    opts = process_options(mock_ydl_mod, base_sub)
    assert "max_downloads" not in opts
    assert opts["playlistreverse"] is True


def test_audio_only(mock_ydl_mod, base_sub):
    base_sub["audio_only"] = True
    opts = process_options(mock_ydl_mod, base_sub)
    assert opts["format"] == "bestaudio/best"
    assert len(opts["postprocessors"]) == 1
    assert opts["postprocessors"][0]["key"] == "FFmpegExtractAudio"


def test_audio_only_with_format(mock_ydl_mod, base_sub):
    base_sub["audio_only"] = True
    base_sub["format"] = "mp3"
    opts = process_options(mock_ydl_mod, base_sub)
    assert opts["format"] == "bestaudio/mp3"


def test_video_format_best(mock_ydl_mod, base_sub):
    base_sub["best"] = True
    base_sub["format"] = "mp4"
    opts = process_options(mock_ydl_mod, base_sub)
    assert opts["format"] == "bestvideo[ext=mp4]"


def test_video_format_no_best(mock_ydl_mod, base_sub):
    base_sub["best"] = False
    base_sub["format"] = "mp4"
    opts = process_options(mock_ydl_mod, base_sub)
    assert opts["format"] == "mp4"


def test_ydl_options_passthrough(mock_ydl_mod, base_sub):
    base_sub["ydl_options"] = {"geo_bypass": True, "sleep_interval": 5}
    opts = process_options(mock_ydl_mod, base_sub)
    assert opts["geo_bypass"] is True
    assert opts["sleep_interval"] == 5


def test_initialize_playlistreverse(mock_ydl_mod, base_sub):
    base_sub["initialize"] = True
    opts = process_options(mock_ydl_mod, base_sub)
    assert opts["playlistreverse"] is True
