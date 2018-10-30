import logging
import re
import os
import sys
import importlib
from ..helpers import CheckComm
from .expected_data import ExpectedData


log = logging.getLogger('bender')


EXPECTED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(__file__))), "static", "ksfiles")


class CheckInstall(CheckComm):
    """"""

    def __init__(self):
        self._expected_data = None

    def _get_expected_data(self):
        expected_data_file = os.path.join(
            EXPECTED_DATA_DIR, self.ksfile.replace('.ks', '.json'))
        self._expected_data = ExpectedData(expected_data_file)
        if self.ksfile == 'ati_fc_01.ks':
            cmd = 'vgs --noheadings -o vg_name'
            ret = self.remotecmd.run_cmd(cmd)
            self._expected_data.set_expected_vgname(ret[1])

    def _remote_reconnect(self):
        cmd = 'lvs -a'
        self.remotecmd.run_cmd(cmd)

    def call_func_by_name(self, name=''):
        class_name, method_name = name.split('.')
        temp = class_name.lower()[:-5]
        module_name = temp + '_check'
        expected_data_name = "expected_" + temp

        module = importlib.import_module("." + module_name, __package__)
        clss = getattr(module, class_name, None)
        expected_data = getattr(self._expected_data, expected_data_name)
        obj = clss(self.remotecmd, expected_data)
        method = getattr(obj, method_name, None)

        return method()

    def go_check(self):
        self.remotecmd.disconnect()
        self._remote_reconnect()
        self._get_expected_data()
        return self.run_cases()


if __name__ == '__main__':
    pass
