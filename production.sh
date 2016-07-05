#! /bin/bash

set -e
GIT_SHA=`git rev-parse --short HEAD || echo "HEAD"`
VERSION=0.5
docker build -t registry.aliyuncs.com/acs-access/proxy:$VERSION .
docker tag registry.aliyuncs.com/acs-access/proxy:$VERSION registry.aliyuncs.com/acs/proxy:$VERSION
docker tag registry.aliyuncs.com/acs-access/proxy:$VERSION registry.aliyuncs.com/acs/proxy:$VERSION-$GIT_SHA
docker push registry.aliyuncs.com/acs/proxy:$VERSION
docker push registry.aliyuncs.com/acs/proxy:$VERSION-$GIT_SHA

