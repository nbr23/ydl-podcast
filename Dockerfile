FROM python:alpine3.17 as wheels

RUN apk add --no-cache g++
RUN pip install --upgrade --no-cache-dir pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /out/wheels brotli pycryptodomex websockets pyyaml

FROM python:alpine3.17
ARG YTDL_MODULE=yt-dlp

COPY --from=wheels /out/wheels /wheels
RUN pip install --upgrade --no-cache-dir pip \
    && pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

WORKDIR /app

COPY README.md .
COPY pyproject.toml .
COPY ydl_podcast ydl_podcast

RUN pip install .[$YTDL_MODULE]

CMD ["python", "-m", "ydl_podcast"]