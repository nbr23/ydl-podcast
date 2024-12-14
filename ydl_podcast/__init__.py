import os
import io
import glob
import yaml
from urllib.parse import quote
import json
import datetime
from datetime import date, timedelta
import importlib
from jinja2 import Template
from urllib.parse import urljoin
from PIL import Image

from .templates.episode_nfo import EPISODE_NFO_TMPL
from .templates.show_nfo import SHOW_NFO_TMPL
from .templates.feed import FEED_TMPL

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
    config = {}
    if not os.path.isfile(config_path):
        print("Config file '%s' not found." % config_path)
        return {}
    with open(config_path) as configfile:
        config = yaml.load(configfile, Loader=yaml.SafeLoader)
    return config


def metadata_file_extension(metadata, data_path, basename):
    ext = None
    if "audio only" in metadata["format"] and os.path.isfile(
        os.path.join(data_path, "%s.%s" % (basename, metadata.get("acodec", metadata.get("audio_ext"))))
    ):
        ext = metadata.get("acodec", metadata.get("audio_ext"))
    if ext is not None:
        return ext
    ext = metadata["ext"]
    if ext is None:
        raise Exception("No extension found")
    return ext

def get_real_thumbnail_ext(metadata_path, default_ext):
    path = os.path.dirname(metadata_path)
    basename = ".".join(os.path.basename(metadata_path).split(".")[:-2])
    extensions = [default_ext, "jpg", "jpeg", "png", "webp"]
    for ext in extensions:
        if os.path.isfile(os.path.join(path, "%s.%s" % (basename, ext))):
            return ext
    return default_ext


def convert_thumbnail_to_jpg(path, thumbnail_filename):
    ext = thumbnail_filename.split(".")[-1]
    if ext == "jpg" or ext == "jpeg":
        return thumbnail_filename
    try:
        print("Converting thumbnail to jpg", thumbnail_filename)
        im = Image.open(os.path.join(path, thumbnail_filename))
        rgb_im = im.convert("RGB")
        new_thumbnail_filename = thumbnail_filename.replace("."+ext, ".jpg")
        rgb_im.save(os.path.join(path, new_thumbnail_filename))
        # os.remove(os.path.join(path, thumbnail_filename))
        return new_thumbnail_filename
    except Exception as e:
        print("Error converting thumbnail to jpg: %s" % e)
        return thumbnail_filename

def metadata_parse(metadata_path):
    with open(metadata_path) as metadata:
        mdjs = json.load(metadata)
        if mdjs.get("_type") == "playlist":
            return
        basename = ".".join(os.path.basename(metadata_path).split(".")[:-2])
        path = os.path.dirname(metadata_path)
        thumbnail_file = None
        if mdjs.get("thumbnail") is not None:
            thumb_ext = get_real_thumbnail_ext(metadata_path, mdjs["thumbnail"].split(".")[-1])
            thumbnail_file = convert_thumbnail_to_jpg(path, "%s.%s" % (basename, thumb_ext))
        extension = metadata_file_extension(mdjs, path, basename)
        if not os.path.isfile(os.path.join(path, "%s.%s" % (basename, extension))):
            with os.scandir(path) as directory:
                for f in directory:
                    ext = f.name.split(".")[-1]
                    if (
                        f.name.startswith(basename)
                        and ext not in ["json", "jpg", "webp", "meta"]
                        and (mdjs.get("thumbnail") is None or ext != thumb_ext)
                    ):
                        extension = ext
                        break
        return {
            "title": mdjs["title"],
            "id": mdjs["id"],
            "timestamp": datetime.datetime.strptime(
                mdjs["upload_date"], "%Y%m%d"
            ).timestamp(),
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

def flatten_entries(metadata, entries):
    for entry in metadata.get("entries", []):
        if entry.get("_type") == "playlist":
            flatten_entries(entry, entries)
        else:
            entries.append(entry)

def download(ydl_mod, sub):
    downloaded = []
    options = process_options(ydl_mod, sub)
    metadata = get_metadata(ydl_mod, sub["url"], options, sub["quiet"])

    if metadata is None:
        print("No metadata found for %s" % sub["name"])
        return

    entries = []
    flatten_entries(metadata, entries)

    # Handle podcast icon
    get_podcast_icon(ydl_mod, sub, metadata)

    # Filter out older entries
    if sub["download_last"] is not None and not sub.get("initialize", False):
        entries = entries[: sub["download_last"]]

    # Generic extractor should be handled differently
    if metadata.get("_type") == "playlist" and (metadata.get("extractor") == "generic" or sub.get("download_as_playlist", False)):
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
                ydl.download([sub["url"]])
            except ydl_mod.utils.YoutubeDLError as e:
                if not sub["quiet"]:
                    print(e)
        return {}

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
                                for fmt in entry.get("formats", [])
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
    print("Writing NFO files for %s" % sub["name"])

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
        if md is None:
            continue
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


def write_xml(config, sub):
    mds = [
        metadata_parse(md_file)
        for md_file in glob.glob(
            os.path.join(sub["output_dir"], "%s/*.info.json" % sub["name"])
        )
    ]

    tmpl_args = {
        "last_update": datetime.datetime.now(),
        "channel_title": sub["name"],
        "channel_link": sub["url"],
        "style_rss_feed": config.get("style_rss_feed", True),
        "items": [
            {
                "id": md["id"],
                "title": md["title"],
                "url": "/".join(
                    [sub["url_root"], quote(sub["name"]), quote(md["filename"])]
                ),
                "media_type": ("audio/%s" % md["extension"])
                if sub["audio_only"]
                else "video/%s" % md["extension"],
                "pubDate": md["pub_date"],
                "timestamp": md["timestamp"],
                "thumbnail": "/".join([
                    sub["url_root"],
                    quote(sub["name"]),
                    quote(convert_thumbnail_to_jpg(
                        os.path.join(sub["url_root"], sub["name"]),
                        md["thumbnail"]
                    ))
                ]) if md.get("thumbnail") is not None else None,
                "description": md["description"],
                "duration": md["duration"],
            }
            for md in mds if md
        ],
    }
    tmpl_args["items"].sort(key=lambda x: x["timestamp"], reverse=True)

    icon_path = os.path.join(sub["output_dir"], sub["name"], 'icon.jpg')
    if os.path.isfile(icon_path):
        tmpl_args["icon_url"] = "/".join(
            [sub["url_root"], quote(sub["name"]), quote('icon.jpg')]
        )

    with open("%s.xml" % os.path.join(sub["output_dir"], sub["name"]), "w") as fout:
        fout.write(Template(FEED_TMPL).render(**tmpl_args))


def get_ydl_module(config):
    m = config.get("youtube-dl-module")
    if m is None:
        try:
            return importlib.import_module("youtube_dl")
        except ModuleNotFoundError:
            return importlib.import_module("yt_dlp")
    return importlib.import_module(m.replace("-", "_"))
