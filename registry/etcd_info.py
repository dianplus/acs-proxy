import etcd
import logging
import json
import sys
import os

logging.basicConfig()
logger = logging.getLogger("haproxy")

CONTAINERS_POSTFIX = "/containers"
INFO_POSTFIX = "/info"
etcd_prefix = "/default"
REGISTRY_BASE = "/registry"
SERVICE_BASE = REGISTRY_BASE + "/services"
SERVICE_PREFIX = SERVICE_BASE + "/"
SERVICE_CONTAINERS_TMPL = SERVICE_PREFIX + "%s" + CONTAINERS_POSTFIX

etcd_client = None


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


def get_etcd_client(host, port, cert, ca_cert, read_timeout=60):
    client = etcd.Client(host=host,
                         port=port,
                         cert=cert,
                         ca_cert=ca_cert,
                         read_timeout=read_timeout,
                         allow_reconnect=True)
    global etcd_client
    etcd_client = client
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
                info = json.loads(tree.value)
            except ValueError:
                logger.warn("json loads failed %s" % tree)
            service.id = info["id"]
            service.info = info
        elif tree.key.endswith('/containers'):
            for container in tree.leaves:
                try:
                    container_state = json.loads(container.value)
                except ValueError:
                    logger.warn("json loads failed %s" % container)
                container_state["id"] = os.path.basename(container.key)
                service.containers.append(container_state)

    return service


def parse_services(services_reg):
    services = []
    for child in services_reg.get_subtree():
        if len(child.key.split("/")) == 5:
            service = parse_service(child)
            services.append(service)
    return services


def get_service_info(service_uri):
    result = etcd_client.read(service_uri, recursive=True)
    wait_index = result.etcd_index
    service_info = parse_service(result)
    return service_info, wait_index


def get_services_info():
    uri = get_services_base_uri()
    result = etcd_client.read(uri, recursive=True)
    wait_index = result.etcd_index
    services = parse_services(result)
    return services, wait_index


def watch_prefix(etcd_client, uri, wait_index):
    try:
        if wait_index == 0:
            result = etcd_client.read(uri, recursive=True)
            wait_index = result.etcd_index
            return result, wait_index + 1
        else:
            result = etcd_client.read(uri, wait=True, recursive=True, waitIndex=wait_index)
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
        raise


def list_services_status():
    return None


def list_services_by_project():
    return None


def get_service_env():
    return None


def get_service_label():
    return None
