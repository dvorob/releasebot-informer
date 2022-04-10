FROM python:3.9.1-slim

WORKDIR /opt

COPY requirements.txt ./

RUN apt-get -y update  && apt-get install -fy ca-certificates  && \
    apt-get -y autoremove  && \
    apt-get clean && rm -rf /var/lib/apt/lists/*  && \
    pip3 install --no-cache-dir --trusted-host nexus.yamoney.ru -i https://nexus.yamoney.ru/repository/pypi-proxy-pypi.org/simple \
    -r requirements.txt && rm /etc/localtime /etc/apt/sources.list && ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY app ./app

CMD [ "python3", "./app/informer.py" ]