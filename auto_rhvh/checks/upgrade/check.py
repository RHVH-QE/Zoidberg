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

    def run_cases(self):
        cks = {}
        try:
            # get checkpoint cases map
            checkpoint_cases_map = self.casesmap.get_checkpoint_cases_map(self.ksfile,
                                                                          self.beaker_name)

            # run check
            log.info("Start to run check points, please wait...")

            delete_imgbase_cases = None
            for checkpoint, cases in checkpoint_cases_map.items():
                if checkpoint == "delete_imgbase_check":
                    delete_imgbase_cases = cases
                    continue
                self.run_checkpoint(checkpoint, cases, cks)
            if delete_imgbase_cases:
                self.run_checkpoint("delete_imgbase_check", delete_imgbase_cases, cks)
        except Exception as e:
            log.error(e)

        return cks

    def go_check(self):
        # make _check_points and _upgrade_process instance
        self._check_points.remotecmd = self._remotecmd
        self._check_points.source_build = self._source_build
        self._check_points.target_build = self._target_build
        self._check_points.beaker_name = self._beaker_name
        self._check_points.host_string = self._host_string
        self._check_points.host_pass = self._host_pass
        self._upgrade_process.remotecmd = self._remotecmd
        self._upgrade_process.source_build = self._source_build
        self._upgrade_process.target_build = self._target_build
        self._upgrade_process.beaker_name = self._beaker_name
        self._upgrade_process.host_string = self._host_string
        self._upgrade_process.host_pass = self._host_pass

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
            elif "yum_ls_update" in self.ksfile:
                ret = self._upgrade_process.yum_local_storage_update_process()
            elif "yum_normal_ls_update" in self.ksfile:
                ret = self._upgrade_process.yum_local_storage_update_process_normal()
            elif "rhvm_vms_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_upgrade_create_vms_process()
            elif "rhvm_config_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_upgrade_config_and_reboot_process()
            elif "rhvm_failed_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_failed_upgrade_process()
            elif "rhvm_bond_vlan_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_bond_vlan_upgrade_process()
            elif "lack_space" in self.ksfile:
                ret = self._upgrade_process.yum_update_lack_space_process()
            elif "rhvm_iscsi" in self.ksfile:
                ret = self._upgrade_process.rhvm_update_iscsi_process()
            elif "rhvm_bond_iscsi" in self.ksfile:
                ret = self._upgrade_process.rhvm_update_bond_process()
            elif "yum_vlan" in self.ksfile:
                ret = self._upgrade_process.yum_update_vlan_process()
            elif "upgrade_and_rollback_01" in self.ksfile:
                ret = self._upgrade_process.yum_upgrade_and_rollback_process(yum_cmd=True)
            elif "upgrade_and_rollback_02" in self.ksfile:
                ret = self._upgrade_process.yum_upgrade_and_rollback_process()
            elif "rhvm_normal_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_normal_upgrade_process()
            elif "rhvm_rhsm_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_rhsm_upgrade_process()
            elif "rhvm_fips_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_fips_upgrade_process()
            elif "rhvm_security_upgrade" in self.ksfile:
                ret = self._upgrade_process.rhvm_security_upgrade_process()
            elif "duplicate_service_update" in self.ksfile:
                ret = self._upgrade_process.duplicate_service_yum_update_process()

            if "lack_space" not in self.ksfile and "rhvm_failed_upgrade" not in self.ksfile and "yum_ls_update" not in self.ksfile:
                self._upgrade_process.upload_upgrade_log(self.log_path)
            
            if not ret:
                raise RuntimeError("Failed to run upgrade.")
            
            if "yum_ls_update" not in self.ksfile:
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
