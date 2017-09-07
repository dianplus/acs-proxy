import logging
import os

import haproxy.helper.new_link_helper as NewLinkHelper
import haproxy.helper.update_helper as UpdateHelper
from haproxy.haproxycfg import Haproxy
from haproxy.parser.legacy_parser import LegacySpecs
from haproxy.parser.new_parser import NewSpecs
from haproxy.utils import save_to_file

import acs_link_helper as AcsLinkHelper
import config
import registry

logger = logging.getLogger("haproxy")


def run_haproxy(msg=None):
    haproxy = AcsHaproxy(config.LINK_MODE, msg)

    haproxy.update()


class AcsHaproxy(Haproxy):
    """extend Haproxy"""

    def __init__(self, link_mode="", msg=""):
        super(AcsHaproxy, self).__init__(link_mode, msg)
        self.specs = self._initialize(self.link_mode)

    @staticmethod
    def _initialize(link_mode):
        if link_mode == "acs":
            links = AcsHaproxy._init_acs_links()
            if links is None:
                specs = LegacySpecs()
            else:
                specs = NewSpecs(links)
        else:
            specs = LegacySpecs()
        return specs

    @staticmethod
    def _get_service_id(hostname, project_name):
        sub_string = "-" + project_name + "-"
        size = len(sub_string)
        index = hostname.find(sub_string)
        last_index = hostname.rfind("-")
        service_name = hostname[index + size:last_index]
        service_id = project_name + "_" + service_name
        return service_id

    @staticmethod
    def _get_service_filter(project_name):
        if config.ADDITIONAL_SERVICES == "*":
            return lambda project, service: True
        elif config.ADDITIONAL_SERVICES:
            return lambda project, service: (project + ":" + service) in (
                config.ADDITIONAL_SERVICES.split(",")) or project == project_name
        else:
            return lambda project, service: project == project_name

    @staticmethod
    def _init_acs_links():
        try:
            project_name = os.environ.get("COMPOSE_PROJECT_NAME")
            etcd_client = registry.get_etcd_client()
            services, _ = registry.get_services_info(etcd_client)
            logger.debug("services %s" % services)
            service_filter = AcsHaproxy._get_service_filter(project_name)
        except Exception as e:
            logger.info("acs registry API error, regressing to legacy links mode: %s" % str(e))
            return None
        links, Haproxy.cls_linked_services = AcsLinkHelper.get_acs_links(services, service_filter)
        logger.debug("Linked service: %s", ", ".join(NewLinkHelper.get_service_links_str(links)))
        logger.debug("Linked container: %s", ", ".join(NewLinkHelper.get_container_links_str(links)))
        logger.debug("links %s" % links)
        return links

    def _update_haproxy(self, cfg):
        if self.link_mode in ["acs"]:
            if Haproxy.cls_cfg != cfg:
                logger.info("HAProxy configuration:\n%s" % cfg)
                Haproxy.cls_cfg = cfg
                if save_to_file(config.HAPROXY_CONFIG_FILE, cfg):
                    Haproxy.cls_process = UpdateHelper.run_reload(Haproxy.cls_process)
            elif self.ssl_updated:
                logger.info("SSL certificates have been changed")
                Haproxy.cls_process = UpdateHelper.run_reload(Haproxy.cls_process)
            else:
                logger.info("HAProxy configuration remains unchanged")
            logger.info("===========END===========")
        elif self.link_mode in ["legacy"]:
            logger.info("HAProxy configuration:\n%s" % cfg)
            if save_to_file(config.HAPROXY_CONFIG_FILE, cfg):
                UpdateHelper.run_once()
