FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

MAINTAINER Jimming Cheng

RUN apt-get update && apt-get install -y \
    software-properties-common \
    build-essential \
    curl \
    tzdata

RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv

ENV TZ US/Pacific
ENV OAUTHLIB_RELAX_TOKEN_SCOPE 1
RUN echo ${TZ} > /etc/timezone && dpkg-reconfigure tzdata

COPY ./secretary /app/secretary
COPY ./README.md /app/
COPY ./poetry.lock /app/
COPY ./pyproject.toml /app/

WORKDIR /app
RUN python3.11 -m venv /app/venv
RUN /app/venv/bin/pip install poetry
RUN . /app/venv/bin/activate && /app/venv/bin/poetry install

RUN groupadd -g 72277 sbapp
RUN useradd -ms /bin/bash -g sbapp -u 1001 scooterbot
USER scooterbot

CMD [ \
  "/app/venv/bin/uvicorn", \
  "secretary.asgi:application", \
  "--host", "0.0.0.0", \
  "--port", "8080", \
  "--workers", "4" \
]
