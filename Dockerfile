FROM registry.cn-hangzhou.aliyuncs.com/acs-sample/haproxy:1.6.7

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/' /etc/apk/repositories
COPY pip.conf /root/.pip/pip.conf

COPY .  /acs-haproxy-src
RUN  cd /acs-haproxy-src/python-etcd && pip install .
RUN  cd /acs-haproxy-src && pip install .

EXPOSE 80 443 1936
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["acs-haproxy"]