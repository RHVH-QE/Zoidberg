"""This module will represent kickstart files
"""
# pylint: disable=C0103, W0403

import os
import json
import doctest
import logging
import fnmatch

from pykickstart.version import makeVersion
from pykickstart.parser import KickstartParser

from constants import KS_FILES_DIR, KS_FILES_AUTO_DIR, \
    SMOKE_TEST_LIST, P1_TEST_LIST, ALL_TEST

loger = logging.getLogger('bender')


class KickStartFilesOld(object):
    """This class will combine *.json and *.tmp into *.ks
    >>> KickStartFiles(dict(liveimg='http://10.66.x.x/rhevh.img',\
                            srv_ip='10.66.9.216',\
                            srv_port='5000')).generate_job_queue()
    """

    def __init__(self, kargs):
        assert isinstance(kargs, dict)
        self.kargs = kargs

    @staticmethod
    def _get_ks_files_by_priority(priority='P1', only_ks=False):
        """pass
        """
        pat = "%s*.tpl" % priority

        for fn in os.listdir(KS_FILES_DIR):
            if fnmatch.fnmatch(fn, pat):
                fn_json = fn.replace('.tpl', '.json')
                assert os.path.exists(os.path.join(KS_FILES_DIR,
                                                   fn_json)) is True
                if not only_ks:
                    yield fn, fn_json
                else:
                    yield fn.replace('.tpl', '.ks'), fn_json

    def format_ks_files(self):
        """fill tpl with actual content"""

        for k, j in self._get_ks_files_by_priority():
            old = json.loads(open(os.path.join(KS_FILES_DIR, j)).read())
            old.update(self.kargs)

            with open(os.path.join(KS_FILES_DIR, k), 'r') as f1:
                with open(
                        os.path.join(KS_FILES_DIR, k.replace('.tpl', '.ks')),
                        'w') as f2:
                    f2.write(f1.read().format(**old))

    def generate_job_queue(self):
        """make job queue from ks files"""
        ks = self._get_ks_files_by_priority(only_ks=True)
        for k, j in ks:
            machines_list = json.loads(open(os.path.join(
                KS_FILES_DIR, j)).read())['MACHINES']
            yield k, machines_list


class KickStartFiles(object):
    """"""
    KS_FILTER = dict(smoke=SMOKE_TEST_LIST, p1=P1_TEST_LIST, all=ALL_TEST)

    def __init__(self):
        self._ks_filter = 'smoke'
        self._liveimg = None

    @property
    def ks_filter(self):
        return self._ks_filter

    @ks_filter.setter
    def ks_filter(self, val):
        if val not in self.KS_FILTER:
            raise RuntimeError(
                "value of `ks_filter=` must be one of [smoke, p1, all]")
        self._ks_filter = val

    @property
    def liveimg(self):
        return self._liveimg

    @liveimg.setter
    def liveimg(self, val):
        self._liveimg = val

    def _get_all_ks_files(self):
        ret = []
        for pat in self.KS_FILTER.get(self._ks_filter, ('*')):
            loger.debug("list ks files match pattern %s", pat)
            ret.extend(fnmatch.filter(
                os.listdir(KS_FILES_DIR), "ati_{}*".format(pat)))
        ret.sort()
        return ret

    def _convert_to_auto_ks(self):
        for ks in self._get_all_ks_files():
            kp = KickstartParser(makeVersion())
            ks_ = os.path.join(KS_FILES_DIR, ks)

            ks_out = os.path.join(KS_FILES_AUTO_DIR, ks)

            kp.readKickstart(ks_)
            kp.handler.liveimg.url = self._liveimg

            with open(ks_out, 'w') as fp:
                fp.write(self._ksparser.handler.__str__())


if __name__ == '__main__':

    ks = KickStartFiles()
    ks.liveimg = 'http://10.66.10.22:8090/rhevh/rhevh7-ng-36/rhev-hypervisor7-ng-4.0-20160527.0/rhev-hypervisor7-ng-4.0-20160527.0.x86_64.liveimg.squashfs'
    ks._convert_to_auto_ks()
