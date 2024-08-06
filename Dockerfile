FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

MAINTAINER Jimming Cheng

RUN apt-get update && apt-get install -y \
    software-properties-common

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    openssh-client \
    python3.11 \
    python3.11-dev \
    tzdata \
    virtualenv

ENV TZ US/Pacific
ENV OAUTHLIB_RELAX_TOKEN_SCOPE 1
RUN echo ${TZ} > /etc/timezone && dpkg-reconfigure tzdata

COPY ./secretary /app/secretary
COPY ./README.md /app/
COPY ./poetry.lock /app/
COPY ./pyproject.toml /app/

WORKDIR /app
RUN virtualenv venv --python=python3.11
RUN /app/venv/bin/pip install poetry==1.3.2
RUN . /app/venv/bin/activate && /app/venv/bin/poetry install

RUN groupadd -g 72277 sbapp
RUN useradd -ms /bin/bash -g sbapp -u 1001 scooterbot
USER scooterbot

CMD [ \
  "/app/venv/bin/uwsgi", \
  "--socket", "0.0.0.0:8080", \
  "--http", "0.0.0.0:58080", \
  "--buffer-size", "8192", \
  "-p", "25", \
  "-w", "secretary.wsgi" \
]
