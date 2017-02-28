import etcd
import logging
import json
import sys
import os
import acshaproxy.config as config

logger = logging.getLogger("haproxy")

CONTAINERS_POSTFIX = "/containers"
INFO_POSTFIX = "/info"
etcd_prefix = "/default"
REGISTRY_BASE = "/registry"
SERVICE_BASE = REGISTRY_BASE + "/services"
SERVICE_PREFIX = SERVICE_BASE + "/"
SERVICE_CONTAINERS_TMPL = SERVICE_PREFIX + "%s" + CONTAINERS_POSTFIX


class Service(object):
    def __init__(self, containers):
        self.containers = containers
        self.id = None
        self.info = None

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


def set_cluster_id(cluster_id):
    global etcd_prefix
    etcd_prefix = "/" + cluster_id


def get_etcd_client(read_timeout=60):
    if not config.ETCD_NODES or not config.CLUSTER_ID:
        logger.error("Environment variables ETCD_NODES or CLUSTER_ID are not set, aborting...")
        raise Exception("Environment variables ETCD_NODES or CLUSTER_ID are not set, aborting...")
    else:
        hosts_info = config.ETCD_NODES.split(",")
        host = ()
        for hostInfo in hosts_info:
            index = hostInfo.index(':')
            host_domain = hostInfo[0:index].strip()
            host_port = int(hostInfo[index + 1:].strip())
            host_pair = (host_domain, host_port)
            host = host + (host_pair,)

        set_cluster_id(config.CLUSTER_ID)
        etcd_client = _get_etcd_client(host, None, (config.TLS_CERTFILE, config.TLS_KEYFILE),
                                       config.TLS_CACERTFILE, read_timeout)
        return etcd_client


def _get_etcd_client(host, port, cert, ca_cert, read_timeout=60):
    if len(cert) > 0 and not cert[0]:
        protocol = "http"
    else:
        protocol = "https"
    client = etcd.Client(host=host,
                         port=port,
                         protocol=protocol,
                         cert=cert,
                         ca_cert=ca_cert,
                         read_timeout=read_timeout,
                         allow_reconnect=True)
    return client


def get_services_base_uri():
    return etcd_prefix + SERVICE_BASE


def get_service_base_uri(service_id):
    return etcd_prefix + SERVICE_PREFIX + service_id


def parse_service(service_reg):
    service = Service([])
    for tree in service_reg.get_subtree():
        if tree.key.endswith('/info'):
            try:
                if tree.value:
                    info = json.loads(tree.value)
                    service.id = info["id"]
                    service.info = info
            except ValueError:
                logger.warn("json loads failed %s" % tree)
        elif tree.key.endswith('/containers'):
            for container in tree.leaves:
                try:
                    if container.value:
                        container_state = json.loads(container.value)
                        container_state["id"] = os.path.basename(container.key)
                        service.containers.append(container_state)
                except ValueError:
                    logger.warn("json loads failed %s" % container)

    return service


def parse_services(services_reg):
    services = []
    for child in services_reg.get_subtree():
        if len(child.key.split("/")) == 5:
            service = parse_service(child)
            services.append(service)
    return services


def get_service_info(etcd_client, service_uri):
    result = etcd_client.read(service_uri, recursive=True)
    wait_index = result.etcd_index
    service_info = parse_service(result)
    return service_info, wait_index


def get_services_info(etcd_client):
    uri = get_services_base_uri()
    result = etcd_client.read(uri, recursive=True)
    wait_index = result.etcd_index
    services = parse_services(result)
    return services, wait_index


def watch_prefix(etcd_client, uri, wait_index):
    logger.debug("wait_index %s" % wait_index)
    try:
        if wait_index == 0:
            result = etcd_client.read(uri, recursive=True, timeout=600)
            wait_index = result.etcd_index
            return result, wait_index + 1
        else:
            result = etcd_client.read(uri, wait=True, recursive=True, waitIndex=wait_index, timeout=600)
            wait_index = result.modifiedIndex
            return result, wait_index + 1
    except etcd.EtcdKeyNotFound as e:
        logger.warn("key %s not found, err: %s" % get_services_base_uri(), e)
        return None, 0
    except etcd.EtcdEventIndexCleared as e:
        logger.warn("index has been cleared, err %s" % e)
        return None, 0
    except etcd.EtcdWatchTimedOut as e:
        logger.warn("watch time out, err %s" % e)
        return None, 0
    except etcd.EtcdConnectionFailed as e:
        logger.warn("connetion failed, need retry, err %s" % e)
        return None, 0
    except:
        logger.error("Unexpected error: %s" % sys.exc_info()[0])
        return None, 0


def list_services_status():
    return None


def list_services_by_project():
    return None


def get_service_env():
    return None


def get_service_label():
    return None
