FROM nriet/kylin10:v1.0

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

COPY CMA.repo /etc/yum.repos.d/CMA.repo

RUN yum update; \
    yum install -y geos; \
    yum clean all; \
    rm -rf /var/cache/yum

# 开放 SSH 服务器端口
EXPOSE 22
