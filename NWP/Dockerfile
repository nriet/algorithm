FROM centos:centos7.9.2009

MAINTAINER Axiu <itzyx@vip.qq.com>

# 运行命令来获取系统架构并设置为环境变量
RUN arch > /tmp/arch && \
    export ARCH=$(cat /tmp/arch) && \
    echo "Architecture: $ARCH"

# 将系统架构设置为环境变量
ARG ARCH
ENV ARCH=${ARCH:-$(cat /tmp/arch)}

# 清理临时文件
RUN rm /tmp/arch

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




