import etcd
import config
import log
import sys




class Events(object):
    def __init__(self):


    def on_message(self, handler):
        self.message_handler = handler

    def run_forever(self, *args, **kwargs):
        index = config.ETCD_NODES.index(':')
        host =config.ETCD_NODES[0:index]
        port = config.ETCD_NODES[index + 1:]
        etcd_client = etcd.get_etcd_client(host, port, (config.TLS_CERTFILE, config.TLS_KEYFILE), config.TLS_CACERTFILE)
        wait_index = 0
        while True:
            result, wait_index = etcd.watch_prefix(etcd_client, etcd.get_services_base_uri(), wait_index+1)
            if result is not None:
                # read the info
                services_info_reg = etcd.get_services_info(etcd_client)
                # find the etcd action and log it
                self.message_handler(services_info_reg)
            else:
                log.error("Unexpected error: %s" % sys.exc_info()[0])




