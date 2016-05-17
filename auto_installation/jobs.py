"""Module Doc Here
"""
import logging
from threading import Thread
from kickstarts import KickStartFiles
from constants import CURRENT_IP_PORT
from beaker import BeakerProvision, MonitorPubSub


LOG = logging.getLogger('bender')


class JobRunner(Thread):
    """class doc here
    """
    def __init__(self, build_url, rd_conn):
        super(JobRunner, self).__init__()
        self.daemon = True
        self.build_url = build_url
        self.rd_conn = rd_conn
        self.ksins = KickStartFiles(dict(liveimg=build_url,
                                         srv_ip=CURRENT_IP_PORT[0],
                                         srv_port=CURRENT_IP_PORT[1]))
        self.job_queue = self.get_job_queue()

    def run(self):
        """pass"""
        for ks, ml in self.job_queue:
            LOG.info("start provisioning on host %s with %s", ml[0], ks)
            ret = BeakerProvision(srv_ip=CURRENT_IP_PORT[0],
                                  srv_port=CURRENT_IP_PORT[1],
                                  ks_file=ks).provision(ml[0])

            if ret == 0:
                LOG.info("provisioning on host %s finished with return code 0", ml[0])
                p = self.rd_conn.pubsub(ignore_subscribe_messages=True)
                LOG.info("subscribe channel %s", ml[0])
                p.subscribe(ml[0])
                LOG.info("start daemon thread to listen on channel %s", ml[0])
                t = MonitorPubSub(ml[0], p)
                t.start()
                t.join()
            else:
                LOG.error("provisioning on host %s failed with return code %s", ml[0], ret)

    def get_job_queue(self):
        """pass"""
        self.ksins.format_ks_files()
        return self.ksins.generate_job_queue()


if __name__ == '__main__':
    jr = JobRunner('http://10.66.10.22:8090/rhevh/rhevh7-ng-36/rhev-hypervisor7-ng-3.6-20160516.0/rhev-hypervisor7-ng-3.6-20160516.0.x86_64.liveimg.squashfs')
    for i in jr.get_job_queue():
        print i

