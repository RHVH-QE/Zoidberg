"""Module Doc Here
"""
import time
import logging
import json
import os
from threading import Thread
from kickstarts import KickStartFiles
from constants import CURRENT_IP_PORT, CB_API, ARGS_TPL
from beaker import BeakerProvision, MonitorPubSub
from checkpoints import CheckCheck
from cobbler import Cobbler

logger = logging.getLogger('bender')


class JobRunner(Thread):
    """class doc here
    """

    def __init__(self, build_url, rd_conn, results_logs, ks_filter='must'):
        super(JobRunner, self).__init__()
        self.daemon = True
        self.build_url = build_url
        self.rd_conn = rd_conn
        self.results_logs = results_logs
        self.ks_filter = ks_filter
        self.ksins = KickStartFiles()
        self.ksins.ks_filter = self.ks_filter
        self.ksins.liveimg = build_url
        self.job_queue = self.ksins.get_job_queue()
        self._debug = False

    def _wait_for_installation(self, p):
        while True:
            time.sleep(5)
            logger.info("waiting for installation done")
            msg = p.get_message(ignore_subscribe_messages=True)

            if msg:
                if 'done' in msg['data']:
                    logger.info('autoinstallation job is success')
                    ip = msg['data'].split(',')[1]
                    return ip

                elif msg['data'] == 'fail':
                    logger.info('autoinstallation job is fail')
                    return False

    def _wait_for_cockpit(self, bkr_name):
        pubsub_cockpit = self.rd_conn.pubsub()
        pubsub_cockpit.subscribe("{0}-cockpit-result".format(bkr_name))
        while True:
            time.sleep(5)
            msg = pubsub_cockpit.get_message(ignore_subscribe_messages=True)
            logger.info(msg)
            if msg:
                if msg['data']:
                    logger.info("cockpit test is done")
                    return msg['data']

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
                with Cobbler(CB_API) as cb:
                    cb.args['kernel_options'] = ARGS_TPL.format(srv_ip=CURRENT_IP_PORT[0],
                                                                srv_port=CURRENT_IP_PORT[1],
                                                                ks_file=ks)
                    cb.change_system(ml[0], cb.args)

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

                ret = self._wait_for_installation(p)
                if not ret:
                    logger.info(
                        "auto installation failed, contine to next job")
                    continue
                else:
                    logger.info(
                        "auto installation finished, contine to chekcpoints")

                    self.results_logs.logger_name = 'checkpoints'
                    self.results_logs.get_actual_logger(self.build_url, ks)
                    ck = CheckCheck()

                    logger.info("ip is %s", ret)
                    ck.host_string, ck._host_user, ck.host_pass = (ret, 'root',
                                                                   'redhat')
                    logger.info(ck.go_check(ks.replace('ati_', '').replace(
                        '.ks', '')))
                logger.info("waiting for the cockpit results")
                cockpit_result_raw = self._wait_for_cockpit(ml[0])
                # cockpit_res = json.loads(cockpit_result_raw)
                # cockpit_res_path = self.results_logs.current_log_path
                # with(open(os.path.join(cockpit_res_path, "cockpit.json")), 'w+') as fp:
                #     fp.write(cockpit_res)

            else:
                logger.error(
                    "provisioning on host %s failed with return code %s",
                    ml[0], ret)


if __name__ == '__main__':
    jr = JobRunner(
        'http://10.66.10.22:8090/rhevh/rhevh7-ng-36/rhev-hypervisor7-ng-3.6-20160516.0/rhev-hypervisor7-ng-3.6-20160516.0.x86_64.liveimg.squashfs')
    for i in jr.get_job_queue():
        print i
