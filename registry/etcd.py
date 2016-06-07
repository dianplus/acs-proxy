import etcd
import log
import json
import sys
import os
#            "CLUSTER_ID=cd1f9462240b44bbf948bc5b0ea843327",
#            "ETCD_NODES=100.98.238.166:2379",
#            "TLS_CACERTFILE=/etc/docker/acs-ca.pem",
#            "TLS_CERTFILE=/etc/docker/service.pem",
#            "TLS_KEYFILE=/etc/docker/service-key.pem",



#
# client = etcd.Client(host='100.98.238.166',
#                      protocol='https',
#                      port=2379,
#                      cert=('/Users/tanlinhua/cs_code/customized-routing-image/etc/docker/service.pem', '/Users/tanlinhua/cs_code/customized-routing-image/etc/docker/service-key.pem'),
#                      allow_reconnect=True,
#                      ca_cert='/Users/tanlinhua/cs_code/customized-routing-image/etc/docker/acs-ca.pem',
#                      version_prefix="/v2/keys/cd1f9462240b44bbf948bc5b0ea843327")

CONTAINERS_POSTFIX = "/containers"
INFO_POSTFIX = "/info"
ETCD_PREFIX = "/default"
REGISTRY_BASE = "/registry"
SERVICE_BASE = REGISTRY_BASE + "/services"
SERVICE_PREFIX = SERVICE_BASE + "/"
SERVICE_CONTAINERS_TMPL = SERVICE_PREFIX + "%s" + CONTAINERS_POSTFIX


# client = etcd.Client(host='192.168.99.100',
#                      protocol='http',
#                      port=2379,
#                      allow_reconnect=True)
# print client.machines
# print client.leader
# print client.read("/test/registry/hosts/192.168.99.100", recursive = True).value
etcd_client = None


def get_etcd_client(host, port, cert, ca_cert):
    client = etcd.Client(host=host,
                         port=port,
                         cert=cert,
                         ca_cert=ca_cert,
                         allow_reconnect=True)
    etcd_client = client
    return client

def get_services_base_uri():
    return ETCD_PREFIX + SERVICE_BASE

def get_service_base_uri(service_id):
    return ETCD_PREFIX + SERVICE_PREFIX + service_id

def parse_service(service_reg):
    service = {}
    service.containers = []
    for node in service_reg['nodes']:
        if node['key'].endswith('/info'):
            info = json.loads(node['value'])
            service.id = info.id
            service.info = info
        elif node['key'].endswith('/containers'):
            for contaienr in node['nodes']:
                contaienr_state = json.loads(contaienr['value'])
                contaienr_state.id = os.path.basename(contaienr['key'])
                service.containers.append(contaienr_state)
    return service

def parse_services(services_reg):
    services = {}
    for child in services_reg._children:
        service = parse_service(child)
        services.append(service)
    return services

def get_service_info(service_uri):
    result = etcd_client.read(service_uri, recursive = True)
    wait_index = result.etcd_index
    service_info = parse_service(result)
    return service_info, wait_index

def get_services_info():
    uri = get_services_base_uri()
    result = etcd_client.read(uri, recursive = True)
    wait_index = result.etcd_index
    services = parse_services(result)
    return services, wait_index

def watch_prefix(etcd_client, uri, wait_index):
    try:
        if wait_index == 0:
            result = etcd_client.read(uri, recursive = True)
            wait_index = result.etcd_index
            return result, wait_index
        else:
            result = etcd_client.read(uri, wait = True, recursive = True, waitIndex=wait_index)
            wait_index = result.modifiedIndex
            return result, wait_index

    except etcd.EtcdKeyNotFound:
        log.warn("key %s not found" % get_services_base_uri())
        return None, wait_index
    except:
        log.error("Unexpected error: %s" % sys.exc_info()[0])
        raise


def list_services_status():


def list_services_by_project():


def get_service_env():


def get_service_label():
