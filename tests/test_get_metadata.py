import io
import json
import types
from unittest.mock import MagicMock, patch

import pytest

from ydl_podcast import get_metadata


def _make_ydl_mod(output_json, raise_error=False):
    mod = types.SimpleNamespace()

    class FakeYDL:
        def __init__(self, options):
            self.options = options
            self._out_files = types.SimpleNamespace(out=None, error=None)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def download(self, urls):
            if raise_error:
                raise mod.utils.YoutubeDLError("fail")
            self._out_files.out.write(output_json)

    class YoutubeDLError(Exception):
        pass

    mod.YoutubeDL = FakeYDL
    mod.utils = types.SimpleNamespace(YoutubeDLError=YoutubeDLError)
    return mod


def test_single_json_mode():
    data = {"id": "abc", "title": "Test"}
    mod = _make_ydl_mod(json.dumps(data))
    result = get_metadata(mod, "http://example.com", {}, quiet=True, single_json=True)
    assert result == data


def test_per_video_mode():
    data = {"id": "abc", "_filename": "test.mp4"}
    mod = _make_ydl_mod(json.dumps(data) + "\n")
    result = get_metadata(mod, "http://example.com", {}, quiet=True, single_json=False)
    assert result == data


def test_per_video_empty_returns_none():
    mod = _make_ydl_mod("")
    result = get_metadata(mod, "http://example.com", {}, quiet=True, single_json=False)
    assert result is None


def test_options_include_dump_single_json():
    mod = _make_ydl_mod(json.dumps({"id": "x"}))

    original_init = mod.YoutubeDL.__init__

    captured = {}
    def tracking_init(self, options):
        captured.update(options)
        original_init(self, options)

    mod.YoutubeDL.__init__ = tracking_init
    get_metadata(mod, "http://example.com", {}, single_json=True)
    assert captured["dump_single_json"] is True
    assert "forcejson" not in captured


def test_options_include_forcejson():
    mod = _make_ydl_mod(json.dumps({"id": "x"}) + "\n")

    original_init = mod.YoutubeDL.__init__

    captured = {}
    def tracking_init(self, options):
        captured.update(options)
        original_init(self, options)

    mod.YoutubeDL.__init__ = tracking_init
    get_metadata(mod, "http://example.com", {}, single_json=False)
    assert captured["forcejson"] is True
    assert "dump_single_json" not in captured


def test_does_not_mutate_input_options():
    mod = _make_ydl_mod(json.dumps({"id": "x"}))
    options = {"some_key": "some_value"}
    original = options.copy()
    get_metadata(mod, "http://example.com", options)
    assert options == original


def test_error_quiet_returns_without_raising(capsys):
    mod = _make_ydl_mod("", raise_error=True)
    mod.YoutubeDL._original_download = mod.YoutubeDL.download

    class ErrorYDL(mod.YoutubeDL):
        def download(self, urls):
            raise mod.utils.YoutubeDLError("fail")

    mod.YoutubeDL = ErrorYDL
    result = get_metadata(mod, "http://example.com", {}, quiet=True, single_json=False)
    assert result is None
    assert capsys.readouterr().out == ""


def test_error_not_quiet_prints(capsys):
    mod = _make_ydl_mod("", raise_error=True)

    class ErrorYDL(mod.YoutubeDL):
        def download(self, urls):
            raise mod.utils.YoutubeDLError("fail")

    mod.YoutubeDL = ErrorYDL
    result = get_metadata(mod, "http://example.com", {}, quiet=False, single_json=False)
    assert result is None
    assert "fail" in capsys.readouterr().out
