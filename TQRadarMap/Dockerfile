FROM openeuler/openeuler:24.03
#FROM registry.cn-hangzhou.aliyuncs.com/nriet/algorithm:tqradarmap_openeuler_24.03_linux_arm64

MAINTAINER Axiu <itzyx@vip.qq.com>

WORKDIR /app/TQRadarMap/bin

ENV LD_LIBRARY_PATH /app/TQRadarMap/lib:$LD_LIBRARY_PATH

ENV QMAKE_SPEC linux-g++

COPY ./TQRadarMap/TQRadarMap_x86/ /app/TQRadarMap


RUN ldd Algo_QC
RUN ldd Algo_PPIS
RUN ldd Algo_CAPPI_Grid