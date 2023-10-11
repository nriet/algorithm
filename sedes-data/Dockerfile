FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#时间
ARG time=2022-05

#系统用户
ARG USERNAME=nriet

#创建用户
RUN useradd -ms /bin/bash ${USERNAME}

WORKDIR /space/cmadaas/dpl/${USERNAME}

COPY . /space/cmadaas/dpl/${USERNAME}/

RUN chown -R ${USERNAME}:${USERNAME} /space/cmadaas/dpl/${USERNAME}

USER ${USERNAME}

#下载EC认证文件，用于人工智能算法
COPY .cdsapirc /home/${USERNAME}/

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt ;\
    python main.py ${time} ;\
    rm -rf ec_data ;\
    pip freeze | xargs pip uninstall -y