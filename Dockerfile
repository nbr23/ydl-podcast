FROM python:alpine3.17 as build
ARG YTDL_MODULE=yt-dlp

RUN apk add --no-cache g++

COPY pyproject.toml .
COPY ydl_podcast ydl_podcast
COPY README.md .

RUN pip install uv --break-system-packages && \
    uv venv /usr/local/python-env && \
    source /usr/local/python-env/bin/activate && \
    uv pip install ".[${YTDL_MODULE}]"

FROM python:alpine3.17
ARG YTDL_MODULE=yt-dlp
ENV PYTHON_ENV="/usr/local/python-env"
ENV PATH="$PYTHON_ENV/bin:$PATH"

RUN apk add --no-cache ffmpeg tzdata mailcap

COPY --from=build /usr/local/python-env $PYTHON_ENV

WORKDIR /app

CMD ["python", "-m", "ydl_podcast"]
