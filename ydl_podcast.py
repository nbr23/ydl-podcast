#! /usr/bin/env python3
import sys
import os
import yaml
import datetime
from datetime import date, timedelta
import youtube_dl
from youtube_dl.utils import DateRange
from collections import ChainMap

def load_config(config_path):
    config = None
    if not os.path.isfile(config_path):
        print("Config file '%s' not found." % config_path)
        return None
    with open(config_path) as configfile:
        config = yaml.load(configfile, Loader=yaml.SafeLoader)
    return config

def download(config, subscription):
    options = {
            'outtmpl': os.path.join(config['output_dir'],
                                       subscription['name'],
                                       '%(title)s [%(id)s].%(ext)s'),
            'daterange': DateRange((date.today() - \
                    timedelta(days=subscription['retention_days']))
                    .strftime('%Y%m%d'), '99991231')}
    if subscription['audio_only']:
        options['format'] = 'bestaudio/best'
        options['postprocessors'] = [{'key': 'FFmpegExtractAudio',
            'preferredcodec': 'best',
            'preferredquality': '5',
            'nopostoverwrites': False}]
    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([subscription['url']])

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
        mtime = date.fromtimestamp(os.path.getmtime(fpath))\
                    .strftime("%a, %d %b %Y %H:%M:%S +0000")
        print(mtime)
        if os.path.isfile(fpath) and not f.startswith('.'):
            xml += """
            <item>
            <id>%s</id>
            <title>%s</title>
            <enclosure url="%s" type="%s"/>
            <pubDate>%s</pubDate>
            </item>
            """ % (f,
                   f,
                   '/'.join([config['url_root'], sub['name'], f]),
                   ('audio/%s' % f.split('.')[-1]) if sub['audio_only'] \
                           else 'video/%s' % f.split('.')[-1],mtime)
    xml += '</channel></rss>'
    with open("%s.xml" % os.path.join(config['output_dir'], sub['name']), "w")  as fout:
        fout.write(xml)

sub_defaults = {
        'retention_days': None,
        'audio_only': False
        }

def main(argv):
    config = load_config(argv[1] if len(argv) > 1 else 'config.yaml')
    if not config:
        print("Configuration file not found.")
        return -1

    for sub in config['subscriptions']:
        if 'name' not in sub or 'url' not in sub:
            print("Skipping erroneous subscription")
            continue

        sub = ChainMap(sub, sub_defaults)
        download(config, sub)
        if sub['retention_days'] is not None:
            cleanup(config, sub)
        write_xml(config, sub)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
