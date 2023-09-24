FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

ENV USERNAME nriet

#创建用户
RUN useradd -ms /bin/bash nriet

USER nriet

WORKDIR /space/cmadaas/dpl/nriet

#下载EC认证文件，用于人工智能算法
COPY .cdsapirc /home/nriet/

COPY requirements-base.txt ./

RUN pip install --no-cache-dir -r requirements-base.txt

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY app /space/cmadaas/dpl/nriet/app

CMD ["python","/space/cmadaas/dpl/nriet/app/SEDES/code/main.py"]
