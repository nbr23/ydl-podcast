import os
import xml.etree.ElementTree as ET

from ydl_podcast import write_xml


def _setup_sub(tmp_path, make_info_json, base_sub, base_config, **overrides):
    sub = {**base_sub, **overrides}
    sub_dir = tmp_path / sub["name"]
    sub_dir.mkdir(exist_ok=True)
    return sub


def test_produces_valid_rss(tmp_path, make_info_json, base_sub, base_config):
    make_info_json()
    sub = _setup_sub(tmp_path, make_info_json, base_sub, base_config)
    write_xml(base_config, sub)

    xml_path = os.path.join(str(tmp_path), "testsub.xml")
    assert os.path.isfile(xml_path)
    tree = ET.parse(xml_path)
    root = tree.getroot()
    assert root.tag == "rss"
    channel = root.find("channel")
    assert channel is not None
    items = channel.findall("item")
    assert len(items) == 1


def test_sorts_by_timestamp_desc(tmp_path, make_info_json, base_sub, base_config):
    make_info_json(
        overrides={"upload_date": "20240101", "id": "old1", "title": "Old"},
        basename="Old [old1][20240101]",
    )
    make_info_json(
        overrides={"upload_date": "20250601", "id": "new1", "title": "New"},
        basename="New [new1][20250601]",
    )
    sub = _setup_sub(tmp_path, make_info_json, base_sub, base_config)
    write_xml(base_config, sub)

    xml_path = os.path.join(str(tmp_path), "testsub.xml")
    tree = ET.parse(xml_path)
    ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
    items = tree.getroot().find("channel").findall("item")
    assert len(items) == 2
    titles = [item.find("title").text for item in items]
    assert titles[0] == "New"
    assert titles[1] == "Old"


def test_audio_media_type(tmp_path, make_info_json, base_sub, base_config):
    make_info_json(overrides={"ext": "mp3", "format": "audio only", "acodec": "mp3"})
    mp3_path = tmp_path / "testsub" / "Test Video [abc123][20250101].mp3"
    mp3_path.write_bytes(b"")
    sub = _setup_sub(tmp_path, make_info_json, base_sub, base_config, audio_only=True)
    write_xml(base_config, sub)

    xml_path = os.path.join(str(tmp_path), "testsub.xml")
    tree = ET.parse(xml_path)
    enclosure = tree.getroot().find("channel").find("item").find("enclosure")
    assert "audio/" in enclosure.get("type")


def test_style_disabled(tmp_path, make_info_json, base_sub, base_config):
    make_info_json()
    base_config["style_rss_feed"] = False
    sub = _setup_sub(tmp_path, make_info_json, base_sub, base_config)
    write_xml(base_config, sub)

    xml_path = os.path.join(str(tmp_path), "testsub.xml")
    with open(xml_path) as f:
        content = f.read()
    assert "xml-stylesheet" not in content


def test_style_enabled(tmp_path, make_info_json, base_sub, base_config):
    make_info_json()
    base_config["style_rss_feed"] = True
    sub = _setup_sub(tmp_path, make_info_json, base_sub, base_config)
    write_xml(base_config, sub)

    xml_path = os.path.join(str(tmp_path), "testsub.xml")
    with open(xml_path) as f:
        content = f.read()
    assert "xml-stylesheet" in content


def test_include_files_all(tmp_path, base_sub, base_config):
    sub_dir = tmp_path / "testsub"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "episode.mp4").write_bytes(b"data")
    (sub_dir / "skip.json").write_text("{}")

    sub = {**base_sub, "xml_include_files": "all"}
    write_xml(base_config, sub)

    xml_path = os.path.join(str(tmp_path), "testsub.xml")
    tree = ET.parse(xml_path)
    items = tree.getroot().find("channel").findall("item")
    assert len(items) == 1


def test_icon_url(tmp_path, make_info_json, base_sub, base_config):
    make_info_json()
    sub_dir = tmp_path / "testsub"
    (sub_dir / "icon.jpg").write_bytes(b"\xff\xd8\xff")

    sub = _setup_sub(tmp_path, make_info_json, base_sub, base_config)
    write_xml(base_config, sub)

    xml_path = os.path.join(str(tmp_path), "testsub.xml")
    with open(xml_path) as f:
        content = f.read()
    assert "itunes:image" in content
    assert "icon.jpg" in content
