#! /bin/bash

set -e
docker build -t registry.aliyuncs.com/acs-access/proxy:0.5 .
docker tag registry.aliyuncs.com/acs-access/proxy:0.5 registry.aliyuncs.com/acs/proxy:0.5
docker push registry.aliyuncs.com/acs/proxy:0.5

