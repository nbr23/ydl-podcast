#! /usr/bin/env python3

import os
import sys
from importlib.metadata import version
from collections import ChainMap
import argparse
import json
from jinja2 import Template
from ydl_podcast.templates.index import INDEX_HTML_TMPL
from ydl_podcast.templates.style import FEED_STYLE_TMPL

from . import load_config, write_xml, cleanup, download, sub_defaults, get_ydl_module, write_sub_nfo


def main():
    parser = argparse.ArgumentParser(description="A simple tool to generate Podcast-like RSS feeds from youtube (or other youtube-dl supported services) channels, using youtube-dl/yt-dlp")
    parser.add_argument("-v", "--version", help="Show version and exit", action='store_true')
    parser.add_argument("-c", "--config", help="Configuration file", type=str, default="config.yaml")
    parser.add_argument("-j", "--json-config", help="Configuration string in JSON format", type=str, default="{}")
    parser.add_argument("-f", "--filter", help="Filter subscriptions", type=str, default=None)
    parser.add_argument("-e", "--exclude", help="Exclude subscriptions", type=str, default=None)
    print(f"ydl-podcast v{version('ydl-podcast')}")
    args = parser.parse_args()
    if args.version:
        return 0

    config = load_config(args.config)
    config = {**config, **json.loads(args.json_config)}

    if config is None or len(config.keys()) == 0:
        print("No valid configuration found.")
        return -1

    # print("Using configuration:", config)
    ydl_mod = get_ydl_module(config)

    if args.filter is not None:
        args.filter = args.filter.split(",")
    args.exclude = args.exclude.split(",") if args.exclude is not None else []


    if config.get("style_rss_feed", True):
        if not os.path.exists(config["output_dir"]):
            print("Creating output directory")
            os.makedirs(config["output_dir"])
        with open(os.path.join(config["output_dir"], "style.xsl"), "w") as fout:
            print("Writing style.xsl")
            fout.write(FEED_STYLE_TMPL)

    for sub in config["subscriptions"]:
        if args.filter is not None and sub["name"] not in args.filter or sub["name"] in args.exclude:
            print("Skipping subscription", sub["name"])
            continue
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
        write_xml(config, sub)

    if config.get("index_enabled", False):
        index_path = os.path.join(config["output_dir"], "index.html")
        with open(index_path, "w") as fout:
            print("Writing ", index_path)
            fout.write(Template(INDEX_HTML_TMPL).render({
                'subscriptions': [sub for sub in config["subscriptions"] if not sub.get("private", False)]
                }))


if __name__ == "__main__":
    sys.exit(main())
