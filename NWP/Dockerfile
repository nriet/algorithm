FROM centos:centos7.9.2009

MAINTAINER Axiu <itzyx@vip.qq.com>

WORKDIR /app/NWP

ENV NWP_VERSION 1.0

ENV GRIB_DEFINITION_PATH /app/NWP/definitions

ENV LD_LIBRARY_PATH :/app/NWP/lib

ENV NWP_URL https://github.com/nriet/algorithm/releases/download/NWPConvert4.0/NWP-x86_64.zip

RUN yum update -y && \
    yum install -y wget unzip && \
    yum clean all

RUN set -eux; \
	\
	wget -O NWP.zip "${NWP_URL}" --no-check-certificate; \
	unzip -oq NWP.zip -d /app; \
  chmod +x /app/NWP/NWPConvert; \
	rm -rf NWP.zip

RUN ldd /app/NWP/NWPConvert

# RUN apt-get update \
#       && apt-get install -y --no-install-recommends \
#         gdal-bin libgdal-dev libnetcdf-dev; \
#     rm -rf /var/lib/apt/lists/*




