import etcd_info
import config
import logging
import sys

logger = logging.getLogger("haproxy")


class Events(object):
    def __init__(self):
        self.message_handler = None

    def on_message(self, handler):
        self.message_handler = handler

    def run_forever(self, *args, **kwargs):
        index = config.ETCD_NODES.index(':')
        host = config.ETCD_NODES[0:index]
        port = int(config.ETCD_NODES[index + 1:])
        etcd_info.set_cluster_id(config.CLUSTER_ID)
        etcd_client = etcd_info.get_etcd_client(host, port, (config.TLS_CERTFILE, config.TLS_KEYFILE),
                                                config.TLS_CACERTFILE)
        wait_index = 0
        while True:
            result, wait_index = etcd_info.watch_prefix(etcd_client, etcd_info.get_services_base_uri(), wait_index)
            if result is not None:
                # read the info
                try:
                    services_info_reg, _ = etcd_info.get_services_info()
                except Exception:
                    logger.warn("Unexpected error: %s" % sys.exc_info()[0])
                # find the etcd action and log it
                self.message_handler(services_info_reg)






