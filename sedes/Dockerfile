FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#系统用户
ARG USERNAME=nriet

#创建用户
RUN useradd -ms /bin/bash ${USERNAME}

USER ${USERNAME}

WORKDIR /space/cmadaas/dpl/${USERNAME}

COPY app /space/cmadaas/dpl/${USERNAME}/app

RUN chown ${USERNAME}:${USERNAME} /space/cmadaas/dpl/${USERNAME}/app

#下载EC认证文件，用于人工智能算法
COPY .cdsapirc /home/${USERNAME}/

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python","app/SEDES/main.py"]
