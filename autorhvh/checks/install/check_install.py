import logging
import re
import os
import sys
from ..check_comm import CheckComm
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

            self.get_remote_file(remote_file,
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

        module = importlib.import_module(module_name)
        clss = getattr(module, class_name, None)
        method = getattr(clss, method_name, None)
        expected_data = getattr(self._expected_data, expected_data_name)

        return clss(self.remotecmd, expected_data).method()

    def go_check(self):
        self.remotecmd.disconnect()
        if self._get_expected_data():
            cks = self.run_cases()
        else:
            cks = {}
        return cks


if __name__ == '__main__':
    ck = CheckInstall()

    ck.source_build = 'redhat-virtualization-host-4.1-20170421.0'
    ck.target_build = NONE
    ck.beaker_name = 'dell-pet105-01.qe.lab.eng.nay.redhat.com'
    ck.ksfile = 'ati_local_02.ks'

    from checks.remotecmd import RemoteCmd
    ck.remotecmd = RemoteCmd('10.66.148.9', 'root', 'redhat')

    from casesinfo.casesmap import CasesMap
    import casesinfo.common as COMM
    test_level = COMM.DEBUG_TIER
    ck.casesmap = CasesMap(test_level)

    print ck.go_check()
