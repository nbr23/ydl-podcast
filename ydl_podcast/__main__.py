#! /usr/bin/env python3

import os
import sys
from importlib.metadata import version
from collections import ChainMap
import argparse
import json

from . import load_config, write_xml, cleanup, download, sub_defaults, get_ydl_module, write_sub_nfo


def main():
    parser = argparse.ArgumentParser(description="ydl-podcast")
    parser.add_argument("-v", "--version", help="Show version and exit", action='store_true')
    parser.add_argument("-c", "--config", help="Configuration file", type=str, default="config.yaml")
    parser.add_argument("-j", "--json-config", help="Configuration string in JSON format", type=str, default="{}")
    print(f"ydl-podcast v{version('ydl-podcast')}")
    args = parser.parse_args()
    if args.version:
        return 0

    config = load_config(args.config)
    config = {**config, **json.loads(args.json_config)}

    if config is None or len(config.keys()) == 0:
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
            or (
                (
                    "url" not in sub
                    or "output_dir" not in sub
                    or "url_root" not in sub
                )
                and not sub.get("skip_download", False)
            )
        ):
            print("Skipping erroneous subscription")
            continue

        if (
            os.path.isdir(os.path.join(sub["output_dir"], sub["name"]))
            and sub["initialize"]
        ):
            sub["initialize"] = False

        if not sub.get("skip_download", False):
            download(ydl_mod, sub)

        if sub["retention_days"] is not None and not sub["initialize"]:
            cleanup(sub)

        write_sub_nfo(sub)
        write_xml(sub)


if __name__ == "__main__":
    sys.exit(main())
