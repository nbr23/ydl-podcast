from ydl_podcast import sub_dir, sub_url, strip_info_json_ext


def test_sub_dir_no_parts(tmp_path):
    sub = {"output_dir": str(tmp_path), "name": "mysub"}
    assert sub_dir(sub) == str(tmp_path / "mysub")


def test_sub_dir_with_parts(tmp_path):
    sub = {"output_dir": str(tmp_path), "name": "mysub"}
    assert sub_dir(sub, "file.mp4") == str(tmp_path / "mysub" / "file.mp4")


def test_sub_dir_multiple_parts(tmp_path):
    sub = {"output_dir": str(tmp_path), "name": "mysub"}
    assert sub_dir(sub, "a", "b.txt") == str(tmp_path / "mysub" / "a" / "b.txt")


def test_sub_url():
    sub = {"url_root": "http://localhost:8080", "name": "my sub"}
    result = sub_url(sub, "file name.mp4")
    assert result == "http://localhost:8080/my%20sub/file%20name.mp4"


def test_sub_url_no_encoding_needed():
    sub = {"url_root": "http://localhost:8080", "name": "test"}
    assert sub_url(sub, "video.mp4") == "http://localhost:8080/test/video.mp4"


def test_strip_info_json_ext():
    assert strip_info_json_ext("/path/to/Video Title [id][date].info.json") == "Video Title [id][date]"


def test_strip_info_json_ext_simple():
    assert strip_info_json_ext("file.info.json") == "file"
