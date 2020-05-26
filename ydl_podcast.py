#! /usr/bin/env python3
import sys
import os
import re
import yaml
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

def download(config, sub):
    options = {
            'outtmpl': os.path.join(config['output_dir'],
                                       sub['name'],
                                       '%(title)s [%(id)s][%(upload_date)s].%(ext)s'),
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
            <rss version="2.0">
            <channel>
            <updated>%s</updated>
            <title>%s</title>
            <link href="%s" rel="self" type="application/rss+xml"/>""" \
                    % (datetime.datetime.now(),
                       sub['name'],
                       '/'.join([config['url_root'], "%s.xml" % sub['name']]))
    for f in os.listdir(directory):
        fpath = os.path.join(directory, f)
        if os.path.isfile(fpath) and not f.startswith('.'):
            ep_info = get_episode_info(f)
            xml += """
            <item>
            <id>%s</id>
            <title>%s</title>
            <enclosure url="%s" type="%s"/>
            <pubDate>%s</pubDate>
            </item>
            """ % (ep_info['id'],
                   ep_info['title'],
                   '/'.join([config['url_root'], sub['name'], f]),
                   ('audio/%s' % ep_info['extension']) if sub['audio_only'] \
                           else 'video/%s' % ep_info['extension'],
                    ep_info['pub_date'])
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
