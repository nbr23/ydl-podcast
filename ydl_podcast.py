#! /usr/bin/env python3
import sys
import os
import re
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
        'audio_only': False
        }

def load_config(config_path):
    config = None
    if not os.path.isfile(config_path):
        print("Config file '%s' not found." % config_path)
        return None
    with open(config_path) as configfile:
        config = yaml.load(configfile, Loader=yaml.SafeLoader)
    return config if 'output_dir' in config and 'url_root' in config else None

def get_episode_info(filename):
    title, id, date, ext = re.match(r'^(.*) \[([^]]*)\]\[([^]]*)\]\.(.+)$',
            filename).groups()
    return {'title': title,
            'id': id,
            'pub_date': datetime.datetime.strptime(date, '%Y%m%d')
                                .strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'extension': ext}

def metadata_parse(metadata_path):
    with open(metadata_path) as metadata:
        mdjs = json.load(metadata)
        basename = '.'.join(os.path.basename(metadata_path).split('.')[:-2])
        thumbnail_file = '%s.%s' % (basename, mdjs['thumbnail'].split('.')[-1])
        extension = mdjs['acodec'] if 'audio only' in mdjs['format'] \
                    else mdjs['ext']
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

def download(config, sub):
    options = {
            'outtmpl': os.path.join(config['output_dir'],
                                       sub['name'],
                                       '%(title)s [%(id)s][%(upload_date)s].%(ext)s'),
            'writeinfojson': True,
            'writethumbnail': True,
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
        options['format'] = 'bestaudio/best'
        options['postprocessors'] = [{'key': 'FFmpegExtractAudio',
            'preferredcodec': 'best',
            'preferredquality': '5',
            'nopostoverwrites': False}]
    with youtube_dl.YoutubeDL(options) as ydl:
        try:
            ydl.download([sub['url']])
        except youtube_dl.utils.MaxDownloadsReached:
            pass


def cleanup(config, sub):
    directory = os.path.join(config['output_dir'], sub['name'])
    for f in os.listdir(directory):
        fpath = os.path.join(directory, f)
        mtime = date.fromtimestamp(os.path.getmtime(fpath))
        ret = date.today() - timedelta(days=sub['retention_days'])
        if mtime < ret:
            os.remove(fpath)

def write_xml(config, sub):
    directory = os.path.join(config['output_dir'], sub['name'])
    xml = """<?xml version="1.0"?>
            <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
            <channel>
            <updated>%s</updated>
            <title>%s</title>
            <link href="%s" rel="self" type="application/rss+xml"/>""" \
                    % (datetime.datetime.now(),
                       sub['name'],
                       '/'.join([config['url_root'], "%s.xml" % sub['name']]))

    for md_file in glob.glob(os.path.join(config['output_dir'],
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
                   '/'.join([config['url_root'], quote(sub['name']), quote(md['filename'])]),
                   ('audio/%s' % md['extension']) if sub['audio_only'] \
                           else 'video/%s' % md['extension'],
                    md['pub_date'],
                    '/'.join([config['url_root'], quote(sub['name']), quote(md['thumbnail'])]),
                    md['description'],
                    md['duration'])
    xml += '</channel></rss>'
    with open("%s.xml" % os.path.join(config['output_dir'], sub['name']), "w")  as fout:
        fout.write(xml)

def main(argv):
    config = load_config(argv[1] if len(argv) > 1 else 'config.yaml')
    if not config:
        print("No valid configuration found.")
        return -1

    for sub in config['subscriptions']:
        if 'name' not in sub or 'url' not in sub:
            print("Skipping erroneous subscription")
            continue

        sub = ChainMap(sub, sub_defaults)
        if os.path.isdir(os.path.join(config['output_dir'], sub['name'])) \
                and sub['initialize']:
            sub['initialize'] = False

        download(config, sub)

        if sub['retention_days'] is not None and not sub['initialize']:
            cleanup(config, sub)

        write_xml(config, sub)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
