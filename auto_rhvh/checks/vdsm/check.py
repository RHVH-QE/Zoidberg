import logging
import re
from env_work import EnvWork
from vdsm_info import VdsmInfo
from checkpoints import CheckPoints
from ..helpers import CheckComm


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

            # make checkpoints instance
            self._checkpoints.vdsminfo = self._vdsminfo
            self._checkpoints.ksfile = self._ksfile
            self._checkpoints.remotecmd = self._remotecmd
            self._checkpoints.set_rhvm()

            # run check
            log.info("Start to run check points, please wait...")
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
        self._vdsminfo.build = self._source_build
        self._vdsminfo.beaker_name = self._beaker_name
        self._vdsminfo.ksfile = self._ksfile
        self._vdsminfo.remotecmd = self._remotecmd

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


if __name__ == '__main__':
    pass
