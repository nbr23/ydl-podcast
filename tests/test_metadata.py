import json
import os

import pytest

from ydl_podcast import metadata_file_extension, get_real_thumbnail_ext, metadata_parse


class TestMetadataFileExtension:
    def test_uses_ext(self, tmp_path):
        md = {"format": "bestvideo+bestaudio", "ext": "mp4"}
        assert metadata_file_extension(md, str(tmp_path), "video") == "mp4"

    def test_audio_only_acodec(self, tmp_path):
        (tmp_path / "video.opus").write_bytes(b"")
        md = {"format": "audio only", "acodec": "opus", "ext": "webm"}
        assert metadata_file_extension(md, str(tmp_path), "video") == "opus"

    def test_audio_only_file_missing(self, tmp_path):
        md = {"format": "audio only", "acodec": "opus", "ext": "webm"}
        assert metadata_file_extension(md, str(tmp_path), "video") == "webm"

    def test_none_ext_raises(self, tmp_path):
        md = {"format": "bestvideo+bestaudio", "ext": None}
        with pytest.raises(Exception, match="No extension found"):
            metadata_file_extension(md, str(tmp_path), "video")


class TestGetRealThumbnailExt:
    def test_finds_match(self, tmp_path):
        (tmp_path / "video.png").write_bytes(b"")
        path = str(tmp_path / "video.info.json")
        assert get_real_thumbnail_ext(path, "webp") == "png"

    def test_no_match(self, tmp_path):
        path = str(tmp_path / "video.info.json")
        assert get_real_thumbnail_ext(path, "webp") == "webp"


class TestMetadataParse:
    def test_full(self, make_info_json):
        info_path = make_info_json()
        result = metadata_parse(info_path)
        assert result["title"] == "Test Video"
        assert result["id"] == "abc123"
        assert result["extension"] == "mp4"
        assert result["description"] == "A test video"
        assert result["duration"] == "1:01:01"
        assert result["thumbnail"] is not None
        assert result["filename"].endswith(".mp4")
        assert result["timestamp"] > 0

    def test_playlist_returns_none(self, make_info_json):
        info_path = make_info_json(overrides={"_type": "playlist"})
        assert metadata_parse(info_path) is None

    def test_no_thumbnail(self, make_info_json):
        info_path = make_info_json(overrides={"thumbnail": None})
        result = metadata_parse(info_path)
        assert result["thumbnail"] is None

    def test_no_duration(self, make_info_json):
        info_path = make_info_json(overrides={"duration": None})
        result = metadata_parse(info_path)
        assert result["duration"] is None

    def test_scandir_fallback(self, tmp_path):
        sub_dir = tmp_path / "testsub"
        sub_dir.mkdir()
        basename = "Test Video [abc123][20250101]"

        md = {
            "title": "Test Video",
            "id": "abc123",
            "upload_date": "20250101",
            "ext": "mp4",
            "format": "bestvideo+bestaudio",
            "duration": 100,
            "description": "test",
            "thumbnail": None,
        }
        info_path = sub_dir / f"{basename}.info.json"
        info_path.write_text(json.dumps(md))
        (sub_dir / f"{basename}.webm").write_bytes(b"")

        result = metadata_parse(str(info_path))
        assert result["extension"] == "webm"

    def test_missing_upload_date_returns_none(self, make_info_json):
        info_path = make_info_json(overrides={"upload_date": None})
        assert metadata_parse(info_path) is None
