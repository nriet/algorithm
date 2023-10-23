FROM centos:centos7.9.2009

MAINTAINER Axiu <itzyx@vip.qq.com>

RUN yum install -y  net-tools.x86_64 kde-l10n-Chinese sudo openssh-server &&\
                   yum clean all && \
                   rm -rf /var/cache/yum

RUN yum install -y epel-release geos geos-devel &&\
                   yum clean all && \
                   rm -rf /var/cache/yum

RUN localedef -c -f UTF-8 -i zh_CN zh_CN.utf8

ENV LC_ALL zh_CN.UTF-8

ENV TZ PRC

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 配置 SSH 服务器
RUN mkdir /var/run/sshd

# RUN echo 'root:password' | chpasswd   # 设置 root 用户密码（请替换为你的密码）
RUN  ssh-keygen -A && \
    echo 'root:password' | chpasswd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config   # 允许 root 用户远程登录

# 开放 SSH 服务器端口
EXPOSE 22

# 启动 SSH 服务
CMD ["/usr/sbin/sshd", "-D"]