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

sub_defaults = {
        'retention_days': None,
        'audio_only': False,
        'download_last': None,
        'initialize': False,
        'best': False,
        'ignore_errors': False,
        'quiet': False,
        'filename_template': '%(title)s [%(id)s][%(upload_date)s].%(ext)s',
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
    if ('audio only' in metadata['format'] and
            os.path.isfile(os.path.join(
                data_path,
                '%s.%s' % (basename, metadata['acodec'])))):
        return metadata['acodec']
    return metadata['ext']

def metadata_parse(metadata_path):
    with open(metadata_path) as metadata:
        mdjs = json.load(metadata)
        basename = '.'.join(os.path.basename(metadata_path).split('.')[:-2])
        path = os.path.dirname(metadata_path)
        thumb_ext = mdjs['thumbnail'].split('.')[-1]
        thumbnail_file = '%s.%s' % (basename, thumb_ext)
        extension = metadata_file_extension(mdjs, path, basename)
        if not os.path.isfile(os.path.join(path,
                                           '%s.%s' % (basename, extension))):
            with os.scandir(path) as directory:
                for f in directory:
                    ext = f.name.split('.')[-1]
                    if f.name.startswith(basename) and ext not in [thumb_ext, 'json']:
                        extension = ext
                        break
        return {'title': mdjs['title'],
                'id': mdjs['id'],
                'pub_date': datetime.datetime.strptime(mdjs['upload_date'],
                                                       '%Y%m%d')
                                    .strftime("%a, %d %b %Y %H:%M:%S +0000"),
                'extension': extension,
                'description': mdjs['description'],
                'thumbnail': thumbnail_file,
                'filename': '%s.%s' % (basename, extension),
                'duration': str(datetime.timedelta(seconds=mdjs['duration']))
                }


def get_playlist_metadata(ydl_mod, sub, options):
    options = options.copy()
    options.update({'quiet': True, 'simulate': True, 'forcejson': True, 'ignoreerrors': True})
    output = io.StringIO()
    with ydl_mod.YoutubeDL(options) as ydl:
        try:
            ydl._screen_file = output
            if sub['quiet']:
                ydl._err_file = io.StringIO()
            ydl.download([sub['url']])
        except ydl_mod.utils.YoutubeDLError as e:
            if not sub['quiet']:
                print(e)

    metadata = [json.loads(entry) for entry in
            ydl._screen_file.getvalue().split('\n') if len(entry) > 0]
    return metadata

def process_options(sub):
    options = {
            'outtmpl': os.path.join(
                sub['output_dir'],
                sub['name'],
                sub['filename_template']),
            'writeinfojson': True,
            'writethumbnail': True,
            'ignoreerrors': sub['ignore_errors'],
            'youtube_include_dash_manifest': True,
            }
    if sub['retention_days'] is not None and not sub['initialize']:
        options['daterange'] = ydl_mod.utils.DateRange(
                (date.today() - timedelta(days=sub['retention_days']))
                .strftime('%Y%m%d'), '99991231')
    if sub['download_last'] is not None and not sub['initialize']:
        options['max_downloads'] = sub['download_last']
    if sub['initialize']:
        options['playlistreverse'] = True
    if sub['audio_only']:
        options['format'] = 'bestaudio/%s' % sub.get('format', 'best')
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': sub.get('format', 'best'),
            'preferredquality': '5',
            'nopostoverwrites': False
            }]
    elif 'format' in sub:
        if sub['best']:
            options['format'] = 'bestvideo[ext=%s]' % sub['format']
        else:
            options['format'] = sub['format']

    for key in sub.get('ydl_options', {}):
        options[key] = sub['ydl_options'][key]

    return options


def download(ydl_mod, sub):
    downloaded = []
    options = process_options(sub)
    metadata = get_playlist_metadata(ydl_mod, sub, options)

    for entry in metadata:
        mdfile_name = '%s.meta' % '.'.join(entry['_filename'].split('.')[:-1])
        if not os.path.isfile(mdfile_name) and not entry.get('is_live', False):
            with ydl_mod.YoutubeDL(options) as ydl:
                if sub['quiet']:
                    ydl._screen_file = io.StringIO()
                    ydl._err_file = ydl._screen_file
                try:
                    ydl.download([entry['webpage_url']])
                except ydl_mod.utils.YoutubeDLError as e:
                    if not sub['quiet']:
                        print(e)
                with open(mdfile_name, 'w+') as f:
                    entry.update({
                        'subscription_name': sub['name'],
                        'formats': [fmt for fmt in entry.get('formats')
                            if (options.get('format') is None
                                or (fmt.get('format') == options.get('format')))]
                        })
                    downloaded.append(entry)
        elif entry.get('is_live', False) and not sub['quiet']:
            print("Skipping ongoing live {} - {}".format(entry.get('id'), entry.get('title')))
        elif not sub['quiet']:
            print("Skipping already retrieved {} - {}".format(entry.get('id'), entry.get('title')))
    return downloaded


def cleanup(sub):
    deleted = []
    directory = os.path.join(sub['output_dir'], sub['name'])
    for f in os.listdir(directory):
        fpath = os.path.join(directory, f)
        mtime = date.fromtimestamp(os.path.getmtime(fpath))
        ret = date.today() - timedelta(days=sub['retention_days'])
        if mtime < ret:
            os.remove(fpath)
            deleted.append(fpath)
    return deleted


def write_xml(sub):
    directory = os.path.join(sub['output_dir'], sub['name'])
    xml = """<?xml version="1.0"?>
            <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
            <channel>
            <updated>%s</updated>
            <title>%s</title>
            <link href="%s" rel="self" type="application/rss+xml"/>""" \
                    % (datetime.datetime.now(),
                       sub['name'],
                       '/'.join([sub['url_root'], "%s.xml" % sub['name']]))

    for md_file in glob.glob(os.path.join(sub['output_dir'],
                                           '%s/*.info.json' % sub['name'])):
        md = metadata_parse(md_file)
        xml += """
            <item>
            <id>%s</id>
            <title>%s</title>
            <enclosure url="%s" type="%s"/>
            <pubDate>%s</pubDate>
            <itunes:image href="%s"/>
            <itunes:summary><![CDATA[%s]]></itunes:summary>
            <itunes:duration>%s</itunes:duration>
            </item>
            """ % (html.escape(md['id']),
                   html.escape(md['title']),
                   '/'.join([sub['url_root'], quote(sub['name']), quote(md['filename'])]),
                   ('audio/%s' % md['extension']) if sub['audio_only'] \
                           else 'video/%s' % md['extension'],
                    md['pub_date'],
                    '/'.join([sub['url_root'], quote(sub['name']), quote(md['thumbnail'])]),
                    md['description'],
                    md['duration'])
    xml += '</channel></rss>'
    with open("%s.xml" % os.path.join(sub['output_dir'], sub['name']), "w")  as fout:
        fout.write(xml)

def get_ydl_module(config):
    return importlib.import_module(config.get('youtube-dl-module', "youtube_dl").replace('-', '_'))