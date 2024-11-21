# 使用官方Python基础镜像
FROM python:3.9-slim

LABEL version="1.0"

WORKDIR /opt/station-pykrige

COPY . /opt/station-pykrige

# 安装系统工具和依赖库
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgfortran5 \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

