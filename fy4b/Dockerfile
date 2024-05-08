FROM python:3.9

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#系统用户
ARG USERNAME=nriet

# 安装必要的依赖
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libffi-dev \
#     libssl-dev \
#     && rm -rf /var/lib/apt/lists/*

# RUN apt-get update \
#       && apt-get install -y --no-install-recommends \
#        vim sudo openssh-server gfortran; \
#     rm -rf /var/lib/apt/lists/*

# 配置 SSH 服务器
# RUN mkdir /var/run/sshd

# RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config   # 允许 root 用户远程登录

WORKDIR /opt/fy4b

COPY . /opt/fy4b

# RUN pip install --no-cache-dir -r requirements.txt

# RUN pip install numpy

# RUN cd /home/code/; \
# 	python a0_ll2lc_fy4a.py; \
# 	f2py -m index2data -c index2data.f90

# 开放 SSH 服务器端口
# EXPOSE 22

# 启动 SSH 服务
# CMD ["/usr/sbin/sshd", "-D"]