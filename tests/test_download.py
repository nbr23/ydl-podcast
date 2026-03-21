import io
import json
import os
import types

import pytest

from ydl_podcast import _download_with_ydl


def _make_ydl_mod(should_fail=False):
    mod = types.SimpleNamespace()

    class YoutubeDLError(Exception):
        pass

    class FakeYDL:
        def __init__(self, options):
            self._out_files = types.SimpleNamespace(out=None, error=None)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def download(self, urls):
            if should_fail:
                raise YoutubeDLError("download failed")

    mod.YoutubeDL = FakeYDL
    mod.utils = types.SimpleNamespace(YoutubeDLError=YoutubeDLError)
    return mod


def test_success_returns_true():
    mod = _make_ydl_mod(should_fail=False)
    assert _download_with_ydl(mod, {}, "http://example.com", quiet=True) is True


def test_failure_returns_false():
    mod = _make_ydl_mod(should_fail=True)
    assert _download_with_ydl(mod, {}, "http://example.com", quiet=True) is False


def test_failure_quiet_no_output(capsys):
    mod = _make_ydl_mod(should_fail=True)
    _download_with_ydl(mod, {}, "http://example.com", quiet=True)
    assert capsys.readouterr().out == ""


def test_failure_not_quiet_prints(capsys):
    mod = _make_ydl_mod(should_fail=True)
    _download_with_ydl(mod, {}, "http://example.com", quiet=False)
    assert "download failed" in capsys.readouterr().out
