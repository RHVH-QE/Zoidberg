"""Module Doc Here
"""
import time
import logging
from threading import Thread
from kickstarts import KickStartFiles
from constants import CURRENT_IP_PORT
from beaker import BeakerProvision, MonitorPubSub

logger = logging.getLogger('bender')


class JobRunner(Thread):
    """class doc here
    """

    def __init__(self, build_url, rd_conn, results_logs):
        super(JobRunner, self).__init__()
        self.daemon = True
        self.build_url = build_url
        self.rd_conn = rd_conn
        self.results_logs = results_logs
        self.ksins = KickStartFiles(dict(liveimg=build_url,
                                         srv_ip=CURRENT_IP_PORT[0],
                                         srv_port=CURRENT_IP_PORT[1]))
        self.job_queue = self.get_job_queue()
        self._debug = False

    def _wait_for_installation(self, p):
        while True:
            time.sleep(5)
            logger.info("waiting for installation done")
            msg = p.get_message(ignore_subscribe_messages=True)

            if msg:
                if msg['data'] == 'success':
                    logger.info('autoinstallation job is success')
                    return True

                elif msg['data'] == 'fail':
                    logger.info('autoinstallation job is fail')
                    return False

    def _wait_for_cockpit(self, bkr_name):
        pubsub_cockpit = self.rd_conn.pubsub()
        pubsub_cockpit.subscribe("{0}-cockpit".format(bkr_name))
        while True:
            time.sleep(2)
            msg = pubsub_cockpit.get_message(ignore_subscribe_messages=True)
            logger.info(msg)
            if msg:
                if msg['data'] == 'done':
                    logger.info("cockpit test is done")
                    return True

    def run(self):
        """pass"""
        for ks, ml in self.job_queue:
            self.results_logs.get_actual_logger(self.build_url, ks)

            logger.info("start provisioning on host %s with %s", ml[0], ks)
            bp = BeakerProvision(srv_ip=CURRENT_IP_PORT[0],
                                 srv_port=CURRENT_IP_PORT[1],
                                 ks_file=ks)

            if self._debug:
                logger.debug("now is debug mode, will not do provisioning")
                ret = 0
            else:
                bp.reserve(ml[0])
                ret = bp.provision(ml[0])

            logger.info(self.results_logs.current_log_path)

            if ret == 0:
                logger.info(
                    "provisioning on host %s finished with kickstart file %s return code 0",
                    ml[0], ks)
                p = self.rd_conn.pubsub(ignore_subscribe_messages=True)

                logger.info("subscribe channel %s", ml[0])
                p.subscribe(ml[0])
                logger.info("start daemon thread to listen on channel %s",
                            ml[0])
                t = MonitorPubSub(ml[0], p)
                t.start()
                t.join()

                if not self._wait_for_installation(p):
                    logger.info(
                        "auto installation failed, contine to next job")
                    continue

                logger.info("waiting for the cockpit results")
                self._wait_for_cockpit(ml[0])

            else:
                logger.error(
                    "provisioning on host %s failed with return code %s",
                    ml[0], ret)

    def get_job_queue(self):
        """pass"""
        self.ksins.format_ks_files()
        return self.ksins.generate_job_queue()


if __name__ == '__main__':
    jr = JobRunner(
        'http://10.66.10.22:8090/rhevh/rhevh7-ng-36/rhev-hypervisor7-ng-3.6-20160516.0/rhev-hypervisor7-ng-3.6-20160516.0.x86_64.liveimg.squashfs')
    for i in jr.get_job_queue():
        print i

