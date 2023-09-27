#!/bin/bash
if [ ! -d "/space/cmadaas/dpl" ]; then
          mkdir -p /space/cmadaas/dpl
fi
if [ ! -d "/space/cmadaas/dpl/$1" ]; then
        echo "开始创建用户$1"
        if id -u $1 >/dev/null 2>&1; then
        echo "user exists"
        else
        useradd -d /space/cmadaas/dpl/$1 -m -u $2 $1
    fi
else
    echo "/space/cmadaas/dpl/$1 目录已存在！重新授权用户$1"
        if id -u $1 >/dev/null 2>&1; then
      echo "user exists"
        else
      useradd -d /space/cmadaas/dpl/$1 -m -u $2 $1
    fi
    chown -R $1:$1 /space/cmadaas/dpl/$1
    cp /etc/skel/.bash* /space/cmadaas/dpl/$1/
fi

echo $1:$3 | chpasswd
sed -i '$a\$1  ALL=(ALL)  NOPASSWD: ALL' /etc/sudoers
/usr/sbin/sshd -D