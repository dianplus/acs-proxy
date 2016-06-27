import unittest
import os
import haproxy.config as config
import haproxy.registry as registry
from haproxy.haproxycfg import Haproxy


class TestRunHaproxy(unittest.TestCase):
    def setUp(self):
        registry.set_cluster_id("test")
        os.environ["HOSTNAME"] = "1234589-wordpress-web-1"
        os.environ["COMPOSE_PROJECT_NAME"] = "wordpress"
        os.environ["ETCD_NODES"] = "192.168.99.100:2379"
        os.environ["CLUSTER_ID"] = "test"
        config.CLUSTER_ID=os.getenv("CLUSTER_ID")
        config.ETCD_NODES=os.getenv("ETCD_NODES")
        self.client = registry.get_etcd_client()

    def test_run_haproxy(self):
        haproxy = Haproxy("acs", "ACS Event")
        haproxy.update()

if __name__ == '__main__':
    unittest.main()
