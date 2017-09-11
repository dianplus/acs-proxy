#! /bin/bash

set -e

GIT_SHA=`git rev-parse --short HEAD || echo "HEAD"`
VERSION=`cat ./acshaproxy/__init__.py | awk -F"\"" '{ print $2 }'`
IMAGE_VERSION=$VERSION-$GIT_SHA

function cleanup() {
	mv acshaproxy/config.py.bak acshaproxy/config.py
}

trap cleanup  EXIT
sed -i.bak "s/HEAD/$IMAGE_VERSION/g" ./acshaproxy/config.py

docker build -t registry.aliyuncs.com/acs-sample/proxy:$VERSION .
docker tag registry.aliyuncs.com/acs-sample/proxy:$VERSION registry.aliyuncs.com/acs-sample/proxy:$VERSION-$GIT_SHA 
docker push registry.aliyuncs.com/acs-sample/proxy:$VERSION
docker push registry.aliyuncs.com/acs-sample/proxy:$VERSION-$GIT_SHA

