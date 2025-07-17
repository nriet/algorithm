FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

# 安装必要的依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends vim sudo curl \
    && rm -rf /var/lib/apt/lists/*


# 安装 nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# 设置 NVM 的环境变量
ENV NVM_DIR=/root/.nvm
ENV NODE_VERSION=22

# 将 nvm 加入到 PATH 中
RUN echo "export NVM_DIR=\"$NVM_DIR\"" >> /root/.bashrc && \
    echo "[ -s \"$NVM_DIR/nvm.sh\" ] && \\. \"$NVM_DIR/nvm.sh\"" >> /root/.bashrc && \
    echo "[ -s \"$NVM_DIR/bash_completion\" ] && \. \"$NVM_DIR/bash_completion\"" >> /root/.bashrc

# 使用 bash 执行安装 Node.js
RUN bash -c "source /root/.bashrc && nvm install $NODE_VERSION"

RUN bash -c "npm install -g npm@11.4.2"

# 验证安装
RUN bash -c "source /root/.bashrc && node -v && npm -v"

WORKDIR /opt/ContoursAlgorithm

COPY . /opt/ContoursAlgorithm

COPY requirements.txt ./

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt