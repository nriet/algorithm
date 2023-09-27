FROM python:3.9-slim

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

COPY user_init.sh /

RUN chmod 755 /user_init.sh

#系统用户
ARG USERNAME=BEHZ_QHZX_ZJCMPS

RUN apt-get update \
      && apt-get install -y --no-install-recommends \
        openssh* net-tools lsof telnet passwd wget vim gcc gcc-c++ sudo libgeos-dev; \
        ./user_init.sh ${BEHZ_QHZX_ZJCMPS} 1001 nriet123; \
    rm -rf /var/lib/apt/lists/*

#USER ${USERNAME}

#COPY requirements.txt ./

# RUN pip install --upgrade pip; \
#     pip install --no-cache-dir -r requirements.txt 

EXPOSE 22

CMD ["/usr/sbin/sshd" "-D"] 