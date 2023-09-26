FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#系统用户
ARG USERNAME=nriet

#创建用户
RUN useradd -ms /bin/bash ${USERNAME}

WORKDIR /space/cmadaas/dpl/${USERNAME}

COPY . /space/cmadaas/dpl/${USERNAME}/

RUN chown -R ${USERNAME}:${USERNAME} /space/cmadaas/dpl/${USERNAME}

#USER ${USERNAME}

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt 

EXPOSE 22

CMD ["/usr/sbin/sshd" "-D"]