"""This module will represent kickstart files
"""
# pylint: disable=C0103, W0403

import os
import logging
import fnmatch

#from pykickstart.version import makeVersion
#from pykickstart.parser import KickstartParser, Script
from pykickstart.parser import Script
from pykickstart.constants import KS_SCRIPT_PRE, KS_SCRIPT_POST
# from pykickstart.commands.network import F22_NetworkData

# import constants
from constants import KS_FILES_DIR, KS_FILES_AUTO_DIR, \
    SMOKE_TEST_LIST, P1_TEST_LIST, ALL_TEST, HOSTS, \
    POST_SCRIPT_01, HOST_POOL, PRE_SCRIPT_01, MUST_HAVE_TEST_LIST, DEBUG_LIST, \
    TEST_LEVEL
from utils import get_testcase_map

loger = logging.getLogger('bender')


class KickStartFiles(object):
    """"""
    KS_FILTER = dict(
        smoke=SMOKE_TEST_LIST,
        p1=P1_TEST_LIST,
        all=ALL_TEST,
        must=MUST_HAVE_TEST_LIST,
        debug=DEBUG_LIST)

    def __init__(self):
        self._ks_filter = 'must'
        self._liveimg = None

    @property
    def ks_filter(self):
        return self._ks_filter

    @ks_filter.setter
    def ks_filter(self, val):
        if val not in self.KS_FILTER:
            raise RuntimeError(
                "value of `ks_filter=` must be one of [smoke, p1, all, must]")
        self._ks_filter = val

    @property
    def liveimg(self):
        return self._liveimg

    @liveimg.setter
    def liveimg(self, val):
        self._liveimg = val

    def _get_host(self, ks_name='', host_type='default'):
        # TODO
        return HOST_POOL.get(host_type)

    def _get_machine_ksl_map(self):
        machine_ksl_map = {}
        testcase_map = get_testcase_map()
        for value in testcase_map.itervalues():
            ks = value[0]
            machine = value[1]
            if machine in machine_ksl_map:
                if ks not in machine_ksl_map.get(machine):
                    machine_ksl_map[machine].append(ks)
            else:
                machine_ksl_map[machine] = []
                machine_ksl_map[machine].append(ks)

        return machine_ksl_map

    def _get_ks_machine_map(self):
        ks_mashine_map = {}
        testcase_map = get_testcase_map()
        for value in testcase_map.itervalues():
            ks = value[0]
            machine = value[1]
            if ks in ks_mashine_map:
                if machine != ks_mashine_map.get(ks):
                    raise ValueError(
                        'One kickstart file cannot be run on two machines.')
            else:
                ks_mashine_map[ks] = machine

        return ks_mashine_map

    def _get_all_ks_files(self):
        ret = []
        for pat in self.KS_FILTER.get(self._ks_filter, ('*')):
            loger.debug("list ks files match pattern %s", pat)
            ret.extend(
                fnmatch.filter(os.listdir(KS_FILES_DIR), "ati_{}*".format(pat)))
        ret.sort()
        return ret

    def _generate_ks_script(self,
                            content,
                            error_on_fail=True,
                            interp=None,
                            logfile=None,
                            script_type=KS_SCRIPT_POST,
                            in_chroot=False,
                            lineno=None):
        sp = Script(content)

        sp.errorOnFail = error_on_fail

        if interp:
            sp.interp = interp

        if logfile:
            sp.logfile = logfile

        sp.type = script_type
        sp.inChroot = in_chroot

        if lineno:
            sp.lineno = lineno
        return sp

    def _convert_to_auto_ks(self):
        loger.info("remove all old files under {}".format(KS_FILES_AUTO_DIR))
        os.system("rm -f {}/*".format(KS_FILES_AUTO_DIR))

        ks_machine_map = self._get_ks_machine_map()

        for ks in ks_machine_map:

            bkr_name = ks_machine_map.get(ks)

            nic_name = HOSTS.get(bkr_name).get("nic").keys()[0].split('-')[-1]

            ks_ = os.path.join(KS_FILES_DIR, ks)
            ks_out = os.path.join(KS_FILES_AUTO_DIR, ks)

            new_live_img = "liveimg --url=" + self._liveimg

            os.system("sed '/liveimg --url=/ c\{}' {} > {}".format(new_live_img,
                                                                   ks_, ks_out))

            post_script = self._generate_ks_script(
                POST_SCRIPT_01.format(nic_name) + bkr_name, error_on_fail=False)

            pre_script = self._generate_ks_script(
                PRE_SCRIPT_01, script_type=KS_SCRIPT_PRE, error_on_fail=False)

            with open(ks_out, "a") as fp:
                fp.write(pre_script.__str__())
                fp.write(post_script.__str__())

    def get_job_queue(self):
        print "current test level is %x" % TEST_LEVEL
        self._convert_to_auto_ks()
        return self._get_machine_ksl_map()
        # return [(ks, self._get_host(ks)) for ks in ks_list]


if __name__ == '__main__':
    ks = KickStartFiles()
    ks.liveimg = "http://fakeimg.squashfs"
    print(ks.get_job_queue())
