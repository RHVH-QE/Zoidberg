"""This module will represent kickstart files
"""
# pylint: disable=C0103, W0403

import os
import json
import logging
import fnmatch

from pykickstart.version import makeVersion
from pykickstart.parser import KickstartParser, Script
from pykickstart.constants import KS_SCRIPT_PRE, KS_SCRIPT_POST

from constants import KS_FILES_DIR, KS_FILES_AUTO_DIR, \
    SMOKE_TEST_LIST, P1_TEST_LIST, ALL_TEST, \
    POST_SCRIPT_01, HOST_POOL, PRE_SCRIPT_01, MUST_HAVE_TEST_LIST

loger = logging.getLogger('bender')


class KickStartFiles(object):
    """"""
    KS_FILTER = dict(smoke=SMOKE_TEST_LIST,
                     p1=P1_TEST_LIST,
                     all=ALL_TEST,
                     must=MUST_HAVE_TEST_LIST)

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

    def _get_all_ks_files(self):
        ret = []
        for pat in self.KS_FILTER.get(self._ks_filter, ('*')):
            loger.debug("list ks files match pattern %s", pat)
            ret.extend(fnmatch.filter(
                os.listdir(KS_FILES_DIR), "ati_{}*".format(pat)))
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

        ks_list = self._get_all_ks_files()

        for ks in ks_list:
            kp = KickstartParser(makeVersion())

            bkr_name = self._get_host(ks_name=ks)

            ks_ = os.path.join(KS_FILES_DIR, ks)
            ks_out = os.path.join(KS_FILES_AUTO_DIR, ks)

            kp.readKickstart(ks_)

            kp.handler.liveimg.url = self._liveimg

            if 'sshd' not in kp.handler.services.enabled:
                kp.handler.services.enabled.append('sshd')

            kp.handler.scripts.append(self._generate_ks_script(
                PRE_SCRIPT_01,
                script_type=KS_SCRIPT_PRE,
                error_on_fail=False, ))
            kp.handler.scripts.append(self._generate_ks_script(
                POST_SCRIPT_01 % bkr_name,
                error_on_fail=False, ))

            with open(ks_out, 'w') as fp:
                fp.write(kp.handler.__str__())
            kp = None

        return ks_list

    def get_job_queue(self):
        print("current kickstart filter is %s", self.ks_filter)
        ks_list = self._convert_to_auto_ks()

        return [(ks, self._get_host(ks)) for ks in ks_list]


if __name__ == '__main__':
    pass
