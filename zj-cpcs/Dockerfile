FROM centos:centos7.9.2009

MAINTAINER Axiu <itzyx@vip.qq.com>

RUN yum install -y net-tools.x86_64 kde-l10n-Chinese &&\
                   yum clean all && \
                   rm -rf /var/cache/yum

RUN localedef -c -f UTF-8 -i zh_CN zh_CN.utf8

ENV LC_ALL zh_CN.UTF-8

ENV TZ PRC

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

