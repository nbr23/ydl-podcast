FEED_STYLE_TMPL = """<?xml version="1.0"?>
<xsl:stylesheet
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
                version="1.0">
  <xsl:output method="html"/>
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en">
      <head>
        <title>
          ydl-podcast | <xsl:value-of select="/rss/channel/title"/>
        </title>
        <style>
body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    margin: 0;
    padding: 20px;
}

.podcast-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.podcast-thumbnail {
    width: 100px;
    height: 100px;
    object-fit: cover;
    margin-right: 20px;
    display: none;
}

.podcast-title {
    font-size: 2em;
    margin: 0;
    color: #333;

    a {
        font-size: 0.5em;
        margin-left: 10px;
        text-decoration: none;
    }
}

.item-list {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.item {
    display: flex;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: transform 0.2s;
}

.item:hover {
    transform: scale(1.02);
}

.thumbnail {
    width: 150px;
    height: 150px;
    object-fit: cover;
    border-right: 1px solid #ddd;
}

.details {
    padding: 20px;
    flex: 1;
    text-decoration: none;
    color: inherit;
}

.title {
    font-size: 1.7em;
    margin: 0 0 10px;
    color: #333;
    font-weight: bold;
}

.description {
    font-size: 1em;
    margin: 0;
    color: #666;
}
        </style>
      </head>
      <body>
        <div class="podcast-header">
          <xsl:if test="/rss/channel/itunes:image/@href">
            <img class="podcast-thumbnail" style="display: block;">
              <xsl:attribute name="src">
                <xsl:value-of select="/rss/channel/itunes:image/@href"/>
              </xsl:attribute>
            </img>
          </xsl:if>
          <h1 class="podcast-title">
            <xsl:value-of select="/rss/channel/title"/>
            <a target="_blank" rel="noopener noreferrer">
            <xsl:attribute name="href">
              <xsl:value-of select="/rss/channel/link"/>
            </xsl:attribute>
            🔗
            </a>
          </h1>
        </div>
        <div class="item-list">
          <xsl:for-each select="/rss/channel/item">
           <div class="item">
            <img class="thumbnail">
              <xsl:attribute name="src">
                <xsl:value-of select="itunes:image/@href"/>
              </xsl:attribute>
            </img>
            <a class="details" target="_blank" rel="noopener noreferrer">
              <xsl:attribute name="href">
                <xsl:value-of select="enclosure/@url"/>
              </xsl:attribute>
              <h3 class="title"><xsl:value-of select="title"/></h3>
              <p class="description">
                <xsl:value-of select="itunes:summary"/>
              </p>
            </a>
          </div>
          </xsl:for-each>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
"""
