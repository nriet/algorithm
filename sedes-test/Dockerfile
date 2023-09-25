FROM nriet/algorithm:sedes-python3

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

#系统用户
ARG USERNAME=nriet

COPY . /space/cmadaas/dpl/${USERNAME}/

USER root

RUN chown -R nriet:nriet /space/cmadaas/dpl/${USERNAME}/

USER nriet

RUN python app/SEDES/main.py 2023-08

#CMD ["python","app/SEDES/main.py"]
