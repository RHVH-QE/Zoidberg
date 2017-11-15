import logging
import re
import os
import sys
root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)
from checks.helpers import CheckComm
#from ..check_comm import CheckComm
from expected_data import ExpectedData
import importlib

log = logging.getLogger('bender')


AUTO_TEST_DIR = '/boot/autotest'
LOCAL_DIR = os.path.join(os.path.dirname(__file__), "expected_data")


class CheckInstall(CheckComm):
    """"""

    def __init__(self):
        self._expected_data = None

    def _get_expected_data(self):
        expected_data_name = self.ksfile.replace('.ks', '.json')
        remote_file = os.path.join(AUTO_TEST_DIR, expected_data_name)
        local_file = os.path.join(LOCAL_DIR, expected_data_name)
        log.info("Start to get %s", remote_file)

        try:

            if not os.path.exists(LOCAL_DIR):
                os.makedirs(LOCAL_DIR)
            else:
                if os.path.exists(local_file):
                    os.system('rm -f {}'.format(local_file))

            self.remotecmd.get_remote_file(remote_file,
                                           local_file)

            self._expected_data = ExpectedData(local_file)

            log.info("Got %s", expected_data_name)

        except Exception as e:
            log.error(e)
            return False

        return True

    def call_func_by_name(self, name=''):
        class_name, method_name = name.split('.')
        temp = class_name.lower()[:-5]
        module_name = temp + '_check'
        expected_data_name = "expected_" + temp

        module = importlib.import_module("checks.install." + module_name)
        clss = getattr(module, class_name, None)
        expected_data = getattr(self._expected_data, expected_data_name)
        obj = clss(self.remotecmd, expected_data)
        method = getattr(obj, method_name, None)

        return method()

    def go_check(self):
        self.remotecmd.disconnect()
        if self._get_expected_data():
            cks = self.run_cases()
        else:
            cks = {}
        return cks


if __name__ == '__main__':
    def log_cfg_for_unit_test():
        from utils import ResultsAndLogs
        logs = ResultsAndLogs()
        logs.logger_name = "unit_test.log"
        logs.img_url = "install/test"
        logs.get_actual_logger("install")

    log_cfg_for_unit_test()
    log = logging.getLogger('bender')

    ck = CheckInstall()

    ck.source_build = None
    ck.target_build = None
    ck.beaker_name = 'dell-per510-01.lab.eng.pek2.redhat.com'
    ck.ksfile = 'ati_fc_01.ks'

    from checks.helpers import RemoteCmd
    ck.remotecmd = RemoteCmd('10.73.75.35', 'root', 'redhat')

    from cases_info import CasesMap, DEBUG_TIER
    test_level = DEBUG_TIER
    ck.casesmap = CasesMap(test_level)

    print ck.go_check()
