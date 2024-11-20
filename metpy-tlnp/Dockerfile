FROM python:3.11-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

WORKDIR /opt/tlnp

COPY . /opt/tlnp

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
