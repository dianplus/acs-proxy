from gevent import monkey

monkey.patch_all()

import logging
import os
import signal
import sys

import dockercloud

import config
from haproxy.eventhandler import on_user_reload
from haproxy import __version__
from acshaproxycfg import run_haproxy
from haproxy.utils import save_to_file

# do monkey patch before import urllib3
import registry

dockercloud.user_agent = "dockercloud-haproxy/%s" % __version__

logger = logging.getLogger("haproxy")


def create_pid_file():
    pid = str(os.getpid())
    save_to_file(config.PID_FILE, pid)
    return pid


def on_acs_event(msg):
    logger.debug(msg)
    logger.debug("on acs event, reload the haproxy")
    run_haproxy("ACS Event")


def listen_acs_events():
    events = registry.Events()
    events.on_message(on_acs_event)
    events.run_forever()


def main():
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("haproxy").setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
    logger.info("starting image registry.aliyuncs.com/acs/proxy:%s ..." % config.IMAGE_VERSION)
    if config.DEBUG:
        logging.getLogger("python-dockercloud").setLevel(logging.DEBUG)

    config.LINK_MODE = "acs"
    signal.signal(signal.SIGUSR1, on_user_reload)
    signal.signal(signal.SIGTERM, sys.exit)

    pid = create_pid_file()
    logger.info("acs-sample/haproxy PID: %s" % pid)

    if config.LINK_MODE == "acs":
        listen_acs_events()
    elif config.LINK_MODE == "legacy":
        run_haproxy()


if __name__ == "__main__":
    main()
