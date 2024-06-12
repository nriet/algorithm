FROM centos:centos7.9.2009

MAINTAINER Axiu <itzyx@vip.qq.com>

ENV NWP_PL_VERSION 1.0

COPY app.tar.gz /

ENV GRIB_DEFINITION_PATH /app/NWP_PL_V${NWP_PL_VERSION}/definitions

ENV LD_LIBRARY_PATH :/app/NWP_PL_V${NWP_PL_VERSION}/lib

RUN apt-get update \
      && apt-get install -y --no-install-recommends \
        gdal-bin libgdal-dev libnetcdf-dev; \
        tar zxvf /app.tar.gz -C /; \
        rm -rf /app.tar.gz; \
    rm -rf /var/lib/apt/lists/*
