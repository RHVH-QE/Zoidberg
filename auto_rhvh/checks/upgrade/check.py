import logging
import requests
import os
import time
import re
import consts_upgrade as CONST
from ..helpers import CheckComm
from ..helpers.rhvm_api import RhevmAction
from check_points import CheckPoints
from upgrade_process import UpgradeProcess


log = logging.getLogger('bender')


class CheckUpgrade(CheckComm):
    """"""

    def __init__(self):
        self._host_string = None
        self._host_pass = None
        self._check_points = CheckPoints()
        self._upgrade_process = UpgradeProcess()

    @property
    def host_string(self):
        return self._host_string

    @host_string.setter
    def host_string(self, val):
        self._host_string = val

    @property
    def host_pass(self):
        return self._host_pass

    @host_pass.setter
    def host_pass(self, val):
        self._host_pass = val


    def call_func_by_name(self, name=''):
        func = getattr(self._check_points, name.lower(), None)
        if func:
            return func()
        else:
            raise NameError(
                'The checkpoint function {} is not defined'.format(name))

    def go_check(self):
        # make _check_points and _upgrade_process instance
        self._check_points.remotecmd = self._remotecmd
        self._check_points.source_build = self._source_build
        self._check_points.target_build = self._target_build
        self._check_points.beaker_name = self._beaker_name
        self._check_points.host_string = self._host_string
        self._check_points.host_pass = self._host_pass
        # self._check_points.ksfile = self._ksfile
        self._upgrade_process.remotecmd = self._remotecmd
        self._upgrade_process.source_build = self._source_build
        self._upgrade_process.target_build = self._target_build
        self._upgrade_process.beaker_name = self._beaker_name
        self._upgrade_process.host_string = self._host_string
        self._upgrade_process.host_pass = self._host_pass
        # self._upgrade_process.ksfile = self._ksfile

        self.remotecmd.disconnect()
        cks = {}

        try:
            if not self._check_points._collect_infos('old'):
                raise RuntimeError("Failed to collect old infos.")

            if "yum_update" in self.ksfile:
                ret = self._upgrade_process.yum_update_process()
            elif "yum_install" in self.ksfile:
                ret = self._upgrade_process.yum_install_process()
            elif "rhvm_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_upgrade_process()
            elif "lack_space" in self.ksfile:
                ret = self._upgrade_process.yum_update_lack_space_process()

            if not ret:
                raise RuntimeError("Failed to run upgrade.")

            if not self._check_points._collect_infos('new'):
                raise RuntimeError("Failed to collect new infos.")

            cks = self.run_cases()
        except Exception as e:
            log.error(e)
        finally:
            self._upgrade_process._del_host_on_rhvm()
            return cks


if __name__ == '__main__':
    pass
