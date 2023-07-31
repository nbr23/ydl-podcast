FROM python:alpine
ARG YTDL_MODULE=yt-dlp

WORKDIR /app

COPY README.md .
COPY pyproject.toml .
COPY ydl_podcast ydl_podcast

RUN pip install .[$YTDL_MODULE]

CMD ["python", "-m", "ydl_podcast"]