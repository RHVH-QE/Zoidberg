#!/usr/bin/python
# This module is aim to debug check fuctions
# Usage:
# python -m checks

from . import CheckInstall, CheckUpgrade, CheckVdsm
from . import CasesMap, RemoteCmd
from cases_info import common as COMM


# Neet to modify these values manually befor debuging.
SRC_BUILD = 'redhat-virtualization-host-4.1-20171207.0'
TAR_BUILD = 'redhat-virtualization-host-4.2-20171218.1'
BEAKER = COMM.DELL_PET105_01
KSFILE = 'atu_yum_update.ks'
HOST_IP = '10.66.148.9'
TEST_LEVEL = COMM.UPGRADE_TIER1


def to_see_detailed_logs():
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils import ResultsAndLogs
    logs = ResultsAndLogs()
    logs.logger_name = "debug.log"
    logs.img_url = "check/test"
    logs.get_actual_logger("check")


def check(module_name):
    if module_name == "install":
        ck = CheckInstall()
    if module_name == "upgrade":
        ck = CheckUpgrade()
    if module_name == "vdsm":
        ck = CheckVdsm()

    ck.source_build = SRC_BUILD
    ck.target_build = TAR_BUILD
    ck.beaker_name = BEAKER
    ck.ksfile = KSFILE
    ck.remotecmd = RemoteCmd(HOST_IP, 'root', 'redhat')
    ck.casesmap = CasesMap(TEST_LEVEL)
    ck.host_string = HOST_IP
    ck.host_pass = 'redhat'

    print ck.go_check()


if __name__ == '__main__':
    to_see_detailed_logs()
    check("upgrade")
