import os
from collections import ChainMap

import yaml
import pytest

from ydl_podcast import sub_defaults, load_config


def _merge_sub(sub_dict, config_dict):
    sub = dict(ChainMap(
        sub_dict,
        {
            t: config_dict[t]
            for t in config_dict.keys()
            if t in ["output_dir", "url_root", "best", "format", "filename_template"]
        },
        sub_defaults,
    ))
    if (
        "ydl_options" in sub
        and sub["ydl_options"] is not None
        and "ydl_options" in config_dict
        and config_dict["ydl_options"] is not None
    ):
        sub["ydl_options"] = {**config_dict["ydl_options"], **sub["ydl_options"]}
    elif "ydl_options" in config_dict and config_dict["ydl_options"] is not None:
        sub["ydl_options"] = config_dict["ydl_options"]
    elif "ydl_options" in sub and sub["ydl_options"] is None:
        sub["ydl_options"] = {}
    return sub


def test_sub_overrides_global(base_config):
    base_config["retention_days"] = 30
    sub = _merge_sub({"name": "s", "retention_days": 7}, base_config)
    assert sub["retention_days"] == 7


def test_global_overrides_defaults(base_config):
    base_config["best"] = True
    sub = _merge_sub({"name": "s"}, base_config)
    assert sub["best"] is True


def test_defaults_apply(base_config):
    sub = _merge_sub({"name": "s"}, base_config)
    assert sub["quiet"] is True
    assert sub["audio_only"] is False


def test_ydl_options_merge_both(base_config):
    base_config["ydl_options"] = {"geo_bypass": True, "sleep_interval": 3}
    sub = _merge_sub(
        {"name": "s", "ydl_options": {"sleep_interval": 10, "retries": 5}},
        base_config,
    )
    assert sub["ydl_options"]["geo_bypass"] is True
    assert sub["ydl_options"]["sleep_interval"] == 10
    assert sub["ydl_options"]["retries"] == 5


def test_ydl_options_only_config(base_config):
    base_config["ydl_options"] = {"geo_bypass": True}
    sub = _merge_sub({"name": "s"}, base_config)
    assert sub["ydl_options"]["geo_bypass"] is True


def test_ydl_options_sub_none(base_config):
    sub = _merge_sub({"name": "s", "ydl_options": None}, base_config)
    assert sub["ydl_options"] == {}


def test_load_config_valid(tmp_path):
    cfg = {"output_dir": "/tmp", "subscriptions": []}
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(cfg))
    result = load_config(str(p))
    assert result["output_dir"] == "/tmp"


def test_load_config_missing(tmp_path):
    result = load_config(str(tmp_path / "nonexistent.yaml"))
    assert result == {}
