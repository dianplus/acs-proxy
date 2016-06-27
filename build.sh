docker build -t registry.aliyuncs.com/linhuatest/proxy:0.1 .
docker tag registry.aliyuncs.com/linhuatest/proxy:0.1 registry.aliyuncs.com/acs-access/proxy:0.1
docker push registry.aliyuncs.com/acs-access/proxy:0.1 && docker push registry.aliyuncs.com/linhuatest/proxy:0.1
