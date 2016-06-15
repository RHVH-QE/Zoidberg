import os
import sys
import string
from nose import with_setup
from nose.tools import ok_, eq_
sys.path.insert(0, os.path.abspath("../auto_installation"))
from auto_installation.kickstarts import KickStartFiles
from auto_installation.constants import SMOKE_TEST_LIST, P1_TEST_LIST, \
                                        MUST_HAVE_TEST_LIST

ksf = None


def setup_func():
    global ksf
    ksf = KickStartFiles()


@with_setup(setup_func)
def test_get_all_ks():
    ksf.ks_filter = 'all'
    ret = ksf._get_all_ks_files()
    ok_(ret[-1] == 'ati_vlan_bond.ks')


@with_setup(setup_func)
def test_get_smoke_ks():
    ret = ksf._get_all_ks_files()
    ret_s = string.join(ret)
    for i in SMOKE_TEST_LIST:
        ok_(i in ret_s)


@with_setup(setup_func)
def test_get_p1_ks():
    ksf.ks_filter = 'p1'

    ret = ksf._get_all_ks_files()
    ret_s = string.join(ret)

    for i in P1_TEST_LIST:
        ok_(i in ret_s)


@with_setup(setup_func)
def test_convert_auto_ks():
    ksf.ks_filter = 'must'
    ksf.liveimg = "http://10.66.10.22:8090/rhevh/rhevh7-ng-36/rhev-hypervisor7-ng-4.0-20160527.0/rhev-hypervisor7-ng-4.0-20160527.0.x86_64.liveimg.squashfs"
    ksf._convert_to_auto_ks()


@with_setup(setup_func)
def test_get_host_by_type():
    eq_(ksf._get_host()[0], 'dell-per510-01.lab.eng.pek2.redhat.com')


@with_setup(setup_func)
def test_get_must_ks():
    ksf.ks_filter = 'must'
    ret = ksf._get_all_ks_files()
    eq_(len(ret), len(MUST_HAVE_TEST_LIST))
