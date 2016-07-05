#! /bin/bash

set -e
GIT_SHA=`git rev-parse --short HEAD || echo "HEAD"`
VERSION=0.5
export IMAGE_VERSION=$VERSION-$GIT_SHA


function cleanup() {
        mv acshaproxy/config.py.bak acshaproxy/config.py
}

trap cleanup  EXIT
sed -i.bak "s/HEAD/$IMAGE_VERSION/g" ./acshaproxy/config.py

docker build -t registry.aliyuncs.com/acs-access/proxy:$VERSION .
docker tag registry.aliyuncs.com/acs-access/proxy:$VERSION registry.aliyuncs.com/acs/proxy:$VERSION
docker tag registry.aliyuncs.com/acs-access/proxy:$VERSION registry.aliyuncs.com/acs/proxy:$VERSION-$GIT_SHA

docker push registry.aliyuncs.com/acs-access/proxy:$VERSION
docker push registry.aliyuncs.com/acs/proxy:$VERSION
docker push registry.aliyuncs.com/acs/proxy:$VERSION-$GIT_SHA

