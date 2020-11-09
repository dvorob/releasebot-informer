#!/bin/bash

if [ -z ${1} ]; then
    echo 'input informer buld number'
    echo './deploy.sh 1'
else
    docker build . -f informer.Dockerfile --compress -t docker-ym.nexus.yamoney.ru/yamoney/releasebot-informer:${1} && \
    docker push docker-ym.nexus.yamoney.ru/yamoney/releasebot-informer:${1}
fi
