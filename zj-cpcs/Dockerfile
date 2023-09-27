FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#系统用户
ARG USERNAME=BEHZ_QHZX_ZJCMPS

RUN apt-get update \
      && apt-get install -y --no-install-recommends \
       sudo openssh-server libgeos-dev; \
    rm -rf /var/lib/apt/lists/*

# 配置 SSH 服务器
RUN mkdir /var/run/sshd
# RUN echo 'root:password' | chpasswd   # 设置 root 用户密码（请替换为你的密码）
RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config   # 允许 root 用户远程登录

COPY user_init.sh /

RUN chmod 755 /user_init.sh

RUN ./user_init.sh ${USERNAME} 1001 nriet123

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

USER ${USERNAME}

# 开放 SSH 服务器端口
EXPOSE 22

# 启动 SSH 服务
CMD ["/usr/sbin/sshd", "-D"]