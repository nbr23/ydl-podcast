FEED_TMPL = """<?xml version="1.0"?>
{% if style_rss_feed %}
<?xml-stylesheet type="text/xsl" href="style.xsl"?>
{% endif %}
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <updated>{{ last_update }}</updated>
    <title><![CDATA[{{ channel_title }}]]></title>
    <link><![CDATA[{{ channel_link }}]]></link>
    <description><![CDATA[{{ channel_description | default(channel_title, true) }}]]></description>
    {% if icon_url %}
    <itunes:image href="{{ icon_url }}"/>
    {% endif %}


{% for item in items %}
    <item>
      <guid isPermaLink="false"><![CDATA[{{ item.id }}]]></guid>
      <title><![CDATA[{{ item.title }}]]></title>
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
