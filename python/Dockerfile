# 使用官方轻量级Python基础镜像
FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露服务端口（根据实际应用修改）
#EXPOSE 5000

# 设置启动命令
CMD ["python", "app.py"]


