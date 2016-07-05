# acs/proxy

自定义代理镜像，通过`FROM dockercloud/haproxy`的方式继承自镜像`dockercloud/haproxy`，动态感知容器的状态，做到后端容器负载均衡代理和服务发现。特点是将HAProxy负载均衡软件的所有配置都参数化了，方便用户自定义自己的需求和配置。该镜像的主要用于aliyun容器服务的默认路由服务不能满足用户的场景，方便用户对HAProxy进行自定义配置。

## 动态负载均衡代理和服务发现的原理

 - 镜像`acs/proxy`通过容器自身环境变量确定负载均衡的全局(GLOBAL)和默认(DEFAULT)的配置
 - 镜像`acs/proxy`侦听集群中的事件，例如容器状态的变化，发生变化后重新获取集群中相关容器的信息，确定最新的负载均衡配置
 - 镜像`acs/proxy`根据最新的负载均衡配置去重新加载（reload）该配置，使得该配置生效。

## 如何确定负载均衡的后端容器
 - 根据`acs/proxy`的环境变量`ADDITIONAL_SERVICES`来确定范围
   - ADDITIONAL_SERVICES: "*"                                                        # 范围为整个集群
   - ADDITIONAL_SERVICES: "project_name1:service_name1,project_name2:service_name2"  # 范围为当前应用和指定应用的指定服务
   - ADDITIONAL_SERVICES 不设置或者为空                                                # 范围为当前应用的容器
 - 根据每个容器的标签来确定是否加入`acs/proxy`的后端。
   - aliyun.proxy.VIRTUAL_HOST: "www.toolchainx.com"  # 加入后端，且域名为`www.toolchainx.com`
   - aliyun.proxy.required: "true"                    # 加入后端，且作为默认的后端

## 如何在前端绑定SLB
 - 使用自定义SLB标签，例如：aliyun.lb.port_80: 'tcp://proxy:80'

## 示例模板


    lb:
      image: registry.aliyuncs.com/acs/proxy:0.5
      ports:
       - '80:80'
      restart: always
      labels:
        aliyun.addon: "proxy"
        aliyun.global: "true"
        aliyun.lb.port_80: tcp://proxy:80
      environment:
        ADDITIONAL_SERVICES: "*"
    web:
      image: registry.aliyuncs.com/acs-sample/wordpress:4.5
      ports:
        - '80'
      environment:
        WORDPRESS_AUTH_KEY: changeme
        WORDPRESS_SECURE_AUTH_KEY: changeme
        WORDPRESS_LOGGED_IN_KEY: changeme
        WORDPRESS_NONCE_KEY: changeme
        WORDPRESS_AUTH_SALT: changeme
        WORDPRESS_SECURE_AUTH_SALT: changeme
        WORDPRESS_LOGGED_IN_SALT: changeme
        WORDPRESS_NONCE_SALT: changeme
        WORDPRESS_NONCE_AA: changeme
      restart: always
      links:
        - 'db:mysql'
      labels:
        aliyun.logs: /var/log
        aliyun.probe.url: http://container/license.txt
        aliyun.probe.initial_delay_seconds: '10'
        aliyun.proxy.VIRTUAL_HOST: www.toolchainx.com
        aliyun.scale: '3'
    db:
      image: registry.aliyuncs.com/acs-sample/mysql:5.7
      environment:
        MYSQL_ROOT_PASSWORD: password
      restart: always
      labels:
        aliyun.logs: /var/log/mysql


## 配置说明

### 通过`acs/proxy`镜像的环境变量设置全局（GLOBAL）和默认（DEFAULT）的配置 ###

Settings in this part is immutable, you have to redeploy HAProxy service to make the changes take effects

|Environment Variable|Default|Description|
|:-----:|:-----:|:----------|
|ADDITIONAL_SERVICES| |list of additional services to balance (es: `prj1:web,prj2:sql`). Discovery will be based on `com.docker.compose.[project|service]` container labels. This environment variable only works on compose v2, and the referenced services must be on a network resolvable and accessible to this containers.|
|BALANCE|roundrobin|load balancing algorithm to use. Possible values include: `roundrobin`, `static-rr`, `source`, `leastconn`. See:[HAProxy:balance](https://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-balance)|
|CA_CERT_FILE| |the path of a ca-cert file. This allows you to mount your ca-cert file directly from a volume instead of from envvar. If set, `CA_CERT` envvar will be ignored. Possible value: `/cacerts/cert0.pem`|
|CA_CERT| |CA cert for haproxy to verify the client. Use the same format as `DEFAULT_SSL_CERT`|
|CERT_FOLDER| |the path of certificates. This allows you to mount your certificate files directly from a volume instead of from envvars. If set, `DEFAULT_SSL_CERT` and `SSL_CERT` from linked services are ignored. Possible value:`/certs/`|
|DEFAULT_SSL_CERT| |Default ssl cert, a pem file content with private key followed by public certificate, '\n'(two chars) as the line separator. should be formatted as one line - see [SSL Termination](#ssl-termination)|
|EXTRA_BIND_SETTINGS| |comma-separated string(`<port>:<setting>`) of extra settings, and each part will be appended to the related port bind section in the configuration file. To escape comma, use `\,`. Possible value: `443:accept-proxy, 80:name http`|
|EXTRA_DEFAULT_SETTINGS| |comma-separated string of extra settings, and each part will be appended to DEFAULT section in the configuration file. To escape comma, use `\,`|
|EXTRA_FRONTEND\_SETTINGS\_&lt;PORT&gt;| |comma-separated string of extra settings, and each part will be appended frontend section with the port number specified in the name of the envvar. To escape comma, use `\,`. E.g. `EXTRA_FRONTEND_SETTINGS_80=balance source, maxconn 2000`|
|EXTRA_GLOBAL_SETTINGS| |comma-separated string of extra settings, and each part will be appended to GLOBAL section in the configuration file. To escape comma, use `\,`. Possible value: `tune.ssl.cachesize 20000, tune.ssl.default-dh-param 2048`|
|EXTRA_ROUTE_SETTINGS| |a string which is append to the each backend route after the health check, can be over written in the linked services. Possible value: "send-proxy"|
|EXTRA_SSL_CERTS| |list of extra certificate names separated by comma, eg. `CERT1, CERT2, CERT3`. You also need to specify each certificate as separate env variables like so: `CERT1="<cert-body1>"`, `CERT2="<cert-body2>"`, `CERT3="<cert-body3>"`|
|HEALTH_CHECK|check|set health check on each backend route, possible value: "check inter 2000 rise 2 fall 3". See:[HAProxy:check](https://cbonte.github.io/haproxy-dconv/configuration-1.5.html#5.2-check)|
|HTTP_BASIC_AUTH| |a comma-separated list of credentials(`<user>:<pass>`) for HTTP basic auth, which applies to all the backend routes. To escape comma, use `\,`. *Attention:* DO NOT rely on this for authentication in production|
|MAXCONN|4096|sets the maximum per-process number of concurrent connections.|
|MODE|http|mode of load balancing for HAProxy. Possible values include: `http`, `tcp`, `health`|
|MONITOR_PORT| |the port number where monitor_uri should be added to. Use together with `MONTIOR_URI`. Possible value: `80`|
|MONITOR_URI| |the exact URI which we want to intercept to return HAProxy's health status instead of forwarding the request.See: http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-monitor-uri. Possible value: `/ping`|
|OPTION|redispatch|comma-separated list of HAProxy `option` entries to the `default` section.|
|RSYSLOG_DESTINATION|127.0.0.1|the rsyslog destination to where HAProxy logs are sent|
|SKIP_FORWARDED_PROTO||If set to any value, HAProxy will not add an X-Forwarded- headers. This can be used when combining HAProxy with another load balancer|
|SSL_BIND_CIPHERS| |explicitly set which SSL ciphers will be used for the SSL server. This sets the HAProxy `ssl-default-bind-ciphers` configuration setting.|
|SSL_BIND_OPTIONS|no-sslv3|explicitly set which SSL bind options will be used for the SSL server. This sets the HAProxy `ssl-default-bind-options` configuration setting. The default will allow only TLSv1.0+ to be used on the SSL server.|
|STATS_AUTH|stats:stats|username and password required to access the Haproxy stats.|
|STATS_PORT|1936|port for the HAProxy stats section. If this port is published, stats can be accessed at `http://<host-ip>:<STATS_PORT>/`
|TIMEOUT|connect 5000, client 50000, server 50000|comma-separated list of HAProxy `timeout` entries to the `default` section.|

### 被代理的后端服务通过相应服务镜像的标签（LABEL）进行某一后端服务的配置###

即通过将标签（LABEL）写到后端服务的镜像上面来配置   
Settings here can overwrite the settings in HAProxy, which are only applied to the linked services. If run in Docker Cloud, when the service redeploys, joins or leaves HAProxy service, HAProxy service will automatically update itself to apply the changes

| Labels|Description|
|:-----:|:----------|
|aliyun.proxy.APPSESSION|sticky session option, possible value `JSESSIONID len 52 timeout 3h`. See:[HAProxy:appsession](http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-appsession)|
|aliyun.proxy.BALANCE|load balancing algorithm to use. Possible values include: `roundrobin`, `static-rr`, `source`, `leastconn`. See:[HAProxy:balance](https://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-balance)|
|aliyun.proxy.COOKIE|sticky session option. Possible value `SRV insert indirect nocache`. See:[HAProxy:cookie](http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-cookie)|
|aliyun.proxy.DEFAULT_SSL_CERT|similar to SSL_CERT, but stores the pem file at `/certs/cert0.pem` as the default ssl certs. If multiple `DEFAULT_SSL_CERT` are specified in linked services and HAProxy, the behavior is undefined|
|aliyun.proxy.EXCLUDE_PORTS|comma separated port numbers(e.g. 3306, 3307). By default, HAProxy will add all the ports exposed by the application services to the backend routes. You can exclude the ports that you don't want to be routed, like database port|
|aliyun.proxy.EXTRA_ROUTE_SETTINGS|a string which is append to the each backend route after the health check,possible value: "send-proxy"|
|aliyun.proxy.EXTRA_SETTINGS|comma-separated string of extra settings, and each part will be appended to either related backend section or listen session in the configuration file. To escape comma, use `\,`. Possible value: `balance source`|
|aliyun.proxy.FORCE_SSL|if set(any value) together with ssl termination enabled. HAProxy will redirect HTTP request to HTTPS request.
|aliyun.proxy.GZIP_COMPRESSION_TYPE|enable gzip compression. The value of this envvar is a list of MIME types that will be compressed, possible value: `text/html text/plain text/css`|
|aliyun.proxy.HEALTH_CHECK|set health check on each backend route, possible value: "check inter 2000 rise 2 fall 3". See:[HAProxy:check](https://cbonte.github.io/haproxy-dconv/configuration-1.5.html#5.2-check)|
|aliyun.proxy.HSTS_MAX_AGE|enable HSTS. It is an integer representing the max age of HSTS in seconds, possible value: `31536000`|
|aliyun.proxy.HTTP_CHECK|enable HTTP protocol to check on the servers health, possible value: "OPTIONS * HTTP/1.1\r\nHost:\ www". See:[HAProxy:httpchk](https://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-option%20httpchk)|
|aliyun.proxy.OPTION|comma-separated list of HAProxy `option` entries. `option` specified here will be added to related backend or listen part, and overwrite the OPTION settings in the HAProxy container|
|aliyun.proxy.SSL_CERT|ssl cert, a pem file with private key followed by public certificate, '\n'(two chars) as the line separator|
|aliyun.proxy.TCP_PORTS|comma separated ports(e.g. 9000, 9001, 2222/ssl). The port listed in `TCP_PORTS` will be load-balanced in TCP mode. Port ends with `/ssl` indicates that port needs SSL termination.
|aliyun.proxy.VIRTUAL_HOST_WEIGHT|an integer of the weight of an virtual host, used together with `VIRTUAL_HOST`, default:0. It affects the order of acl rules of the virtual hosts. The higher weight one virtual host has, the more priority that acl rules applies.|
|aliyun.proxy.VIRTUAL_HOST|specify virtual host and virtual path. Format: `[scheme://]domain[:port][/path], ...`. wildcard `*` can be used in `domain` and `path` part|

Check [the HAProxy configuration manual](http://cbonte.github.io/haproxy-dconv/configuration-1.5.html) for more information on the above.

## Virtual host and virtual path

Both virtual host and virtual path can be specified in environment variable `VIRTUAL_HOST`, which is a set of comma separated urls with the format of `[scheme://]domain[:port][/path]`.

|Item|Default|Description|
|:---:|:-----:|:---------|
|scheme|http|possible values: `http`, `https`, `wss`|
|domain||virtual host. `*` can be used as the wildcard|
|port|80/433|port number of the virtual host. When the scheme is `https`  `wss`, the default port will be to `443`|
|/path||virtual path, starts with `/`. `*` can be used as the wildcard|

#### examples of matching

|Virtual host|Match|Not match|
|:-----------|:----|:--------|
|http://domain.com|domain.com|www.domain.com|
|domain.com|domain.com|www.domain.com|
|domain.com:90|domain.com:90|domain.com|
|https://domain.com|https://domain.com|domain.com|
|https://domain.com:444|https://domain.com:444|https://domain.com|
|\*.domain.com|www.domain.com|domain.com|
|\*domain.com|www.domain.com, domain.com, anotherdomain.com|www.abc.com|
|www.e\*e.com|www.domain.com, www.exxe.com|www.axxa.com|
|www.domain.\*|www.domain.com, www.domain.org|domain.com|
|\*|any website with HTTP||
|https://\*|any website with HTTPS||
|\*/path|domain.com/path, domain.org/path?u=user|domain.com/path/|
|\*/path/|domain.com/path/, domain.org/path/?u=user|domain.com/path, domain.com/path/abc|
|\*/path/\*|domain.com/path/, domain.org/path/abc|domain.com/abc/path/
|\*/\*/path/\*|domain.com/path/, domain.org/abc/path/, domain.net/abc/path/123|domain.com/path|
|\*/\*.js|domain.com/abc.js, domain.org/path/abc.js|domain.com/abc.css|
|\*/\*.do/|domain.com/abc.do/, domain.org/path/abc.do/|domain.com/abc.do|
|\*/path/\*.php|domain.com/path/abc.php|domain/abc.php, domain.com/root/abc.php|
|\*.domain.com/\*.jpg|www.domain.com/abc.jpg, abc.domain.com/123.jpg|domain.com/abc.jpg|
|\*/path, \*/path/|domain.com/path, domain.org/path/||
|domain.com:90, https://domain.com | domain.com:90, https://domain.com   ||

**Note**:
1. The sequence of the acl rules generated based on VIRTUAL_HOST are random. In HAProxy, when an acl rule with a wide scope(e.g. *.domain.com) is put before a rule with narrow scope(e.g. web.domain.com), the narrow rule will never be reached. As a result, if the virtual hosts you set have overlapping scopes, you need to use `VIRTUAL_HOST_WEIGHT` to manually set the order of acl rules, namely, giving the narrow virtual host a higher weight than the wide one.
2. Every service that has the same VIRTUAL_HOST environment variable setting will be considered and merged into one single service. It may be useful for some testing scenario.

## SSL termination

`acs/proxy` supports ssl termination on multiple certificates. For each application that you want ssl terminates, simply set `SSL_CERT` and `VIRTUAL_HOST`. HAProxy, then, reads the certificate from the link environment and sets the ssl termination up.

**Attention**: there was a bug that if an environment variable value contains "=", which is common in the `SSL_CERT`, docker skips that environment variable. As a result, multiple ssl termination only works on docker 1.7.0 or higher.

SSL termination is enabled when:

1. at least one SSL certificate is set, and
2. either `VIRTUAL_HOST` is not set, or it is set with "https" as the scheme.

To set SSL certificate, you can either:

1. set `DEFAULT_SSL_CERT` in `acs/proxy`, or
2. set `aliyun.proxy.SSL_CERT` and/or `DEFAULT_SSL_CERT` in the application services linked to HAProxy

The difference between `aliyun.proxy.SSL_CERT` and `DEFAULT_SSL_CERT` is that, the multiple certificates specified by `SSL_CERT` are stored in as cert1.pem, cert2.pem, ..., whereas the one specified by `DEFAULT_SSL_CERT` is always stored as cert0.pem. In that case, HAProxy will use cert0.pem as the default certificate when there is no SNI match. However, when multiple `DEFAULT_SSL_CERTIFICATE` is provided, only one of the certificates can be stored as cert0.pem, others are discarded.

#### PEM Files
The certificate specified in `acs/proxy` or in the linked application services is a pem file, containing a private key followed by a public certificate(private key must be put before the public certificate and any extra Authority certificates, order matters). You can run the following script to generate a self-signed certificate:

	openssl req -x509 -newkey rsa:2048 -keyout key.pem -out ca.pem -days 1080 -nodes -subj '/CN=*/O=My Company Name LTD./C=US'
	cp key.pem cert.pem
	cat ca.pem >> cert.pem

Once you have the pem file, you can run this command to convert the file correctly to one line:

	awk 1 ORS='\\n' cert.pem

Copy the output and set it as the value of `aliyun.proxy.SSL_CERT` or `DEFAULT_SSL_CERT`.

## Affinity and session stickiness

There are three method to setup affinity and sticky session:

1. set `aliyun.proxy.BALANCE=source` in your application service. When setting `source` method of balance, HAProxy will hash the client IP address and make sure that the same IP always goes to the same server.
2. set `aliyun.proxy.APPSESSION=<value>`. use application session to determine which server a client should connect to. Possible value of `<value>` could be `JSESSIONID len 52 timeout 3h`
2. set `aliyun.proxy.COOKIE=<value>`. use application cookie to determine which server a client should connect to. Possible value of `<value>` could be `SRV insert indirect nocache`

Check [HAProxy:appsession](http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-appsession) and [HAProxy:cookie](http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#4-cookie) for more information.


## TCP load balancing

By default, `acs/proxy` runs in `http` mode. If you want a linked service to run in a `tcp` mode, you can specify the environment variable `TCP_PORTS`, which is a comma separated ports(e.g. 9000, 9001).

For example, if you run:

	docker --name app-1 --expose 9000 --expose 9001 -e TCP_PORTS="9000, 9001" your_app
	docker --name app-2 --expose 9000 --expose 9001 -e TCP_PORTS="9000, 9001" your_app
	docker run --link app-1:app-1 --link app-2:app-2 -p 9000:9000, 9001:9001 acs/proxy

Then, haproxy balances the load between `app-1` and `app-2` in both port `9000` and `9001` respectively.

Moreover, If you have more exposed ports than `TCP_PORTS`, the rest of the ports will be balancing using `http` mode.

For example, if you run:

	docker --name app-1 --expose 80 --expose 22 -e TCP_PORTS=22 your_app
	docker --name app-2 --expose 80 --expose 22 -e TCP_PORTS=22 your_app
	docker run --link app-1:app-2 --link app-2:app-2 -p 80:80 -p 22:22 acs/proxy

Then, haproxy balances in `http` mode at port `80` and balances in `tcp` on port at port `22`.

In this way, you can do the load balancing both in `tcp` and in `http` at the same time.

In `TCP_PORTS`, if you set port that ends with '/ssl', for example `2222/ssl`, HAProxy will set ssl termination on port `2222`.

Note:

1. You are able to set `VIRTUAL_HOST` and `TCP_PORTS` at the same them, giving more control on `http` mode.
2. Be careful that, the load balancing on `tcp` port is applied to all the services. If you link two(or more) different services using the same `TCP_PORTS`, `acs/proxy` considers them coming from the same service.

## WebSocket support
-----------------

There are two ways to enable the support of websocket:

1. As websocket starts using HTTP protocol, you can use virtual host to specify the scheme using `ws` or `wss`. For example, `-e VIRTUAL_HOST="ws://ws.domain.com, wss://wss.domain.com"
2. Websocket itself is a TCP connection, you can also try the TCP load balancing mentioned in the previous section.


## Use case scenarios

#### My webapp container exposes port 8080(or any other port), and I want the proxy to listen in port 80

Use the following:

    docker run -d --expose 80 --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -p 80:80 acs/proxy

#### My webapp container exposes port 80 and database ports 8083/8086, and I want the proxy to listen in port 80 without my database ports added to haproxy

    docker run -d -e EXCLUDE_PORTS=8803,8806 --expose 80 --expose 8033 --expose 8086 --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -p 80:80 acs/proxy

#### My webapp container exposes port 8080(or any other port), and I want the proxy to listen in port 8080

Use the following:

    docker run -d --expose 8080 --name webapp your_app
    docker run -d --link webapp:webapp -p 8080:80 acs/proxy

#### I want the proxy to terminate SSL connections and forward plain HTTP requests to my webapp to port 8080(or any port)

Use the following:

    docker run -d -e SSL_CERT="YOUR_CERT_TEXT" --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -p 443:443 -p 80:80 acs/proxy

or

    docker run -d --link webapp:webapp -p 443:443 -p 80:80 -e DEFAULT_SSL_CERT="YOUR_CERT_TEXT" acs/proxy

The certificate in `YOUR_CERT_TEXT` is a combination of private key followed by public certificate. Remember to put `\n` between each line of the certificate. A way to do this, assuming that your certificate is stored in `~/cert.pem`, is running the following:

    docker run -d --link webapp:webapp -p 443:443 -p 80:80 -e DEFAULT_SSL_CERT="$(awk 1 ORS='\\n' ~/cert.pem)" acs/proxy

#### I want the proxy to terminate SSL connections and redirect HTTP requests to HTTPS

Use the following:

    docker run -d -e FORCE_SSL=yes -e SSL_CERT="YOUR_CERT_TEXT" --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -p 443:443 acs/proxy

#### I want to load my SSL certificate from volume instead of passing it through environment variable

You can use `CERT_FOLDER` envvar to specify which folder the certificates are mounted in the container, using the following:

    docker run -d --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -e CERT_FOLDER="/certs/" -v $(pwd)/cert1.pem:/certs/cert1.pem -p 443:443 acs/proxy

#### I want to set up virtual host routing by domain

Virtual hosts can be configured by the proxy reading linked container environment variables (`VIRTUAL_HOST`). Here is an example:

    docker run -d -e VIRTUAL_HOST="www.webapp1.com, www.webapp1.org" --name webapp1 dockercloud/hello-world
    docker run -d -e VIRTUAL_HOST=www.webapp2.com --name webapp2 your/webapp2
    docker run -d --link webapp1:webapp1 --link webapp2:webapp2 -p 80:80 acs/proxy

In the example above, when you access `http://www.webapp1.com` or `http://www.webapp1.org`, it will show the service running in container `webapp1`, and `http://www.webapp2.com` will go to container `webapp2`.

If you use the following:

    docker run -d -e VIRTUAL_HOST=www.webapp1.com --name webapp1 dockercloud/hello-world
    docker run -d -e VIRTUAL_HOST=www.webapp2.com --name webapp2-1 dockercloud/hello-world
    docker run -d -e VIRTUAL_HOST=www.webapp2.com --name webapp2-2 dockercloud/hello-world
    docker run -d --link webapp1:webapp1 --link webapp2-1:webapp2-1 --link webapp2-2:webapp2-2 -p 80:80 acs/proxy

When you access `http://www.webapp1.com`, it will show the service running in container `webapp1`, and `http://www.webapp2.com` will go to both containers `webapp2-1` and `webapp2-2` using round robin (or whatever is configured in `BALANCE`).

#### I want all my `*.node.io` domains point to my service

    docker run -d -e VIRTUAL_HOST="*.node.io" --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -p 80:80 acs/proxy

#### I want `web.domain.com` go to one service and `*.domain.com` go to another service

    docker run -d -e VIRTUAL_HOST="web.domain.com" -e VIRTUAL_HOST_WEIGHT=1 --name webapp dockercloud/hello-world
    docker run -d -e VIRTUAL_HOST="*.domain.com" -e VIRTUAL_HOST_WEIGHT=0 --name app dockercloud/hello-world
    docker run -d --link webapp:webapp --link app:app -p 80:80 acs/proxy

#### I want all the requests to path `/path` point to my service

	docker run -d -e VIRTUAL_HOST="*/path, */path/*" --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -p 80:80 acs/proxy

#### I want all the static html request point to my service

	docker run -d -e VIRTUAL_HOST="*/*.htm, */*.html" --name webapp dockercloud/hello-world
    docker run -d --link webapp:webapp -p 80:80 acs/proxy

#### I want to see stats of HAProxy

	docker run -d --link webapp:webapp -e STATS_AUTH="auth:auth" -e STATS_PORT=1936 -p 80:80 -p 1936:1936 acs/proxy

#### I want to send all my logs to papertrailapp

Replace `<subdomain>` and `<port>` with your the values matching your papertrailapp account:

    docker run -d --name web1 dockercloud/hello-world
    docker run -d --name web2 dockercloud/hello-world
    docker run -it --env RSYSLOG_DESTINATION='<subdomain>.papertrailapp.com:<port>' -p 80:80 --link web1:web1 --link web2:web2 acs/proxy

## Topologies using virtual hosts


阿里云容器服务代理拓扑图

                                                               |---- container_a1
                                        |----- service_a ----- |---- container_a2
                                        |   (virtual host a)   |---- container_a3
    internet --- SLB -- acs/proxy--- |
                                        |                      |---- container_b1
                                        |----- service_b ----- |---- container_b2
                                            (virtual host b)   |---- container_b3

## Manually reload haproxy

In most cases, `acs/proxy` will configure itself automatically when the linked services change, you don't need to reload it manually. But for some reason, if you have to do so, here is how:

* `docker exec <haproxy_id> /reload.sh`, if you are on the node where acs/proxy deploys
