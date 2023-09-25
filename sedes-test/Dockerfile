FROM nriet/algorithm:sedes-python3

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

RUN python main.py 2023-08

USER root

RUN cd / ;\
    ls | grep -v space | xargs rm -rf \

# pip uninstall -y $(pip list | cut -d' ' -f1)

#CMD ["python","app/SEDES/main.py"]
