import os

from ydl_podcast import write_sub_nfo


def test_creates_tvshow_nfo(tmp_path, make_info_json, base_sub):
    make_info_json()
    base_sub["nfo_files"] = True
    write_sub_nfo(base_sub)

    nfo_path = os.path.join(str(tmp_path), "testsub", "tvshow.nfo")
    assert os.path.isfile(nfo_path)
    with open(nfo_path) as f:
        content = f.read()
    assert "testsub" in content


def test_creates_episode_nfo(tmp_path, make_info_json, base_sub):
    make_info_json()
    base_sub["nfo_files"] = True
    write_sub_nfo(base_sub)

    nfo_files = [f for f in os.listdir(os.path.join(str(tmp_path), "testsub")) if f.endswith(".nfo") and f != "tvshow.nfo"]
    assert len(nfo_files) == 1
    with open(os.path.join(str(tmp_path), "testsub", nfo_files[0])) as f:
        content = f.read()
    assert "Test Video" in content


def test_skips_audio_only(tmp_path, make_info_json, base_sub):
    make_info_json()
    base_sub["nfo_files"] = True
    base_sub["audio_only"] = True
    write_sub_nfo(base_sub)

    nfo_path = os.path.join(str(tmp_path), "testsub", "tvshow.nfo")
    assert not os.path.isfile(nfo_path)


def test_skips_when_disabled(tmp_path, make_info_json, base_sub):
    make_info_json()
    base_sub["nfo_files"] = False
    write_sub_nfo(base_sub)

    nfo_path = os.path.join(str(tmp_path), "testsub", "tvshow.nfo")
    assert not os.path.isfile(nfo_path)


def test_does_not_overwrite(tmp_path, make_info_json, base_sub):
    make_info_json()
    sub_dir = os.path.join(str(tmp_path), "testsub")
    nfo_path = os.path.join(sub_dir, "tvshow.nfo")
    with open(nfo_path, "w") as f:
        f.write("ORIGINAL CONTENT")

    base_sub["nfo_files"] = True
    write_sub_nfo(base_sub)

    with open(nfo_path) as f:
        assert f.read() == "ORIGINAL CONTENT"
