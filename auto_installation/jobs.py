import time
import logging
import attr
from threading import Thread
import subprocess
from .kickstarts import KickStartFiles
from .beaker import Beaker, inst_watcher
from .constants import CURRENT_IP_PORT, ARGS_TPL, HOSTS, CB_PROFILE
from .const_install import KS_KERPARAMS_MAP
from .cobbler import Cobbler
from .check_install import CheckInstall
from .check_upgrade import CheckUpgrade
from .check_vdsm import CheckVdsm

log = logging.getLogger("bender")


@attr.s
class JobRunner(object):
    build_url = attr.ib()
    rd_conn = attr.ib()
    results_logs = attr.ib()
    target_build = attr.ib()
    # ks_filter = attr.ib(default='must')
    debug = attr.ib(default=False)

    def _wait_for_installation(self, p):
        while True:
            time.sleep(5)
            log.info("waitting for install done")
            msg = p.get_message(ignore_subscribe_messages=True)
            if msg:
                if 'done' in msg['data']:
                    log.info('autoinstallation job is success')
                    ip = msg['data'].split(',')[1]
                    return ip
                elif msg['data'] == 'fail':
                    log.info('autoinstallation job is fail')
                    return False

    def _wait_for_cockpit(self, bkr_name):
        pubsub_cockpit = self.rd_conn.pubsub()
        pubsub_cockpit.subscribe("{0}-cockpit-result".format(bkr_name))
        while True:
            time.sleep(5)
            msg = pubsub_cockpit.get_message(ignore_subscribe_messages=True)
            log.info(msg)
            if msg:
                if msg['data']:
                    log.info("cockpit test is done")
                    return msg['data']

    def _provision(self, ks, m):
        bp = Beaker(
            srv_ip=CURRENT_IP_PORT[0], srv_port=CURRENT_IP_PORT[1], ks_file=ks)
        bp.reserve(m)
        ret = bp.reboot(m)

        log.info("reboot {} with return code {}".format(m, ret))

        addition_kernel_params = ''
        if ks in KS_KERPARAMS_MAP:
            addition_kernel_params = KS_KERPARAMS_MAP.get(ks)

        with Cobbler() as cb:
            kargs = ARGS_TPL.format(
                srv_ip=CURRENT_IP_PORT[0],
                srv_port=CURRENT_IP_PORT[1],
                ks_file=ks,
                addition_params=addition_kernel_params)
            cb.add_new_system(
                name=m,
                profile=CB_PROFILE,
                modify_interface=HOSTS.get(m)['nic'],
                kernel_options=kargs)
        return ret

    def _set_repos(self):
        if self.target_build:
            version = self.target_build.split("-host-")[-1]
            tower_cmd = 'tower-cli job launch --job-template="rhvh_upgrade_select" ' \
                        '--extra-vars="version: {}"'.format(version)
            subprocess.Popen(tower_cmd, shell=True)

    @property
    def ksins(self):
        k = KickStartFiles()
        # k.ks_filter = self.ks_filter
        k.liveimg = self.build_url
        return k

    @property
    def job_queue(self):
        return self.ksins.get_job_queue()

    def go(self):
        self._set_repos()
        for m, ksl in self.job_queue.items():
            for ks in ksl:
                self.results_logs.get_actual_logger(ks)
                log.info("start provisioning on host %s with %s", m, ks)

                if self.debug:
                    log.debug("now is debug mode, will not do provisioning")
                    ret = 0
                else:
                    ret = self._provision(ks, m)

                log.info(self.results_logs.current_log_path)

                if ret == 0:
                    log.info("provisioning on host %s finished " +
                             "with kickstart file %s return code 0", m, ks)
                    p = self.rd_conn.pubsub(ignore_subscribe_messages=True)
                    log.info("subscribe channel %s", m)
                    p.subscribe(m)
                    log.info("start daemon thread to listen on channel %s", m)
                    t = inst_watcher(m, p)
                    t.setDaemon(True)
                    t.start()
                    t.join()

                    ret = self._wait_for_installation(p)
                    if not ret:
                        log.info(
                            "auto installation failed, contine to next job")
                        continue
                    else:
                        log.info(
                            "auto installation finished, contine to chekcpoints"
                        )

                        self.results_logs.logger_name = 'checkpoints'
                        self.results_logs.get_actual_logger(ks)

                        if ks.find("ati") == 0:
                            ck = CheckInstall()
                        elif ks.find("atu") == 0:
                            ck = CheckUpgrade()
                            ck.source_build = self.build_url.split('/')[-1].split('.x86_64.')[0]
                            ck.target_build = self.target_build
                        elif ks.find("atv") == 0:
                            ck = CheckVdsm()
                            ck.build = self.build_url.split('/')[-1].split('.x86_64.')[0]
                        else:
                            log.error("ks file name %s isn't started with ati/atu/atv.", ks)
                            continue

                        log.info("ip is %s", ret)
                        ck.host_string, ck.host_user, ck.host_pass = (
                            ret, 'root', 'redhat')
                        ck.beaker_name = m
                        ck.ksfile = ks

                        log.info(ck.go_check())

                        # TODO wati for cockpit new results format
                else:
                    log.error(
                        "provisioning on host %s failed with return code %s",
                        m, ret)

        self.rd_conn.set("running", "0")


def job_runner(img_url, rd_conn, results_logs, target_build=None):
    ins = JobRunner(img_url, rd_conn, results_logs, target_build)
    return Thread(target=ins.go)
