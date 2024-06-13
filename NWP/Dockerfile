FROM centos:centos7.9.2009

MAINTAINER Axiu <itzyx@vip.qq.com>

# 设置环境变量
ENV ARCH=${ARCH}

# 示例命令，显示架构信息
RUN echo "The architecture is $ARCH"


ENV NWP_VERSION 1.0

ENV GRIB_DEFINITION_PATH /app/NWP/definitions

ENV LD_LIBRARY_PATH :/app/NWP/lib

ENV NWP_URL https://github.com/nriet/algorithm/releases/download/NWPConvert4.0/NWP-$ARCH.zip

RUN set -eux; \
	\
	wget -O NWP.zip "${NWP_URL}" --no-check-certificate; \
	unzip -oq NWP.zip -d /app; \
	rm -rf NWP.zip


# RUN apt-get update \
#       && apt-get install -y --no-install-recommends \
#         gdal-bin libgdal-dev libnetcdf-dev; \
#     rm -rf /var/lib/apt/lists/*




