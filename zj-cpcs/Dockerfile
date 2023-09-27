FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#系统用户
ARG USERNAME=BEHZ_QHZX_ZJCMPS

#创建用户
RUN useradd -ms /bin/bash ${USERNAME}

RUN echo '${USERNAME}:' | chpasswd

# 改变用户的UID和GID
# RUN usermod -u 1000 ${USERNAME} && usermod -G 1000 ${USERNAME}
# 允许新用户拥有root权限
#RUN echo '${USERNAME} ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

WORKDIR /space/cmadaas/dpl/${USERNAME}

COPY . /space/cmadaas/dpl/${USERNAME}/

RUN chown -R ${USERNAME}:${USERNAME} /space/cmadaas/dpl/${USERNAME}

RUN apt-get update \
      && apt-get install -y --no-install-recommends \
        libgeos-dev sudo openssh-server; \
    rm -rf /var/lib/apt/lists/*

# RUN pip install pipreqs ;\
#     find . -type d -exec sh -c "pipreqs {} --force" \;
# RUN pip install --upgrade pip; \
#     pip freeze > requirements.txt; \
#     pip install --no-cache-dir -r requirements.txt 

RUN adduser ${USERNAME} sudo

#USER ${USERNAME}

#COPY requirements.txt ./

# RUN pip install --upgrade pip; \
#     pip install --no-cache-dir -r requirements.txt 

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]