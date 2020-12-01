#! /usr/bin/env python3

import sys
import os
import io
import glob
import yaml
import html
from urllib.parse import quote
import json
import datetime
from datetime import date, timedelta
import youtube_dl
from youtube_dl.utils import DateRange
from collections import ChainMap

sub_defaults = {
        'retention_days': None,
        'audio_only': False,
        'download_last': None,
        'initialize': False,
        'best': False,
        'ignore_errors': False,
        }

def load_config(config_path):
    config = None
    if not os.path.isfile(config_path):
        print("Config file '%s' not found." % config_path)
        return None
    with open(config_path) as configfile:
        config = yaml.load(configfile, Loader=yaml.SafeLoader)
    return config

def metadata_parse(metadata_path):
    with open(metadata_path) as metadata:
        mdjs = json.load(metadata)
        basename = '.'.join(os.path.basename(metadata_path).split('.')[:-2])
        path = os.path.dirname(metadata_path)
        thumb_ext = mdjs['thumbnail'].split('.')[-1]
        thumbnail_file = '%s.%s' % (basename, thumb_ext)
        extension = mdjs['acodec'] if 'audio only' in mdjs['format'] \
                    else mdjs['ext']
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

def download(sub):
    options = {
            'outtmpl': os.path.join(sub['output_dir'],
                                       sub['name'],
                                       '%(title)s [%(id)s][%(upload_date)s].%(ext)s'),
            'writeinfojson': True,
            'writethumbnail': True,
            'ignoreerrors': sub['ignore_errors'],
            }
    if sub['retention_days'] is not None and not sub['initialize']:
        options['daterange'] = DateRange((date.today() - \
                    timedelta(days=sub['retention_days']))
                    .strftime('%Y%m%d'), '99991231')
    if sub['download_last'] is not None and not sub['initialize']:
        options['max_downloads'] = sub['download_last']
    if sub['initialize']:
        options['playlistreverse'] = True
    if sub['audio_only']:
        options['format'] = 'bestaudio/%s' % ('best' if 'format' not in sub \
                                                     else sub['format'])
        options['postprocessors'] = [{'key': 'FFmpegExtractAudio',
            'preferredcodec': 'best' if 'format' not in sub
                                     else sub['format'],
            'preferredquality': '5',
            'nopostoverwrites': False}]
    elif 'format' in sub:
        if sub['best']:
            options['format'] = 'bestvideo[ext=%s]' % sub['format']
        else:
            options['format'] = sub['format']

    if 'ydl_options' in sub:
        for key in sub['ydl_options']:
            options[key] = sub['ydl_options'][key]

    # Get playlist metadata
    options.update({'quiet': True, 'simulate': True, 'forcejson': True})
    output = io.StringIO()
    with youtube_dl.YoutubeDL(options) as ydl:
        try:
            ydl._screen_file = output
            ydl.download([sub['url']])
        except youtube_dl.utils.MaxDownloadsReached:
            pass

    metadata = [json.loads(entry) for entry in
            ydl._screen_file.getvalue().split('\n') if len(entry) > 0]

    options.pop('simulate')
    options.pop('quiet')
    options.pop('forcejson')

    for entry in metadata:
        mdfile_name = os.path.join(sub['output_dir'], sub['name'],
                '.{}.{}.meta'.format(entry.get('id'), entry.get('title')))
        if not os.path.isfile(mdfile_name) and not entry.get('is_live', False):
            with youtube_dl.YoutubeDL(options) as ydl:
                try:
                    ydl.download([entry['webpage_url']])
                except youtube_dl.utils.MaxDownloadsReached:
                    pass
                with open(mdfile_name, 'w+') as f:
                    pass
        elif entry.get('is_live', False):
            print("Skipping ongoing live {} - {}".format(entry.get('id'), entry.get('title')))
        else:
            print("Skipping already retrieved {} - {}".format(entry.get('id'), entry.get('title')))

def cleanup(sub):
    directory = os.path.join(sub['output_dir'], sub['name'])
    for f in os.listdir(directory):
        fpath = os.path.join(directory, f)
        mtime = date.fromtimestamp(os.path.getmtime(fpath))
        ret = date.today() - timedelta(days=sub['retention_days'])
        if mtime < ret:
            os.remove(fpath)

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

def main():
    argv = sys.argv
    config = load_config(argv[1] if len(argv) > 1 else 'config.yaml')
    if not config:
        print("No valid configuration found.")
        return -1

    for sub in config['subscriptions']:
        sub = ChainMap(sub, {t: config[t] for t in config.keys() if t in ['output_dir', 'url_root', 'best', 'format']}, sub_defaults)
        if 'ydl_options' in sub and sub['ydl_options'] is not None\
                and 'ydl_options' in config \
                and config['ydl_options'] is not None:
            sub['ydl_options'] = {**config['ydl_options'], **sub['ydl_options']}
        elif 'ydl_options' in config and config['ydl_options'] is not None:
            sub['ydl_options'] = config['ydl_options']
        elif 'ydl_options' in sub and sub['ydl_options'] is None:
            sub['ydl_options'] = {}
        if 'name' not in sub or 'url' not in sub or 'output_dir' not in sub \
                or 'url_root' not in sub:
            print("Skipping erroneous subscription")
            continue

        if os.path.isdir(os.path.join(sub['output_dir'], sub['name'])) \
                and sub['initialize']:
            sub['initialize'] = False

        download(sub)

        if sub['retention_days'] is not None and not sub['initialize']:
            cleanup(sub)

        write_xml(sub)

if __name__ == "__main__":
    sys.exit(main())
