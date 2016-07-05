import unittest
import os
import acshaproxy.config as config
import acshaproxy.registry as registry
import logging
from acshaproxy.acshaproxycfg import AcsHaproxy


class TestRunHaproxy(unittest.TestCase):
    def setUp(self):
        logging.getLogger("haproxy").setLevel(logging.DEBUG)
        registry.set_cluster_id("test")
        os.environ["HOSTNAME"] = "1234589-wordpress-web-1"
        os.environ["COMPOSE_PROJECT_NAME"] = "wordpress"
        os.environ["ETCD_NODES"] = "192.168.99.100:2379"
        os.environ["CLUSTER_ID"] = "test"
        os.environ["ADDITIONAL_SERVICES"] = "*"
        config.CLUSTER_ID=os.getenv("CLUSTER_ID")
        config.ETCD_NODES=os.getenv("ETCD_NODES")
        config.ADDITIONAL_SERVICES = os.getenv("ADDITIONAL_SERVICES")
        self.client = registry.get_etcd_client()

    def test_run_haproxy(self):
        haproxy = AcsHaproxy("acs", "ACS Event")
        haproxy.update()
        print "test ends"

if __name__ == '__main__':
    unittest.main()
