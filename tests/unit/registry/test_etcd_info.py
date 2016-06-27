import unittest
import sys
import haproxy.registry as registry
import haproxy.config as config
import os

print sys.path


class TestEtcd(unittest.TestCase):
    def setUp(self):
        os.environ["ETCD_NODES"] = "192.168.99.100:2379"
        os.environ["CLUSTER_ID"] = "test"
        config.CLUSTER_ID=os.getenv("CLUSTER_ID")
        config.ETCD_NODES=os.getenv("ETCD_NODES")
        self.client = registry.get_etcd_client()
        registry.set_cluster_id("test")

    def test_EtcdClient(self):

        service_url = registry.get_service_base_uri("wordpress_web")
        result = self.client.read(service_url)
        print result
        for leaf in result.leaves:
            print leaf.key
            print leaf.value
        for tree in result.get_subtree():
            print tree.key
            print tree.value
        print "================================="

    def test_parse_service(self):
        service_url = registry.get_service_base_uri("wordpress_web")
        service_info, _ = registry.get_service_info(self.client, service_url)
        print service_info
        print "================================="

    def test_parse_services(self):
        services_info, _ = registry.get_services_info(self.client)
        print len(services_info)
        for service_info in services_info:
            print service_info
        print "================================="

    def test_watch_prefix(self):
        service_url = registry.get_services_base_uri()
        service_watch, index = registry.watch_prefix(self.client, service_url, 22704)
        print service_watch
        print index


if __name__ == '__main__':
    unittest.main()
