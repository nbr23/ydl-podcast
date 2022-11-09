ATOM_TMPL = """<?xml version="1.0"?>
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
      {% if item.pubDate != None %}<pubDate>{{ item.pubDate }}</pubDate>{% endif %}
      {% if item.thumbnail != None %}<itunes:image href="{{ item.thumbnail }}"/>{% endif %}
      {% if item.description != None %}<itunes:summary><![CDATA[{{ item.description }}]]></itunes:summary> {% endif %}
      {% if item.duration != None %}<itunes:duration>{{ item.duration }}</itunes:duration>{% endif %}
    </item>
{% endfor %}
  </channel>
</rss>
"""
