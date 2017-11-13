import time
import logging
import attr
from threading import Thread
import subprocess
import os
from .kickstarts import KickStartFiles
from .beaker import Beaker, inst_watcher
from .cobbler import Cobbler
from .constants import CURRENT_IP_PORT, ARGS_TPL, CB_PROFILE, COVERAGE_TEST
from casesinfo.common import HOSTS
from checks import CheckInstall, CheckUpgrade, CheckVdsm, RemoteCmd
from .util_result_index import cache_logs_summary
from reports import ResultsToPolarion
from coverage import upload_coverage_raw_res_from_host, generate_final_coverage_result

log = logging.getLogger("bender")


@attr.s
class JobRunner(object):
    build_url = attr.ib()
    rd_conn = attr.ib()
    results_logs = attr.ib()
    casesmap = attr.ib()
    target_build = attr.ib()
    # ks_filter = attr.ib(default='must')
    debug = attr.ib(default=False)
    test_flag = attr.ib(default='install')

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

    def _provision(self, ks, ker_param, m):
        bp = Beaker(
            srv_ip=CURRENT_IP_PORT[0], srv_port=CURRENT_IP_PORT[1], ks_file=ks)
        bp.reserve(m)
        ret = bp.reboot(m)

        log.info("reboot {} with return code {}".format(m, ret))

        with Cobbler() as cb:
            kargs = ARGS_TPL.format(
                srv_ip=CURRENT_IP_PORT[0],
                srv_port=CURRENT_IP_PORT[1],
                ks_file=ks,
                addition_params=ker_param)
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
        k.casesmap = self.casesmap
        return k

    @property
    def job_queue(self):
        return self.ksins.get_job_queue()

    def go(self):
        self._set_repos()
        for m, ksl in self.job_queue.items():
            for kt in ksl:
                ks = kt[0]
                ker_param = ''
                if len(kt) > 1:
                    ker_param = kt[1]

                self.results_logs.get_actual_logger(ks)
                log.info("start provisioning on host %s with %s", m, ks)

                if self.debug:
                    log.debug("now is debug mode, will not do provisioning")
                    ret = 0
                else:
                    ret = self._provision(ks, ker_param, m)

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

                        log.info("ip is %s", ret)
                        ck = self.create_check(ret, ks)
                        if not ck:
                            continue

                        log.info(ck.go_check())

                        if ks.find("ati") == 0 and COVERAGE_TEST:
                            upload_coverage_raw_res_from_host(ck)

                            # TODO wati for cockpit new results format
                else:
                    log.error(
                        "provisioning on host %s failed with return code %s",
                        m, ret)

        self.generate_final_results()

        if ks.find("ati") == 0 and COVERAGE_TEST:
            generate_final_coverage_result(ck, self.build_url.split('/')[-2])

        cache_logs_summary()
        self.rd_conn.set("running", "0")

    def create_check(self, host_ip, ks):
        if ks.find("ati") == 0:
            self.test_flag = "install"
            ck = CheckInstall()
        elif ks.find("atu") == 0:
            self.test_flag = "upgrade"
            ck = CheckUpgrade()
        elif ks.find("atv") == 0:
            self.test_flag = "vdsm"
            ck = CheckVdsm()
        else:
            log.error(
                "ks file name %s isn't started with ati/atu/atv.",
                ks)
            return None

        ck.source_build = self.build_url.split('/')[-2]
        ck.target_build = self.target_build
        ck.beaker_name = m
        ck.ksfile = ks
        ck.remotecmd = RemoteCmd(host_ip, 'root', 'redhat')
        ck.casesmap = self.casesmap

        return ck

    def generate_final_results(self):
        try:
            log_path = self.results_logs.current_log_path
            build_name = self.results_logs.parse_img_url()
            if build_name not in log_path:
                return
            final_path = os.path.join(
                log_path.split(build_name)[0], build_name)
            report = ResultsToPolarion(
                final_path, '-l', self.casesmap, self.test_flag, self.target_build)
            report.run()
        except Exception as e:
            log.error(e)


def job_runner(img_url, rd_conn, results_logs, casesmap, target_build=None):
    ins = JobRunner(img_url, rd_conn, results_logs, casesmap, target_build)
    return Thread(target=ins.go)
