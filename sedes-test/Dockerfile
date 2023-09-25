FROM nriet/algorithm:sedes-python3

LABEL maintainer="Axiu <itzyx@vip.qq.com>"

LABEL version="1.0"

RUN python main.py 2023-08

RUN set -eux; \
	pip uninstall -y $(pip list | cut -d' ' -f1); \
	rm -rf /var/lib/apt/lists/*

# pip uninstall -y $(pip list | cut -d' ' -f1)

#CMD ["python","app/SEDES/main.py"]
