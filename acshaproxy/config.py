from haproxy.config import *


ACS_LINK_MODE = os.getenv("ACS_LINK_MODE", "true")


CLUSTER_ID=os.getenv("CLUSTER_ID")
ETCD_NODES=os.getenv("ETCD_NODES")
TLS_CACERTFILE=os.getenv("TLS_CACERTFILE")
TLS_CERTFILE=os.getenv("TLS_CERTFILE")
TLS_KEYFILE=os.getenv("TLS_KEYFILE")
IMAGE_VERSION="HEAD"
