"""This module will represent kickstart files
"""
# pylint: disable=C0103, W0403

import os
import json
import doctest
import logging
import fnmatch

from constants import KS_FILES_DIR

LOGER = logging.getLogger('bender')


class KickStartFiles(object):
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
                assert os.path.exists(os.path.join(KS_FILES_DIR, fn_json)) is True
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
                with open(os.path.join(KS_FILES_DIR, k.replace('.tpl', '.ks')), 'w') as f2:
                    f2.write(f1.read().format(**old))

    def generate_job_queue(self):
        """make job queue from ks files"""
        ks = self._get_ks_files_by_priority(only_ks=True)
        for k, j in ks:
            machines_list = json.loads(open(os.path.join(KS_FILES_DIR, j)).read())['MACHINES']
            yield k, machines_list


if __name__ == '__main__':

    doctest.testmod(verbose=True)
