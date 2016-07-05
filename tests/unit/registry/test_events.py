import unittest
import acshaproxy.registry as registry
import os
import acshaproxy.config as config
import logging


def test_call_back(info):
    print "hit call back"
    print info


class TestEvents(unittest.TestCase):
    def setUp(self):
        logging.getLogger("haproxy").setLevel(logging.DEBUG)
        os.environ["ETCD_NODES"] = "192.168.99.100:2379"
        os.environ["CLUSTER_ID"] = "test"
        config.CLUSTER_ID=os.getenv("CLUSTER_ID")
        config.ETCD_NODES=os.getenv("ETCD_NODES")

    def test_run_forever(self):
        event = registry.Events()
        event.on_message(test_call_back)
        event.run_forever()


if __name__ == '__main__':
    unittest.main()
