FROM python:3.8.1-slim

WORKDIR /opt/YMreleasebot/informer

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt && \
    rm /etc/localtime /etc/apt/sources.list && ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime

COPY app/ymReleaseBot_informer.py ./
COPY app ./app

CMD [ "python3", "./ymReleaseBot_informer.py" ]