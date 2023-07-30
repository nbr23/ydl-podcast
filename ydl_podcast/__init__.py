import os
import io
import glob
import yaml
import html
from urllib.parse import quote
import json
import datetime
from datetime import date, timedelta
import importlib
from jinja2 import Template
from urllib.parse import urljoin

from .template import ATOM_TMPL, SHOW_NFO_TMPL, EPISODE_NFO_TMPL

sub_defaults = {
    "retention_days": None,
    "audio_only": False,
    "download_last": None,
    "initialize": False,
    "best": False,
    "ignore_errors": False,
    "quiet": True,
    "filename_template": "%(title)s [%(id)s][%(upload_date)s].%(ext)s",
}


def load_config(config_path):
    config = None
    if not os.path.isfile(config_path):
        print("Config file '%s' not found." % config_path)
        return None
    with open(config_path) as configfile:
        config = yaml.load(configfile, Loader=yaml.SafeLoader)
    return config


def metadata_file_extension(metadata, data_path, basename):
    if "audio only" in metadata["format"] and os.path.isfile(
        os.path.join(data_path, "%s.%s" % (basename, metadata["acodec"]))
    ):
        return metadata["acodec"]
    return metadata["ext"]

def get_real_thumbnail_ext(metadata_path, default_ext):
    path = os.path.dirname(metadata_path)
    basename = ".".join(os.path.basename(metadata_path).split(".")[:-2])
    extensions = [default_ext, "jpg", "jpeg", "png", "webp"]
    for ext in extensions:
        if os.path.isfile(os.path.join(path, "%s.%s" % (basename, ext))):
            return ext
    return default_ext


def metadata_parse(metadata_path):
    with open(metadata_path) as metadata:
        mdjs = json.load(metadata)
        basename = ".".join(os.path.basename(metadata_path).split(".")[:-2])
        path = os.path.dirname(metadata_path)
        thumbnail_file = None
        if mdjs.get("thumbnail") is not None:
            thumb_ext = get_real_thumbnail_ext(metadata_path, mdjs["thumbnail"].split(".")[-1])
            thumbnail_file = "%s.%s" % (basename, thumb_ext)
        extension = metadata_file_extension(mdjs, path, basename)
        if not os.path.isfile(os.path.join(path, "%s.%s" % (basename, extension))):
            with os.scandir(path) as directory:
                for f in directory:
                    ext = f.name.split(".")[-1]
                    if (
                        f.name.startswith(basename)
                        and ext != "json"
                        and (mdjs.get("thumbnail") is None or ext != thumb_ext)
                    ):
                        extension = ext
                        break
        return {
            "title": mdjs["title"],
            "id": mdjs["id"],
            "pub_date": datetime.datetime.strptime(
                mdjs["upload_date"], "%Y%m%d"
            ).strftime("%a, %d %b %Y %H:%M:%S +0000")
            if mdjs.get("upload_date") is not None
            else None,
            "extension": extension,
            "description": mdjs.get("description"),
            "thumbnail": thumbnail_file,
            "filename": "%s.%s" % (basename, extension),
            "duration": str(datetime.timedelta(seconds=mdjs["duration"]))
            if mdjs.get("duration") is not None
            else None,
        }


def get_metadata(ydl_mod, url, options, quiet=True):
    my_options = options.copy()
    my_options.update(
        {
            "quiet": quiet,
            "simulate": True,
            "ignoreerrors": True,
            "dump_single_json": True,
            "extract_flat": "in_playlist",
        }
    )
    output = io.StringIO()
    with ydl_mod.YoutubeDL(my_options) as ydl:
        try:
            if hasattr(ydl, "_out_files"):
                ydl._out_files.out = output
            else:
                ydl._screen_file = output
            if quiet:
                if hasattr(ydl, "_out_files"):
                    ydl._out_files.error = io.StringIO()
                else:
                    ydl._err_file = io.StringIO()
            ydl.download([url])
        except ydl_mod.utils.YoutubeDLError as e:
            if not quiet:
                print(e)

    return json.loads(output.getvalue())


def get_video_metadata(ydl_mod, url, options, quiet=True):
    my_options = options.copy()
    my_options.update(
        {
        "quiet": quiet,
        "simulate": True,
        "forcejson": True,
        "ignoreerrors": True,
        "extract_flat": "in_playlist",
        }
    )
    output = io.StringIO()
    with ydl_mod.YoutubeDL(my_options) as ydl:
        try:
            if hasattr(ydl, "_out_files"):
                ydl._out_files.out = output
            else:
                ydl._screen_file = output
            if quiet:
                if hasattr(ydl, "_out_files"):
                    ydl._out_files.error = io.StringIO()
                else:
                    ydl._err_file = io.StringIO()
            ydl.download([url])
        except ydl_mod.utils.YoutubeDLError as e:
            if not quiet:
                print(e)
    md = output.getvalue().split("\n")[0]
    if len(md) == 0:
        return None
    return json.loads(md)

def process_options(ydl_mod, sub):
    options = {
        "outtmpl": os.path.join(
            sub["output_dir"], sub["name"], sub["filename_template"]
        ),
        "writeinfojson": True,
        "writethumbnail": True,
        "ignoreerrors": sub["ignore_errors"],
        "youtube_include_dash_manifest": True,
        "matchtitle": sub.get("matchtitle", None),
    }
    if sub["retention_days"] is not None and not sub["initialize"]:
        options["daterange"] = ydl_mod.utils.DateRange(
            (date.today() - timedelta(days=sub["retention_days"])).strftime("%Y%m%d"),
            "99991231",
        )
    if sub["download_last"] is not None and not sub["initialize"]:
        options["max_downloads"] = sub["download_last"]
    if sub["initialize"]:
        options["playlistreverse"] = True
    if sub["audio_only"]:
        options["format"] = "bestaudio/%s" % sub.get("format", "best")
        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": sub.get("format", "best"),
                "preferredquality": "5",
                "nopostoverwrites": False,
            }
        ]
    elif "format" in sub:
        if sub["best"]:
            options["format"] = "bestvideo[ext=%s]" % sub["format"]
        else:
            options["format"] = sub["format"]

    for key in sub.get("ydl_options", {}):
        options[key] = sub["ydl_options"][key]

    return options

def get_podcast_icon(ydl_mod, sub, metadata):
    # check if it already exists
    icon_filepath = os.path.join(sub["output_dir"], sub["name"], "icon.jpg")
    if os.path.isfile(icon_filepath):
        return

    # get the channel's about  metadata
    channel_url = metadata.get("uploader_url")
    if channel_url is None:
        return
    options =  {
        "quiet": False,
        "ignoreerrors": True,
        "extract_flat": "in_playlist",
        "writethumbnail": True,
        "filename_template": "icon.jpg",
        "outtmpl": os.path.join(
            sub["output_dir"], sub["name"], 'icon.jpg'
        ),
        "writeinfojson": False,
    }

    output = io.StringIO()
    with ydl_mod.YoutubeDL(options) as ydl:
        try:
            if hasattr(ydl, "_out_files"):
                ydl._out_files.out = output
                ydl._out_files.error = io.StringIO()
            else:
                ydl._screen_file = output
                ydl._err_file = io.StringIO()
            ydl.download(['/'.join([channel_url, 'about'])])
        except ydl_mod.utils.YoutubeDLError:
            pass


def download(ydl_mod, sub):
    downloaded = []
    options = process_options(ydl_mod, sub)
    metadata = get_metadata(ydl_mod, sub["url"], options, sub["quiet"])

    if metadata is None:
        print("No metadata found for %s" % sub["name"])
        return
    entries = metadata.get("entries", [])

    # Handle podcast icon
    get_podcast_icon(ydl_mod, sub, metadata)

    # Filter out older entries
    if sub["download_last"] is not None and not sub.get("initialize", False):
        entries = entries[: sub["download_last"]]

    # Go through entries and download them
    for i, md in enumerate(entries):
        entry = get_video_metadata(ydl_mod, md["url"], options, quiet=True)
        if entry is None:
            if not sub["quiet"]:
                print("No metadata found for %s, skipping (likely due to the video upload date being out of range)" % md["url"])
            continue
        mdfile_name = "%s.meta" % ".".join(entry["_filename"].split(".")[:-1])
        if not os.path.isfile(mdfile_name) and not entry.get("is_live", False):
            with ydl_mod.YoutubeDL(options) as ydl:
                if sub["quiet"]:
                    ydl._screen_file = io.StringIO()
                    if ydl._out_files is not None:
                        ydl._out_files.out = io.StringIO()
                        ydl._out_files.error = ydl._out_files.out
                    else:
                        ydl._screen_file = io.StringIO()
                        ydl._err_file = ydl._screen_file
                if sub["quiet"]:
                    if ydl._out_files is not None:
                        ydl._out_files.error = io.StringIO()
                    else:
                        ydl._err_file = io.StringIO()

                try:
                    ydl.download([entry["webpage_url"]])
                except ydl_mod.utils.YoutubeDLError as e:
                    if not sub["quiet"]:
                        print(e)
                    continue
                with open(mdfile_name, "w+") as f:
                    entry.update(
                        {
                            "subscription_name": sub["name"],
                            "formats": [
                                fmt
                                for fmt in entry.get("formats")
                                if (
                                    options.get("format") is None
                                    or (fmt.get("format") == options.get("format"))
                                )
                            ],
                        }
                    )
                    downloaded.append(entry)
        elif entry.get("is_live", False) and not sub["quiet"]:
            print(
                "Skipping ongoing live {} - {}".format(
                    entry.get("id"), entry.get("title")
                )
            )
        elif not sub["quiet"]:
            print(
                "Skipping already retrieved {} - {}".format(
                    entry.get("id"), entry.get("title")
                )
            )
            if sub["download_last"] is not None and i > sub["download_last"]:
                break
    return downloaded


def cleanup(sub):
    deleted = []
    directory = os.path.join(sub["output_dir"], sub["name"])
    if not os.path.isdir(directory):
        return deleted
    for f in os.listdir(directory):
        fpath = os.path.join(directory, f)
        mtime = date.fromtimestamp(os.path.getmtime(fpath))
        ret = date.today() - timedelta(days=sub["retention_days"])
        if mtime < ret:
            os.remove(fpath)
            deleted.append(fpath)
    return deleted


def write_sub_nfo(sub):
    if not sub.get('nfo_files', False) or sub.get("audio_only", False):
        return
    nso_file = os.path.join(sub["output_dir"], sub["name"], "tvshow.nfo")
    sub_nfo_tmpl = SHOW_NFO_TMPL
    episode_nfo_tmpl = EPISODE_NFO_TMPL

    if not os.path.exists(nso_file):
        with open(nso_file, "w+") as fout:
            fout.write(Template(sub_nfo_tmpl).render({
                "title": sub.get("pretty_name", sub["name"])
            }))

    mds = [
        metadata_parse(md_file)
        for md_file in glob.glob(
            os.path.join(sub["output_dir"], "%s/*.info.json" % sub["name"])
        )
    ]

    for md in mds:
        nfo_file = os.path.join(sub["output_dir"], sub["name"], "%s.nfo" % ".".join(md["filename"].split(".")[:-1]))
        ep_date = datetime.datetime.strptime(md["pub_date"], "%a, %d %b %Y %H:%M:%S +0000").strftime("%Y-%m-%d")
        if not os.path.exists(nfo_file):
            with open(nfo_file, "w+") as fout:
                fout.write(Template(EPISODE_NFO_TMPL).render({
                    "title": md["title"],
                    "ep_date": ep_date,
                    "show_title": sub.get("pretty_name", sub["name"]),
                    "duration": md["duration"],
                }))


def write_xml(sub):
    mds = [
        metadata_parse(md_file)
        for md_file in glob.glob(
            os.path.join(sub["output_dir"], "%s/*.info.json" % sub["name"])
        )
    ]

    tmpl_args = {
        "last_update": datetime.datetime.now(),
        "channel_title": sub["name"],
        "channel_link": "/".join([sub["url_root"], "%s.xml" % sub["name"]]),
        "items": [
            {
                "id": html.escape(md["id"]),
                "title": html.escape(md["title"]),
                "url": "/".join(
                    [sub["url_root"], quote(sub["name"]), quote(md["filename"])]
                ),
                "media_type": ("audio/%s" % md["extension"])
                if sub["audio_only"]
                else "video/%s" % md["extension"],
                "pubDate": md["pub_date"],
                "thumbnail": "/".join(
                    [sub["url_root"], quote(sub["name"]), quote(md["thumbnail"])]
                )
                if md.get("thumbnail") is not None
                else None,
                "description": md["description"],
                "duration": md["duration"],
            }
            for md in mds
        ],
    }

    icon_path = os.path.join(sub["output_dir"], sub["name"], 'icon.jpg')
    if os.path.isfile(icon_path):
        tmpl_args["icon_url"] = "/".join(
            [sub["url_root"], quote(sub["name"]), quote('icon.jpg')]
        )

    with open("%s.xml" % os.path.join(sub["output_dir"], sub["name"]), "w") as fout:
        fout.write(Template(ATOM_TMPL).render(**tmpl_args))


def get_ydl_module(config):
    return importlib.import_module(
        config.get("youtube-dl-module", "youtube_dl").replace("-", "_")
    )
