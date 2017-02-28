import etcd_info
import logging
import sys

logger = logging.getLogger("haproxy")


class Events(object):
    def __init__(self):
        self.message_handler = None

    def on_message(self, handler):
        self.message_handler = handler

    def run_forever(self, *args, **kwargs):
        etcd_client = etcd_info.get_etcd_client()
        wait_index = 0
        while True:
            logger.info("watch with index: %s" % wait_index)
            result, wait_index = etcd_info.watch_prefix(etcd_client, etcd_info.get_services_base_uri(), wait_index)
            logger.info("got result")
            if result is not None:
                # read the info
                try:
                    services_info_reg, _ = etcd_info.get_services_info(etcd_client)
                except Exception:
                    logger.warn("Unexpected error: %s" % sys.exc_info()[0])
                else: # find the etcd action and log it
                    self.message_handler(services_info_reg)
