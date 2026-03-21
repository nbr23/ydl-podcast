import os
import time
from datetime import date, timedelta

from ydl_podcast import cleanup


def _make_files(directory, names):
    os.makedirs(directory, exist_ok=True)
    paths = []
    for name in names:
        p = os.path.join(directory, name)
        with open(p, "w") as f:
            f.write("x")
        paths.append(p)
    return paths


def test_removes_old_files(tmp_path, base_sub):
    base_sub["retention_days"] = 7
    d = os.path.join(str(tmp_path), "testsub")
    paths = _make_files(d, ["old.mp4", "old.info.json"])
    old_time = time.time() - 30 * 86400
    for p in paths:
        os.utime(p, (old_time, old_time))
    deleted = cleanup(base_sub)
    assert len(deleted) == 2
    for p in paths:
        assert not os.path.exists(p)


def test_keeps_recent_files(tmp_path, base_sub):
    base_sub["retention_days"] = 7
    d = os.path.join(str(tmp_path), "testsub")
    _make_files(d, ["new.mp4"])
    deleted = cleanup(base_sub)
    assert deleted == []
    assert os.path.exists(os.path.join(d, "new.mp4"))


def test_mixed(tmp_path, base_sub):
    base_sub["retention_days"] = 7
    d = os.path.join(str(tmp_path), "testsub")
    _make_files(d, ["old.mp4", "new.mp4"])
    old_time = time.time() - 30 * 86400
    os.utime(os.path.join(d, "old.mp4"), (old_time, old_time))
    deleted = cleanup(base_sub)
    assert len(deleted) == 1
    assert not os.path.exists(os.path.join(d, "old.mp4"))
    assert os.path.exists(os.path.join(d, "new.mp4"))


def test_nonexistent_directory(tmp_path, base_sub):
    base_sub["name"] = "nonexistent"
    deleted = cleanup(base_sub)
    assert deleted == []
