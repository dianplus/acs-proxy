import logging

logger = logging.getLogger("haproxy")


def get_acs_links(services, haproxy_service, project_name):
    if not project_name:
        raise Exception("Cannot read compose labels. Are you using docker compose V2?")
    links = {}
    linked_compose_services = []
    for service in services:
        if service.info:
            compose_labels = service.info.get("definition", {}).get("labels", {})
            compose_project = service.info.get("project")
            compose_service = service.info.get("name")
            linked_compose_services.append(service.info.get("name"))
            service_name = "%s_%s" % (compose_project, compose_service)
            for _container in service.containers:
                if compose_project == project_name:
                    container_id = _container["id"]
                    container_name = _container.get("name").lstrip("/")
                    container_evvvars = _get_container_envvars(compose_labels)
                    endpoints = _get_container_endpoints(_container, container_name, service.info)
                    if len(endpoints) > 0:
                        links[container_id] = {"service_name": service_name,
                                               "container_envvars": container_evvvars,
                                               "container_name": container_name,
                                               "endpoints": endpoints,
                                               "compose_service": compose_service,
                                               "compose_project": compose_project}
    return links, ["%s_%s" % (project_name, service) for service in linked_compose_services]


def _get_container_endpoints(container, container_name, info):
    logger.info("container: %s" % container)
    logger.info("info: %s" % info)
    endpoints = {}
    port_list = info.get("container_config", {}).get("ExposedPorts", [])
    if not port_list:
        port_list = []
    logger.info(port_list)
    service_port_map = info.get("definition", {}).get("ports", [])
    logger.info(service_port_map)
    service_port_list = []
    for port in service_port_map:
        iterms = port.split(":", 1)
        if len(iterms) == 2:
            service_port_list.append(iterms[1])
        else:
            service_port_list.append(iterms[0])
    if len(service_port_list) > 0:
        port_list = service_port_list
    for k in port_list:
        terms = k.split("/", 1)
        port = terms[0]
        if len(terms) == 2:
            protocol = terms[1]
        else:
            protocol = "tcp"
        if container.get("status") == "running" and container.get("health") == "success":
            endpoint = "%s://%s:%s" % (protocol, container.get("ip"), port)
            endpoints[k] = endpoint
    return endpoints


def _get_container_envvars(compose_labels):
    container_evvvars = []
    for k, v in compose_labels.iteritems():
        if k.startswith("aliyun.proxy."):
            container_evvvar = dict()
            container_evvvar["key"] = k[len("aliyun.proxy."):]
            container_evvvar["value"] = v
            container_evvvars.append(container_evvvar)
    return container_evvvars


def _get_linked_compose_services(networks, project):
    prefix = "%s_" % project
    prefix_len = len(prefix)

    haproxy_links = []
    for network in networks.itervalues():
        network_links = network.get("Links", [])
        if network_links:
            haproxy_links.extend(network_links)

    linked_services = []
    for link in haproxy_links:
        terms = link.strip().split(":")
        service = terms[0].strip()
        if service and service.startswith(prefix):
            last = service.rfind("_")
            linked_service = service[prefix_len:last]
            if linked_service not in linked_services:
                linked_services.append(linked_service)
    return linked_services


def get_service_links_str(links):
    return sorted(set([link.get("service_name") for link in links.itervalues()]))


def get_container_links_str(haproxy_links):
    return sorted(set([link.get("container_name") for link in haproxy_links.itervalues()]))
