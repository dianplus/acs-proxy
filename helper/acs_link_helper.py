import logging

logger = logging.getLogger("haproxy")


def get_acs_links(services, haproxy_service, project_name):
    if not project_name:
        raise Exception("Cannot read compose labels. Are you using docker compose V2?")
    links = {}
    linked_compose_services = []
    for service in services:
        for _container in service.containers:
            container_id = _container.id
            compose_labels = service.info.get("definition", {}).get("labels", {})
            compose_project = compose_labels.get("com.docker.compose.project", "")
            compose_service = compose_labels.get("com.docker.compose.service", "")
            if compose_project == project_name:
                linked_compose_services.append(service.info.get("name"))
                service_name = "%s_%s" % (compose_project, compose_service)
                container_name = _container.get("name").lstrip("/")
                container_evvvars = _get_container_envvars(compose_labels)
                endpoints = _get_container_endpoints(_container, container_name, service.info)
                links[container_id] = {"service_name": service_name,
                                       "container_envvars": container_evvvars,
                                       "container_name": container_name,
                                       "endpoints": endpoints,
                                       "compose_service": compose_service,
                                       "compose_project": compose_project}
    return links, ["%s_%s" % (project_name, service) for service in linked_compose_services]


def _get_container_endpoints(container, container_name, info):
    endpoints = {}
    for k in info.get("definition", {}).get("ports", []):
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
            container_evvvar = {"key": k[len("aliyun.proxy."):]}
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
