FROM python:3.9-slim

MAINTAINER Axiu <itzyx@vip.qq.com>

#下载EC认证文件，用于人工智能算法
COPY .cdsapirc /root/

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements-base.txt

RUN pip install --no-cache-dir -r requirements.txt


CMD ["catalina.sh", "run"]
