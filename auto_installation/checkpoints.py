import logging
from fabric.api import settings, run
from fabric.exceptions import NetworkError, CommandTimeout

from constants import KS_FILES_AUTO_DIR
import re

log = logging.getLogger('bender')


class CheckYoo(object):
    """"""

    def __init__(self):
        self._host_string = None
        self._host_user = None
        self._host_pass = None

    @property
    def host_string(self):
        return self._host_string

    @host_string.setter
    def host_string(self, val):
        # TODO check val
        self._host_string = val

    @property
    def host_user(self):
        return self._host_user

    @host_user.setter
    def host_user(self, val):
        self._host_user = val

    @property
    def host_pass(self):
        return self._host_pass

    @host_pass.setter
    def host_pass(self, val):
        self._host_pass = val

    def run_cmd(self, cmd, timeout=60):
        ret = None
        try:
            with settings(host_string=self.host_string,
                          user=self.host_user,
                          password=self.host_pass,
                          disable_known_hosts=True,
                          connection_attempts=60):
                ret = run(cmd, quiet=True, timeout=timeout)
                if ret.succeeded:
                    return True, ret
                else:
                    return False, ret
        except NetworkError as e:
            return False, e

        return True, ret

    def check_strs_in_file(self, fp, strs, timeout):
        log.info("start to check if %s in %s", strs, fp)
        try:
            ret = self.run_cmd('cat {}'.format(fp), timeout=timeout)
        except CommandTimeout as e:
            log.error(e)
            return False

        log.info("Got result %s", ret)
        if ret[0]:
            for s in strs:
                if s not in ret[1]:
                    log.error("can not found %s in %s", s, fp)
                    return False
            log.info("ks test %s is pass", fp)
            return True
        else:
            log.error(ret[1])
            return False

    def check_strs_in_cmd_output(self, cmd, strs, timeout):
        log.info("start to check if %s in %s output", strs, cmd)
        try:
            ret = self.run_cmd(cmd, timeout=timeout)
            log.info(ret)
        except CommandTimeout as e:
            log.error(e)
            return False

        log.info("Got result %s", ret)
        if ret[0]:
            for s in strs:
                if s not in ret[1]:
                    log.error("can not found %s in %s", s, cmd)
                    return False
            log.info("ks test %s is pass", cmd)
            return True
        else:
            log.error(ret[1])
            return False

    def match_strs_in_cmd_output(self, cmd, patterns, timeout):
        log.info("start to match if %s in %s output", patterns, cmd)
        try:
            ret = self.run_cmd(cmd, timeout=timeout)
            log.info("Got result %s", ret)
        except CommandTimeout as e:
            log.error(e)
            return False

        if ret[0]:
            lines = ret[1].split('\n')
            for p in patterns:
                for line in lines:
                    match = p.match(line.strip())
                    if match:
                        break
                else:
                    log.error("can not match pattern %s in %s", p, cmd)
                    return False
            return True
        else:
            log.error("run cmd %s failed", cmd)
            return False

class CheckCheck(CheckYoo):
    """"""

    def go_check(self, name):
        func = getattr(self, name.lower(), None)
        if func:
            return func()
        else:
            return self.default()

    def bond_01(self):
        return self.check_strs_in_file(
            '/etc/sysconfig/network-scripts/ifcfg-bond00',
            ('DEVICE=bond00', 'miimon=100 mode=balance-rr'),
            timeout=300)

    def fc_01_00(self):
        ck01 = self.check_strs_in_cmd_output('fdisk -l | grep "Linux LVM"',
                                             'LVM',
                                             timeout=300)
        ck02 = self.check_strs_in_cmd_output('lvs', '4.00g', timeout=300)

        return ck01 and ck02

    def firewall_01(self):
        return self.check_strs_in_cmd_output('firewall-cmd --state',
                                             'running',
                                             timeout=300)

    def iscsi_01(self):
        ck01 = self.check_strs_in_cmd_output('fdisk -l | grep "Linux LVM"',
                                             'LVM',
                                             timeout=300)
        return ck01

    def network_01(self):
        ck01 = self.check_strs_in_file(
            '/etc/sysconfig/network-scripts/ifcfg-em1',
            ('BOOTPROTO=dhcp',),
            timeout=300)

        return ck01

    def selinux_01(self):
        return self.check_strs_in_cmd_output('cat /etc/selinux/config',
                                             'SELINUX=enforcing',
                                             timeout=300)

    def services_01(self):
        ck01 = self.check_strs_in_cmd_output('systemctl status sshd',
                                             'active',
                                             timeout=300)
        return ck01

    def _install_check(self, auto_ks_file):
        '''
        local, fc, iscsi
        '''
        return self.check_strs_in_cmd_output('nodectl check',
                                             'Status: OK',
                                             timeout=300)

    def _static_network_check(self):
        '''
        case RHEVM-17800
        '''
        ck01 = self.check_strs_in_cmd_output('ip addr',
                                             'inet 10.66.148.9/22',
                                             timeout=300)
        ck02 = self.check_strs_in_cmd_output('ip route',
                                             'default via 10.66.151.254 dev enp2s0',
                                             timeout=300)
        return ck01 and ck02

    def _hostname_check(self):
        '''
        case RHEVM-17801
        '''
        return self.check_strs_in_cmd_output('hostname',
                                             'test.redhat.com',
                                             timeout=300)

    def _auto_partition_check(self):
        '''
        case RHEVM-17806
        '''
        # check mount points and fstype using df
        vgname = 'rhvh_dell--per510--01'
        lvpre = '/dev/mapper/%s' % vgname
        boot_device = '/dev/mapper/mpatha1'
        df_patterns = [re.compile(r'^%s-rhvh.*ext4.*/' % lvpre),
                       re.compile(r'^%s.*ext4.*/boot' % boot_device),
                       re.compile(r'^%s-var.*ext4.*/var') % lvpre]
        ck01 = self.match_strs_in_cmd_output('df -Th',
                                             df_patterns,
                                             timeout=300)

        # check pool
        poolname = 'pool00'
        lvs_patterns = [re.compile(r'^root.*%s' % poolname),
                        re.compile(r'^rhvh.*%s\s*root$' % poolname),
                        re.compile(r'^rhvh.*%s\s*rhvh' % poolname),
                        re.compile(r'^var.*%s' % poolname),
                        re.compile(r'^swap.*m$')]
        ck02 = self.match_strs_in_cmd_output('lvs --units m',
                                             lvs_patterns,
                                             timeout=300)

        # check /, /var, /boot size
        cmd = "expr 15360 - $(lvs --noheadings -o size --unit=m --nosuffix %s/%s | sed -r 's/\s*([0-9]+)\..*/\1/')" % (vgname, 'var')
        ck03 = self.check_strs_in_cmd_output(cmd, '0', timeout=300)

        cmd = "expr 6 \*1024 - $(lvs --noheadings -o size --unit=m --nosuffix %s/%s | sed -r 's/\s*([0-9]+)\..*/\1/')" % (vgname, 'root')
        ck04 = self.check_strs_in_cmd_output(cmd, '-', timeout=300)

        cmd = "expr 1024 \* 1024 - $(fdisk -s %s)" % boot_device
        ck05 = self.check_strs_in_cmd_output(cmd, '0', timeout=300)

        return ck01 and ck02 and ck03 and ck04 and ck05

    def _manually_partition_check(self):
        '''
        case RHEVM-17807
        '''
        # check mount points and fstype using df
        vgname = 'rhvh'
        lvpre = '/dev/mapper/%s' % vgname
        boot_device = '/dev/sda1'
        df_patterns = [re.compile(r'^%s-rhvh.*ext4.*/' % lvpre),
                       re.compile(r'^%s.*ext4.*/boot' % boot_device),
                       re.compile(r'^%s-var.*ext4.*/var' % lvpre),
                       re.compile(r'^%s-home.*xfs.*/home' % lvpre)]
        ck01 = self.match_strs_in_cmd_output('df -Th',
                                             df_patterns,
                                             timeout=300)

        # check size and pool
        poolname = 'pool'
        lvs_patterns = [re.compile(r'^root.*130000.*%s' % poolname),
                        re.compile(r'^rhvh.*130000.*%s\s*root$' % poolname),
                        re.compile(r'^rhvh.*130000.*%s\s*rhvh' % poolname),
                        re.compile(r'^var.*15360.*%s' % poolname),
                        re.compile(r'^home.*50000.*%s' % poolname),
                        re.compile(r'^swap.*8000.00m$')]
        ck02 = self.match_strs_in_cmd_output('lvs --units m',
                                             lvs_patterns,
                                             timeout=300)

        # check pool grow
        cmd = "expr 200000 - $(lvs --noheadings -o size --unit=m --nosuffix %s/%s | sed -r 's/\s*([0-9]+)\..*/\1/')" % (vgname, poolname)
        ck03 = self.check_strs_in_cmd_output(cmd, '-', timeout=300)

        # check /boot size
        cmd = "expr 1024 \* 1024 - $(fdisk -s %s)" % boot_device
        ck04 = self.check_strs_in_cmd_output(cmd, '0', timeout=300)

        return ck01 and ck02 and ck03 and ck04

    def _bond_vlan_check(self):
        '''
        case RHEVM-17816
        '''
        ck01 = self.check_strs_in_cmd_output('ip addr',
                                             ('bond0.50', '192.168.50.'),
                                             timeout=300)
        ck02 = self.check_strs_in_file('/etc/sysconfig/network-scripts/ifcfg-bond0',
                                       'mode=active-backup,primary=p1p1,miimon=100',
                                       timeout=300)
        return ck01 and ck02

    def _lang_check(self):
        '''
        case RHEVM-17798
        '''
        return self.check_strs_in_cmd_output('localectl status',
                                             'LANG=en_US.UTF-8',
                                             timeout=300)

    def _ntp_check(self):
        '''
        case RHEVM-17802
        '''
        return self.check_strs_in_file('/etc/ntp.conf',
                                       'clock02.util.phx2.redhat.com',
                                       timeout=300)

    def _us_keyboard_check(self):
        '''
        case RHEVM-17803
        '''
        return self.check_strs_in_cmd_output('localectl status',
                                             ('VC Keymap: us', 'X11 Layout: us'),
                                             timeout=300)

    def _ge_keyboard_check(self):
        '''
        case RHEVM-17804
        '''
        return self.check_strs_in_cmd_output('localectl status',
                                             ('VC Keymap: ge', 'X11 Layout: ge'),
                                             timeout=300)

    def _security_policy_check(self):
        '''
        case RHEVM-17805
        '''
        return self.check_strs_in_cmd_output('ll /root',
                                             'openscap_data',
                                             timeout=300)

    def _kdump_check(self):
        '''
        case RHEVM-17808
        '''
        return self.check_strs_in_file('/etc/grub2.cfg',
                                       'crashkernel=200M',
                                       timeout=300)

    def _users_check(self):
        '''
        case RHEVM-17811
        '''
        ck01 = self.check_strs_in_file('/etc/passwd',
                                       'test',
                                       timeout=300)
        ck02 = self.check_strs_in_file('/etc/shadow',
                                       'test',
                                       timeout=300)
        ck03 = self.check_strs_in_cmd_output('ll /home',
                                             'test',
                                             timeout=300)
        return ck01 and ck02 and ck03


    def _multi_disks_check(self):
        '''
        case RHEVM-17813
        '''
        pass


    def local_01(self):
        ck = {}
        # tier1
        ck['RHEVM-17788'] = self._install_check(KS_FILES_AUTO_DIR + 'ati_local_01.ks')
        ck['RHEVH-17800'] = self._static_network_check()
        ck['RHEVH-17801'] = self._hostname_check()
        ck['RHEVH-17807'] = self._manually_partition_check()
        ck['RHEVH-17826'] = ck['RHEVM-17788']
        ck['RHEVH-17828'] = ck['RHEVM-17788']

        # tier2
        ck['RHEVH-17798'] = self._lang_check()
        ck['RHEVH-17802'] = self._ntp_check()
        ck['RHEVH-17803'] = self._us_keyboard_check()
        ck['RHEVH-17805'] = self._security_policy_check()
        ck['RHEVH-17808'] = self._kdump_check()
        ck['RHEVH-17811'] = self._users_check()

        return ck

    def local_02(self):
        ck = {}
        # tier2
        ck['RHEVM-17804'] = self._ge_keyboard_check()

        return ck

    def fc_01(self):
        ck = {}
        # tier1
        ck['RHEVM-17790'] = self._install_check(KS_FILES_AUTO_DIR + 'ati_fc_01.ks')
        ck['RHEVM-17806'] = self._auto_partition_check()
        ck['RHEVM-17816'] = self._bond_vlan_check()
        ck['RHEVM-16972'] = ck['RHEVM-17806']

        return ck

    def default(self, name):
        log.info("Can't find corresponding check function for {}" +
                 "Perform basic check, " +
                 "installation is finished, reboot is success".format(name))
        ck01 = True
        return ck01


if __name__ == '__main__':
    # 10.73.75.219
    ck = CheckCheck()
    ck.host_string, ck._host_user, ck.host_pass = ('10.73.75.228', 'root',
                                                   'redhat')
    print ck.go_check('bond_01')
