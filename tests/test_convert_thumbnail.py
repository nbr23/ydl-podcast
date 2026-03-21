import os

from PIL import Image

from ydl_podcast import convert_thumbnail_to_jpg


def test_jpg_passthrough(tmp_path):
    (tmp_path / "thumb.jpg").write_bytes(b"\xff\xd8\xff")
    result = convert_thumbnail_to_jpg(str(tmp_path), "thumb.jpg")
    assert result == "thumb.jpg"


def test_jpeg_passthrough(tmp_path):
    result = convert_thumbnail_to_jpg(str(tmp_path), "thumb.jpeg")
    assert result == "thumb.jpeg"


def test_converts_png_to_jpg(tmp_path):
    img = Image.new("RGBA", (2, 2), color="blue")
    img.save(str(tmp_path / "thumb.png"))
    result = convert_thumbnail_to_jpg(str(tmp_path), "thumb.png")
    assert result == "thumb.jpg"
    assert os.path.isfile(tmp_path / "thumb.jpg")


def test_converts_webp_to_jpg(tmp_path):
    img = Image.new("RGB", (2, 2), color="green")
    img.save(str(tmp_path / "thumb.webp"))
    result = convert_thumbnail_to_jpg(str(tmp_path), "thumb.webp")
    assert result == "thumb.jpg"
    assert os.path.isfile(tmp_path / "thumb.jpg")


def test_missing_file_returns_original(tmp_path):
    result = convert_thumbnail_to_jpg(str(tmp_path), "missing.webp")
    assert result == "missing.webp"
