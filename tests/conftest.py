import json
import os
import types

import pytest
from PIL import Image


SAMPLE_METADATA = {
    "title": "Test Video",
    "id": "abc123",
    "upload_date": "20250101",
    "ext": "mp4",
    "format": "bestvideo+bestaudio",
    "duration": 3661,
    "description": "A test video",
    "thumbnail": "https://example.com/thumb.jpg",
}


@pytest.fixture
def sample_metadata_dict():
    return SAMPLE_METADATA.copy()


@pytest.fixture
def make_info_json(tmp_path):
    def _factory(overrides=None, sub_name="testsub", basename="Test Video [abc123][20250101]"):
        sub_dir = tmp_path / sub_name
        sub_dir.mkdir(exist_ok=True)

        md = {**SAMPLE_METADATA, **(overrides or {})}

        info_path = sub_dir / f"{basename}.info.json"
        info_path.write_text(json.dumps(md))

        ext = md.get("ext", "mp4")
        (sub_dir / f"{basename}.{ext}").write_bytes(b"")

        thumb = Image.new("RGB", (1, 1), color="red")
        thumb.save(str(sub_dir / f"{basename}.jpg"), "JPEG")

        return str(info_path)

    return _factory


@pytest.fixture
def mock_ydl_mod():
    ns = types.SimpleNamespace()

    class DateRange:
        def __init__(self, start, end):
            self.start = start
            self.end = end

    class YoutubeDLError(Exception):
        pass

    ns.utils = types.SimpleNamespace(DateRange=DateRange, YoutubeDLError=YoutubeDLError)
    return ns


@pytest.fixture
def base_sub(tmp_path):
    return {
        "name": "testsub",
        "url": "https://www.youtube.com/channel/test",
        "output_dir": str(tmp_path),
        "url_root": "http://localhost:8080",
        "retention_days": None,
        "audio_only": False,
        "download_last": None,
        "initialize": False,
        "best": False,
        "ignore_errors": False,
        "quiet": True,
        "filename_template": "%(title)s [%(id)s][%(upload_date)s].%(ext)s",
    }


@pytest.fixture
def base_config(tmp_path):
    return {
        "output_dir": str(tmp_path),
        "url_root": "http://localhost:8080",
        "subscriptions": [],
    }
