import io
import types

from ydl_podcast import silence_ydl


def _make_ydl(has_out_files=True):
    ydl = types.SimpleNamespace()
    if has_out_files:
        ydl._out_files = types.SimpleNamespace(out=None, error=None)
    else:
        ydl._screen_file = None
        ydl._err_file = None
    return ydl


def test_redirects_output_new_api():
    ydl = _make_ydl(has_out_files=True)
    output = io.StringIO()
    silence_ydl(ydl, output=output, quiet=False)
    assert ydl._out_files.out is output


def test_redirects_output_old_api():
    ydl = _make_ydl(has_out_files=False)
    output = io.StringIO()
    silence_ydl(ydl, output=output, quiet=False)
    assert ydl._screen_file is output


def test_quiet_silences_all_new_api():
    ydl = _make_ydl(has_out_files=True)
    silence_ydl(ydl, quiet=True)
    assert isinstance(ydl._out_files.out, io.StringIO)
    assert isinstance(ydl._out_files.error, io.StringIO)


def test_quiet_silences_all_old_api():
    ydl = _make_ydl(has_out_files=False)
    silence_ydl(ydl, quiet=True)
    assert isinstance(ydl._screen_file, io.StringIO)
    assert isinstance(ydl._err_file, io.StringIO)


def test_not_quiet_leaves_error_alone_new_api():
    ydl = _make_ydl(has_out_files=True)
    output = io.StringIO()
    silence_ydl(ydl, output=output, quiet=False)
    assert ydl._out_files.error is None


def test_not_quiet_leaves_error_alone_old_api():
    ydl = _make_ydl(has_out_files=False)
    output = io.StringIO()
    silence_ydl(ydl, output=output, quiet=False)
    assert ydl._err_file is None
