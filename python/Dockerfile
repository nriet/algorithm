# 使用官方轻量级Python基础镜像
FROM python:3.10-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

WORKDIR /app

#系统用户
ARG USERNAME=nriet

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libssl-dev libffi-dev python3-dev vim sudo openssh-server \
    && rm -rf /var/lib/apt/lists/*

# RUN apt-get update \
#       && apt-get install -y --no-install-recommends \
#        vim sudo openssh-server; \
#     rm -rf /var/lib/apt/lists/*

# 配置 SSH 服务器
RUN mkdir -p /var/run/sshd

RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config   # 允许 root 用户远程登录

# 复制依赖文件并安装
COPY requirements.txt .

#RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 开放 SSH 服务器端口
EXPOSE 22

# 启动 SSH 服务
CMD ["/usr/sbin/sshd", "-D"]