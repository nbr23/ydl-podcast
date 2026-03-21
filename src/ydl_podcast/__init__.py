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


def sub_dir(sub, *parts):
    return os.path.join(sub["output_dir"], sub["name"], *parts)


def sub_url(sub, filename):
    return "/".join([sub["url_root"], quote(sub["name"]), quote(filename)])


def strip_info_json_ext(path):
    return ".".join(os.path.basename(path).split(".")[:-2])


def silence_ydl(ydl, output=None, quiet=True):
    if output is not None:
        if hasattr(ydl, "_out_files"):
            ydl._out_files.out = output
        else:
            ydl._screen_file = output
    if quiet:
        if hasattr(ydl, "_out_files"):
            if output is None:
                ydl._out_files.out = io.StringIO()
            ydl._out_files.error = io.StringIO()
        else:
            if output is None:
                ydl._screen_file = io.StringIO()
            ydl._err_file = io.StringIO()


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
    basename = strip_info_json_ext(metadata_path)
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
        new_thumbnail_filename = thumbnail_filename.replace("."+ext, ".jpg")
        with Image.open(os.path.join(path, thumbnail_filename)) as im:
            rgb_im = im.convert("RGB")
            rgb_im.save(os.path.join(path, new_thumbnail_filename))
        return new_thumbnail_filename
    except Exception as e:
        print("Error converting thumbnail to jpg: %s" % e)
        return thumbnail_filename

def metadata_parse(metadata_path):
    with open(metadata_path) as metadata:
        mdjs = json.load(metadata)
        if mdjs.get("_type") == "playlist":
            return
        if mdjs.get("upload_date") is None:
            return
        basename = strip_info_json_ext(metadata_path)
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
        upload_dt = datetime.datetime.strptime(mdjs["upload_date"], "%Y%m%d")
        return {
            "title": mdjs["title"],
            "id": mdjs["id"],
            "timestamp": upload_dt.timestamp(),
            "pub_date": upload_dt.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "extension": extension,
            "description": mdjs.get("description"),
            "thumbnail": thumbnail_file,
            "filename": "%s.%s" % (basename, extension),
            "duration": str(datetime.timedelta(seconds=mdjs["duration"]))
            if mdjs.get("duration") is not None
            else None,
        }


def get_metadata(ydl_mod, url, options, quiet=True, single_json=True):
    my_options = options.copy()
    extra = {"dump_single_json": True} if single_json else {"forcejson": True}
    my_options.update(
        {
            "quiet": quiet,
            "simulate": True,
            "ignoreerrors": True,
            "extract_flat": "in_playlist",
            **extra,
        }
    )
    output = io.StringIO()
    with ydl_mod.YoutubeDL(my_options) as ydl:
        try:
            silence_ydl(ydl, output=output, quiet=quiet)
            ydl.download([url])
        except ydl_mod.utils.YoutubeDLError as e:
            if not quiet:
                print(e)

    result = output.getvalue()
    if not single_json:
        result = result.split("\n")[0]
        if len(result) == 0:
            return None
    return json.loads(result)


def process_options(ydl_mod, sub):
    options = {
        "outtmpl": sub_dir(sub, sub["filename_template"]),
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
    icon_filepath = sub_dir(sub, "icon.jpg")
    if os.path.isfile(icon_filepath):
        return

    channel_url = metadata.get("uploader_url")
    if channel_url is None:
        return
    options =  {
        "quiet": False,
        "ignoreerrors": True,
        "extract_flat": "in_playlist",
        "writethumbnail": True,
        "filename_template": "icon.jpg",
        "outtmpl": sub_dir(sub, "icon.jpg"),
        "writeinfojson": False,
    }

    with ydl_mod.YoutubeDL(options) as ydl:
        try:
            silence_ydl(ydl, quiet=True)
            ydl.download(['/'.join([channel_url, 'about'])])
        except ydl_mod.utils.YoutubeDLError:
            pass

def flatten_entries(metadata, entries):
    for entry in metadata.get("entries", []):
        if entry.get("_type") == "playlist":
            flatten_entries(entry, entries)
        else:
            entries.append(entry)


def _download_with_ydl(ydl_mod, options, url, quiet):
    with ydl_mod.YoutubeDL(options) as ydl:
        if quiet:
            silence_ydl(ydl, quiet=True)
        try:
            ydl.download([url])
        except ydl_mod.utils.YoutubeDLError as e:
            if not quiet:
                print(e)
            return False
    return True


def download(ydl_mod, sub):
    downloaded = []
    options = process_options(ydl_mod, sub)
    metadata = get_metadata(ydl_mod, sub["url"], options, sub["quiet"])

    if metadata is None:
        print("No metadata found for %s" % sub["name"])
        return

    entries = []
    flatten_entries(metadata, entries)

    get_podcast_icon(ydl_mod, sub, metadata)

    if sub["download_last"] is not None and not sub.get("initialize", False):
        entries = entries[: sub["download_last"]]

    if metadata.get("_type") == "playlist" and (metadata.get("extractor") == "generic" or sub.get("download_as_playlist", False)):
        _download_with_ydl(ydl_mod, options, sub["url"], sub["quiet"])
        return {}

    for i, md in enumerate(entries):
        entry = get_metadata(ydl_mod, md["url"], options, quiet=True, single_json=False)
        if entry is None:
            if not sub["quiet"]:
                print("No metadata found for %s, skipping (likely due to the video upload date being out of range)" % md["url"])
            continue
        mdfile_name = "%s.meta" % ".".join(entry["_filename"].split(".")[:-1])
        if not os.path.isfile(mdfile_name) and not entry.get("is_live", False):
            if not _download_with_ydl(ydl_mod, options, entry["webpage_url"], sub["quiet"]):
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
    directory = sub_dir(sub)
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

    nso_file = sub_dir(sub, "tvshow.nfo")
    pretty_name = sub.get("pretty_name", sub["name"])

    if not os.path.exists(nso_file):
        with open(nso_file, "w+") as fout:
            fout.write(Template(SHOW_NFO_TMPL).render({
                "title": pretty_name
            }))

    info_json_glob = sub_dir(sub, "*.info.json")
    mds = [
        metadata_parse(md_file)
        for md_file in glob.glob(info_json_glob)
    ]

    for md in mds:
        if md is None:
            continue
        nfo_file = sub_dir(sub, "%s.nfo" % ".".join(md["filename"].split(".")[:-1]))
        ep_date = datetime.datetime.strptime(md["pub_date"], "%a, %d %b %Y %H:%M:%S +0000").strftime("%Y-%m-%d")
        if not os.path.exists(nfo_file):
            with open(nfo_file, "w+") as fout:
                fout.write(Template(EPISODE_NFO_TMPL).render({
                    "title": md["title"],
                    "ep_date": ep_date,
                    "show_title": pretty_name,
                    "duration": md["duration"],
                }))


def write_xml(config, sub):
    if sub.get("xml_include_files") == 'all':
        mds = [
            {
                "id": os.path.basename(f),
                "title": '.'.join(os.path.basename(f).split('.')[:-1]),
                "filename":  os.path.basename(f),
                "extension": os.path.basename(f).split('.')[-1],
                "pub_date": date.fromtimestamp(os.path.getmtime(f)),
                "timestamp": date.fromtimestamp(os.path.getmtime(f)),
            }
            for f in glob.glob(
                sub_dir(sub, "*.*")
            ) if os.path.basename(f).split('.')[-1] not in ["json", "jpg", "webp", "meta", "part", "ytdl"]
        ]
    else:
        mds = [
            metadata_parse(md_file)
            for md_file in glob.glob(sub_dir(sub, "*.info.json"))
        ]

    tmpl_args = {
        "last_update": datetime.datetime.now(),
        "channel_title": sub["name"],
        "channel_link": sub.get("url", ""),
        "style_rss_feed": config.get("style_rss_feed", True),
        "items": [
            {
                "id": md["id"],
                "title": md["title"],
                "url": sub_url(sub, md["filename"]),
                "media_type": ("audio/%s" % md["extension"])
                if sub["audio_only"]
                else "video/%s" % md["extension"],
                "pubDate": md["pub_date"],
                "timestamp": md["timestamp"],
                "thumbnail": sub_url(sub, convert_thumbnail_to_jpg(
                    os.path.join(sub["url_root"], sub["name"]),
                    md["thumbnail"]
                )) if md.get("thumbnail") is not None else None,
                "description": md.get("description", None),
                "duration": md.get("duration", None),
            }
            for md in mds if md
        ],
    }
    tmpl_args["items"].sort(key=lambda x: x["timestamp"], reverse=True)

    icon_path = sub_dir(sub, "icon.jpg")
    if os.path.isfile(icon_path):
        tmpl_args["icon_url"] = sub_url(sub, "icon.jpg")

    with open("%s.xml" % sub_dir(sub), "w") as fout:
        fout.write(Template(FEED_TMPL).render(**tmpl_args))


def get_ydl_module(config):
    m = config.get("youtube-dl-module")
    if m is None:
        try:
            return importlib.import_module("youtube_dl")
        except ModuleNotFoundError:
            return importlib.import_module("yt_dlp")
    return importlib.import_module(m.replace("-", "_"))
