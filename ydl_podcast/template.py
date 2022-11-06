ATOM_TMPL = """
"<?xml version="1.0"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <updated>{{ last_update }}</updated>
    <title>{{ channel_title }}</title>
    <link href="{{ channel_link }}" rel="self" type="application/rss+xml"/>

{% for item in items %}
    <item>
    <id>{{ item.id }}</id>
    <title>{{ item.title }}</title>
    <enclosure url="{{ item.url }}" type="{{ item.media_type }}"/>
    <pubDate>{{ item.pubDate }}</pubDate>
    {% if item.thumbnail != None %}
    <itunes:image href="{{ item.thumbnail }}"/>
    {% endif %}
    <itunes:summary><![CDATA[item.summary]]></itunes:summary>
    <itunes:duration>item.duration</itunes:duration>
    </item>
{% endfor %}
  </channel>
</rss>
"""