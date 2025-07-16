FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#系统用户
#ARG USERNAME=nriet

# 安装必要的依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends vim sudo nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ContoursAlgorithm

COPY . /opt/ContoursAlgorithm

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt