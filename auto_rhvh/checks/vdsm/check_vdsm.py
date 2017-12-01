import logging
import re
from ..helplers import CheckComm
from env_work import EnvWork
from vdsm_info import VdsmInfo
from checkpoint import CheckPoints


log = logging.getLogger('bender')


class CheckVdsm(CheckComm):
    """"""

    def __init__(self):
        self._vdsminfo = VdsmInfo()
        self._checkpoints = CheckPoints()

    #################################################
    # Before checking, create the datacenter, cluster
    #################################################
    def _setup_before_check(self, env_work):
        return env_work.setup()

    #################################################
    # After checking, remove the cluster, datacenter
    #################################################
    def _teardown_after_check(self, env_work):
        return env_work.teardown()

    def run_cases(self):
        cks = {}
        try:
            # get checkpoint cases map
            disorder_checkpoint_cases_map = self.casesmap.get_checkpoint_cases_map(
                self.ksfile, self.beaker_name)
            checkpoint_cases_map_list = sorted(
                disorder_checkpoint_cases_map.items(), key=lambda item: item[0])

            # run check
            log.info("Start to run check points, please wait...")

            self._checkpoints.vdsminfo = self._vdsminfo
            self._checkpoints.set_rhvm()

            for l in checkpoint_cases_map_list:
                checkpoint = l[0]
                cases = l[1]
                self.run_checkpoint(checkpoint, cases, cks)
        except Exception as e:
            log.exception(e)

        return cks

    def run_checkpoint(self, checkpoint, cases, cks):
        try:
            log.info("Start to run checkpoint:%s for cases:%s",
                     checkpoint, cases)
            ck = self.call_func_by_name(checkpoint)
            if ck:
                newck = 'passed'
            else:
                newck = 'failed'
            for case in cases:
                if not re.search("RHEVM-[0-9]+", case):
                    continue
                cks[case] = newck
        except Exception as e:
            log.error(e)
        finally:
            log.info("Run checkpoint:%s for cases:%s finished.",
                     checkpoint, cases)

    def call_func_by_name(self, name=''):
        func = getattr(self._checkpoints, name.lower(), None)
        if func:
            return func()
        else:
            raise NameError(
                'The checkpoint function {} is not defined'.format(name))

    def _get_vdsm_info(self):
        self._vdsminfo.build = self.source_build
        self._vdsminfo.beaker_name = self.beaker_name
        self._vdsminfo.ksfile = self.ksfile
        self._vdsminfo.remotecmd = self.remotecmd

        self._vdsminfo.get()

    def go_check(self):
        self.remotecmd.disconnect()

        # Get all related information
        self._get_vdsm_info()

        # Env setup
        ew = EnvWork(self._vdsminfo)
        is_setup_success = self._setup_before_check(ew)

        # Run cases
        cks = self.run_cases() if is_setup_success else {}

        # Env teardown
        self._teardown_after_check(ew)

        return cks

def log_cfg_for_unit_test():
    from utils import ResultsAndLogs
    logs = ResultsAndLogs()
    logs.logger_name = "unit_test.log"
    logs.img_url = "vdsm/test"
    logs.get_actual_logger("vdsm")


if __name__ == '__main__':
    log_cfg_for_unit_test()
    log = logging.getLogger('bender')

    ck = CheckVdsm()
    ck.host_string, ck.host_user, ck.host_pass = ('10.73.73.17', 'root',
                                                  'redhat')
    ck.build = 'redhat-virtualization-host-4.1-20170531.0'
    ck.beaker_name = 'dell-per515-01.lab.eng.pek2.redhat.com'
    ck.ksfile = 'atv_bondi_02.ks'

    print ck.go_check()
