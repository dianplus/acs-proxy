import os
import re


def parse_extra_bind_settings(extra_bind_settings):
    bind_dict = {}
    if extra_bind_settings:
        settings = re.split(r'(?<!\\),', extra_bind_settings)
        for setting in settings:
            term = setting.split(":", 1)
            if len(term) == 2:
                bind_dict[term[0].strip().replace("\,", ",")] = term[1].strip().replace("\,", ",")
    return bind_dict


# envvar
DEFAULT_SSL_CERT = os.getenv("DEFAULT_SSL_CERT") or os.getenv("SSL_CERT")
EXTRA_SSL_CERT = os.getenv("EXTRA_SSL_CERTS")
DEFAULT_CA_CERT = os.getenv("CA_CERT")
MAXCONN = os.getenv("MAXCONN", "4096")
MODE = os.getenv("MODE", "http")
OPTION = os.getenv("OPTION", "redispatch, httplog, dontlognull, forwardfor")
RSYSLOG_DESTINATION = os.getenv("RSYSLOG_DESTINATION", "127.0.0.1")
SSL_BIND_CIPHERS = os.getenv("SSL_BIND_CIPHERS")
SSL_BIND_OPTIONS = os.getenv("SSL_BIND_OPTIONS")
STATS_AUTH = os.getenv("STATS_AUTH", "stats:stats")
STATS_PORT = os.getenv("STATS_PORT", "1936")
TIMEOUT = os.getenv("TIMEOUT", "connect 5000, client 50000, server 50000")
HEALTH_CHECK = os.getenv("HEALTH_CHECK", "check inter 2000 rise 2 fall 3")
EXTRA_GLOBAL_SETTINGS = os.getenv("EXTRA_GLOBAL_SETTINGS")
EXTRA_DEFAULT_SETTINGS = os.getenv("EXTRA_DEFAULT_SETTINGS")
EXTRA_BIND_SETTINGS = parse_extra_bind_settings(os.getenv("EXTRA_BIND_SETTINGS"))
HTTP_BASIC_AUTH = os.getenv("HTTP_BASIC_AUTH")
MONITOR_URI = os.getenv("MONITOR_URI")
MONITOR_PORT = os.getenv("MONITOR_PORT")
BALANCE = os.getenv("BALANCE", "roundrobin")
HAPROXY_CONTAINER_URI = os.getenv("DOCKERCLOUD_CONTAINER_API_URI")
HAPROXY_SERVICE_URI = os.getenv("DOCKERCLOUD_SERVICE_API_URI")
API_AUTH = os.getenv("DOCKERCLOUD_AUTH")
CA_CERT_FILE = os.getenv("CA_CERT_FILE")
CERT_FOLDER = os.getenv("CERT_FOLDER")
ADDITIONAL_SERVICES = os.environ.get("ADDITIONAL_SERVICES")
DEBUG = os.getenv("DEBUG", False)
LINK_MODE = ""

# envvar for acs routing
# "CLUSTER_ID=cf2ec3f580e894197aee7fbc083b88ed9",
# "ETCD_NODES=service1.cs-cn-shenzhen.aliyun-inc.com:2379",
# "TLS_CACERTFILE=/etc/docker/acs-ca.pem",
# "TLS_CERTFILE=/etc/docker/service.pem",
# "TLS_KEYFILE=/etc/docker/service-key.pem",
CLUSTER_ID=os.getenv("CLUSTER_ID")
ETCD_NODES=os.getenv("ETCD_NODES")
TLS_CACERTFILE=os.getenv("TLS_CACERTFILE")
TLS_CERTFILE=os.getenv("TLS_CERTFILE")
TLS_KEYFILE=os.getenv("TLS_KEYFILE")

# const
CERT_DIR = "/certs/"
CACERT_DIR = "/cacerts/"
HAPROXY_CONFIG_FILE = "/haproxy.cfg"
HAPROXY_RUN_COMMAND = ['/usr/sbin/haproxy', '-f', HAPROXY_CONFIG_FILE, '-db', '-q']
API_RETRY = 10  # seconds
PID_FILE = "/tmp/dockercloud-haproxy.pid"

# regular expressions
SERVICE_NAME_MATCH = re.compile(r"(.+)_\d+$")
BACKEND_MATCH = re.compile(r"(?P<proto>tcp|udp):\/\/(?P<addr>[^:]*):(?P<port>.*)")
SERVICE_ALIAS_MATCH = re.compile(r"_PORT_\d{1,5}_(TCP|UDP)$")
DETAILED_SERVICE_ALIAS_MATCH = re.compile(r"_\d+_PORT_\d{1,5}_(TCP|UDP)$")
ENV_SERVICE_ALIAS_MATCH = re.compile(r"_ENV_")
ENV_DETAILED_SERVICE_ALIAS_MATCH = re.compile(r"_\d+_ENV")
