FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

ENV USERNAME nriet

#创建用户
RUN useradd -ms /bin/bash ${USERNAME}

USER ${USERNAME}

WORKDIR /space/cmadaas/dpl/${USERNAME}

#下载EC认证文件，用于人工智能算法
COPY .cdsapirc /home/${USERNAME}/

COPY requirements-base.txt ./

RUN pip install --no-cache-dir -r requirements-base.txt

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY app /space/cmadaas/dpl/${USERNAME}/app

CMD ["python","/space/cmadaas/dpl/${USERNAME}/app/SEDES/code/main.py"]
