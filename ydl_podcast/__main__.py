#! /usr/bin/env python3

import os
import sys
from collections import ChainMap

from . import load_config, write_xml, cleanup, download, sub_defaults, get_ydl_module


def main():
    argv = sys.argv
    config = load_config(argv[1] if len(argv) > 1 else "config.yaml")
    if not config:
        print("No valid configuration found.")
        return -1

    ydl_mod = get_ydl_module(config)

    for sub in config["subscriptions"]:
        sub = ChainMap(
            sub,
            {
                t: config[t]
                for t in config.keys()
                if t
                in ["output_dir", "url_root", "best", "format", "filename_template"]
            },
            sub_defaults,
        )
        if (
            "ydl_options" in sub
            and sub["ydl_options"] is not None
            and "ydl_options" in config
            and config["ydl_options"] is not None
        ):
            sub["ydl_options"] = {**config["ydl_options"], **sub["ydl_options"]}
        elif "ydl_options" in config and config["ydl_options"] is not None:
            sub["ydl_options"] = config["ydl_options"]
        elif "ydl_options" in sub and sub["ydl_options"] is None:
            sub["ydl_options"] = {}
        if (
            "name" not in sub
            or "url" not in sub
            or "output_dir" not in sub
            or "url_root" not in sub
        ):
            print("Skipping erroneous subscription")
            continue

        if (
            os.path.isdir(os.path.join(sub["output_dir"], sub["name"]))
            and sub["initialize"]
        ):
            sub["initialize"] = False

        download(ydl_mod, sub)

        if sub["retention_days"] is not None and not sub["initialize"]:
            cleanup(sub)

        write_xml(sub)


if __name__ == "__main__":
    sys.exit(main())
