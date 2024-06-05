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
