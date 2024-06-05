ATOM_TMPL = """<?xml version="1.0"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <updated>{{ last_update }}</updated>
    <title>{{ channel_title }}</title>
    <link href="{{ channel_link }}" rel="self" type="application/rss+xml"/>
    {% if icon_url %}
    <itunes:image href="{{ icon_url }}"/>
    {% endif %}


{% for item in items %}
    <item>
      <id>{{ item.id }}</id>
      <title>{{ item.title }}</title>
      <enclosure url="{{ item.url }}" type="{{ item.media_type }}"/>
      {% if item.pubDate != None %}<pubDate>{{ item.pubDate }}</pubDate>{% endif %}
      {% if item.thumbnail != None %}<itunes:image href="{{ item.thumbnail }}"/>{% endif %}
      {% if item.description != None %}<itunes:summary><![CDATA[{{ item.description }}]]></itunes:summary> {% endif %}
      {% if item.duration != None %}<itunes:duration>{{ item.duration }}</itunes:duration>{% endif %}
    </item>
{% endfor %}
  </channel>
</rss>
"""

SHOW_NFO_TMPL = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<tvshow>
  <lockdata>true</lockdata>
  <title>{{ title  }}</title>
</tvshow>
"""

EPISODE_NFO_TMPL = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<episodedetails>
  <plot />
  <lockdata>true</lockdata>
  <dateadded>{{ ep_date }}</dateadded>
  <title>{{ title }}</title>
  <runtime>{{ duration }}</runtime>
  <art />
  <showtitle>{{ show_title }}</showtitle>
  <aired>{{ ep_date }}</aired>
</episodedetails>
"""

INDEX_HTML_TMPL = """
<!DOCTYPE html>
<html manifest="" lang="en-US">
  <head>
    <meta charset="UTF-8">
    <style>
body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    margin: 0;
    padding: 20px;
}

h1 {
    margin-bottom: 20px;
    font-size: 2em;
    margin: 0;
}

ul {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

li {
    display: flex;
    overflow: hidden;
    list-style-type: none;
}
    </style>
  </head>
  <body>
    <h1>Ydl-Podcast index</h1>
    <ul>
    {% for sub in subscriptions %}
      <li><a href="{{ sub.name }}.xml">{{ sub.name }}</a></li>
    {% endfor %}
    </ul>
  </body>
<html>
"""
