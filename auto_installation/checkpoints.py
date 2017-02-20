import logging
from fabric.api import settings, run, get
from fabric.exceptions import NetworkError, CommandTimeout

import re
import os
import pickle
import constants as CONST
from utils import get_testcase_map

log = logging.getLogger('bender')

REMOTE_TMP_FILE_DIR = '/boot/autotest'
CHECKDATA_MAP_PKL = 'checkdata_map.pkl'
REMOTE_CHECKDATA_MAP_PKL = os.path.join(REMOTE_TMP_FILE_DIR, CHECKDATA_MAP_PKL)
LOCAL_CHECKDATA_MAP_PKL = os.path.join(CONST.PROJECT_ROOT, 'logs',
                                       CHECKDATA_MAP_PKL)


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

    def get_remote_file(self, remote_path, local_path):
        with settings(
                host_string=self.host_string,
                user=self.host_user,
                password=self.host_pass,
                disable_known_hosts=True,
                connection_attempts=120):
            ret = get(remote_path, local_path)
            if not ret.succeeded:
                raise ValueError("Can't get {} from remote server:{}.".format(
                    remote_path, self.host_string))

    def run_cmd(self, cmd, timeout=60):
        ret = None
        try:
            with settings(
                    host_string=self.host_string,
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

    def __init__(self):
        self._beaker_name = None
        self._ksfile = None
        self._checkdata_map = None

    @property
    def beaker_name(self):
        return self._beaker_name

    @beaker_name.setter
    def beaker_name(self, val):
        self._beaker_name = val

    @property
    def ksfile(self):
        return self._ksfile

    @ksfile.setter
    def ksfile(self, val):
        self._ksfile = val

    def _set_checkdata_map(self):
        log.info("Start to read %s", REMOTE_CHECKDATA_MAP_PKL)

        try:
            if os.path.exists(LOCAL_CHECKDATA_MAP_PKL):
                os.system('rm -f {}'.format(LOCAL_CHECKDATA_MAP_PKL))

            self.get_remote_file(REMOTE_CHECKDATA_MAP_PKL,
                                 LOCAL_CHECKDATA_MAP_PKL)

            fp = open(LOCAL_CHECKDATA_MAP_PKL, 'rb')
            self._checkdata_map = pickle.load(fp)
            fp.close()

            log.info("Change %s to data finished", CHECKDATA_MAP_PKL)

        except Exception:
            raise
        return

    def _get_checkpoint_cases_map(self):
        # get testcase map
        testcase_map = get_testcase_map()
        # get ksfile name, machine name
        ksfile_name = self.ksfile
        machine_name = self.beaker_name

        checkpoint_cases_map = {}
        for key, value in testcase_map.items():
            if set((ksfile_name, machine_name)) < set(value):
                checkpoint = value[2]
                if checkpoint in checkpoint_cases_map:
                    checkpoint_cases_map[checkpoint].append(key)
                else:
                    checkpoint_cases_map[checkpoint] = []
                    checkpoint_cases_map[checkpoint].append(key)

        return checkpoint_cases_map

    def _check_device_ifcfg_value(self, device_data_map):
        patterns = []
        for key, value in device_data_map.items():
            if key.isupper():
                patterns.append(re.compile(r'^{}="?{}"?$'.format(key, value)))

        ifcfg_file = "/etc/sysconfig/network-scripts/ifcfg-{}".format(
            device_data_map.get('DEVICE'))
        cmd = 'cat {}'.format(ifcfg_file)

        return self.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_device_connected(self, nics, expected_result='yes'):
        patterns = []
        for nic in nics:
            if expected_result == 'yes':
                patterns.append(
                    re.compile(r'^.*{}.*:.*connected.*$'.format(nic)))
            else:
                patterns.append(
                    re.compile(r'^.*{}.*:.*disconnected.*$'.format(nic)))

        cmd = 'nmcli -t -f DEVICE,STATE dev'

        return self.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_device_ipv4_address(self, nic, ipv4):
        patterns = [re.compile(r'^inet\s+{}'.format(ipv4))]
        cmd = 'ip -f inet addr show {}'.format(nic)

        return self.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_bond_has_slave(self, bond, slaves, expected_result='yes'):
        patterns = []
        for slave in slaves:
            if expected_result == 'yes':
                patterns.append(re.compile(r'^Slave.*{}$'.format(slave)))
            else:
                patterns.append(
                    re.compile(r'^((?!Slave.*{}).)*$'.format(slave)))

        cmd = 'cat /proc/net/bonding/{}'.format(bond)

        return self.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_parts_mnt_fstype(self):
        partition = self._checkdata_map.get('partition')
        vgname = partition.get('volgroup').get('name')
        lvpre = '/dev/mapper/{}'.format(vgname)

        df_patterns = []
        for key in partition:
            if key in ['pool', 'swap', 'volgroup']:
                continue

            part = partition.get(key)
            fstype = part.get('fstype')
            if part.get('lvm'):
                name = part.get('name')
                if key == '/':
                    pattern = re.compile(
                        r'^{}-rhvh.*{}.*{}'.format(lvpre, fstype, key))
                else:
                    pattern = re.compile(
                        r'^{}-{}.*{}.*{}'.format(lvpre, name, fstype, key))
            else:
                part_device = part.get('drive') + part.get('partnum')
                pattern = re.compile(
                    r'^{}.*{}.*{}'.format(part_device, fstype, key))

            df_patterns.append(pattern)

        return self.match_strs_in_cmd_output(
            'df -Th', df_patterns, timeout=300)

    def _check_parts_size(self):
        partition = self._checkdata_map.get('partition')
        vgname = partition.get('volgroup').get('name')

        for key in partition:
            if key in ['volgroup']:
                continue

            part = partition.get(key)
            if part.get('lvm'):
                if part.get('percent'):
                    cmd = 'python -c "print int(' \
                        "round($(lvs --noheadings -o size --unit=m --nosuffix {}/{}) * 100 / " \
                        '$(vgs --noheadings -o size --unit=m --nosuffix {})))"'.format(vgname, part.get('name'), vgname)
                else:
                    cmd = "lvs --noheadings -o size --unit=m --nosuffix {}/{} | sed -r 's/\s*([0-9]+)\..*/\\1/'".format(
                        vgname, part.get('name'))
            else:
                cmd = "expr $(fdisk -s {}) / 1024".format(
                    part.get('drive') + part.get('partnum'))

            ret = self.run_cmd(cmd, timeout=300)

            if ret[0]:
                part_real_size = ret[1]
            else:
                return False

            if part.get('grow'):
                if int(part_real_size) <= int(part.get('size')):
                    return False
                else:
                    maxsize = part.get('maxsize')
                    if maxsize and int(part_real_size) > int(maxsize):
                        return False
            else:
                if int(part_real_size) != int(part.get('size')):
                    return False

        return True

    def install_check(self):
        return self.check_strs_in_cmd_output(
            'nodectl check', 'Status: OK', timeout=300)

    def partition_check(self):
        ck01 = self._check_parts_mnt_fstype()
        ck02 = self._check_parts_size()

        return ck01 and ck02

    def static_network_check(self):
        device_data_map = self._checkdata_map.get('network').get('static')
        nic_device = device_data_map.get('DEVICE')
        nic_ipv4 = device_data_map.get('IPADDR')

        ck01 = self._check_device_ifcfg_value(device_data_map)
        ck02 = self._check_device_ipv4_address(nic_device, nic_ipv4)
        ck03 = self._check_device_connected([nic_device])

        return ck01 and ck02 and ck03

    def bond_check(self):
        device_data_map = self._checkdata_map.get('network').get('bond')
        bond_device = device_data_map.get('DEVICE')
        bond_slaves = device_data_map.get('slaves')

        ck01 = self._check_device_ifcfg_value(device_data_map)
        ck02 = self._check_bond_has_slave(bond_device, bond_slaves)
        ck03 = self._check_device_connected([bond_device] + bond_slaves)

        return ck01 and ck02 and ck03

    def vlan_check(self):
        device_data_map = self._checkdata_map.get('network').get('vlan')
        vlan_device = device_data_map.get('DEVICE')

        ck01 = self._check_device_ifcfg_value(device_data_map)
        ck02 = self._check_device_connected([vlan_device])

        return ck01 and ck02

    def bond_vlan_check(self):
        ck01 = self.bond_check()
        ck02 = self.vlan_check()
        return ck01 and ck02

    def nic_stat_dur_install_check(self):
        device_data_map = self._checkdata_map.get('network').get('nic')
        nic_device = device_data_map.get('DEVICE')
        nic_status_dur_install = device_data_map.get('status')

        ck01 = not nic_status_dur_install
        ck02 = self._check_device_ifcfg_value(device_data_map)
        ck03 = self._check_device_connected(
            [nic_device], expected_result='false')

        return ck01 and ck02 and ck03

    def dhcp_network_check(self):
        device_data_map = self._checkdata_map.get('network').get('dhcp')
        nic_device = device_data_map.get('DEVICE')

        ck01 = self._check_device_ifcfg_value(device_data_map)
        ck02 = self._check_device_connected([nic_device])

        return ck01 and ck02

    def hostname_check(self):
        hostname = self._checkdata_map.get('network').get('hostname')
        return self.check_strs_in_cmd_output('hostname', hostname, timeout=300)

    def lang_check(self):
        lang = self._checkdata_map.get('lang')
        return self.check_strs_in_cmd_output(
            'localectl status', lang, timeout=300)

    def ntp_check(self):
        ntp = self._checkdata_map.get('ntpservers')
        return self.check_strs_in_file('/etc/ntp.conf', ntp, timeout=300)

    def keyboard_check(self):
        vckey = self._checkdata_map.get('keyboard').get('vckeymap')
        xlayouts = self._checkdata_map.get('keyboard').get('xlayouts')
        return self.check_strs_in_cmd_output(
            'localectl status',
            ('VC Keymap: {}'.format(vckey), 'X11 Layout: {}'.format(xlayouts)),
            timeout=300)

    def security_policy_check(self):
        return self.check_strs_in_cmd_output(
            'ls /root', 'openscap_data', timeout=300)

    def kdump_check(self):
        reserve_mb = self._checkdata_map.get('kdump').get('reserve-mb')
        return self.check_strs_in_file(
            '/etc/grub2.cfg',
            'crashkernel={}M'.format(reserve_mb),
            timeout=300)

    def users_check(self):
        username = self._checkdata_map.get('user').get('name')
        ck01 = self.check_strs_in_file('/etc/passwd', username, timeout=300)
        ck02 = self.check_strs_in_file('/etc/shadow', username, timeout=300)
        ck03 = self.check_strs_in_cmd_output('ls /home', username, timeout=300)
        return ck01 and ck02 and ck03

    def firewall_check(self):
        return self.check_strs_in_cmd_output(
            'firewall-cmd --state', 'running', timeout=300)

    def selinux_check(self):
        selinux_status = self._checkdata_map.get('selinux')
        strs = 'SELINUX={}'.format(selinux_status)
        return self.check_strs_in_file(
            '/etc/selinux/config', strs, timeout=300)

    def sshd_check(self):
        return self.check_strs_in_cmd_output(
            'systemctl status sshd', 'running', timeout=300)

    def grubby_check(self):
        checkstr = self._checkdata_map.get('grubby')

        return self.check_strs_in_cmd_output(
            'grubby --info=0', checkstr, timeout=300)

    def bootloader_check(self):
        boot_device = self._checkdata_map.get('partition').get('/boot').get(
            'drive')
        cmd = 'dd if={} bs=512 count=1 2>&1 | strings |grep -i grub'.format(
            boot_device)

        return self.check_strs_in_cmd_output(cmd, 'GRUB', timeout=300)

    def check(self):
        cks = {}
        try:
            # set checkdata_map
            self._set_checkdata_map()
            # get checkpoint cases map
            checkpoint_cases_map = self._get_checkpoint_cases_map()

            # run check
            log.info("Start to run check points, please wait...")

            for checkpoint, cases in checkpoint_cases_map.items():
                try:
                    ck = self.go_check(checkpoint)
                    for case in cases:
                        cks[case] = ck
                except NameError as e:
                    log.error(e)
        except Exception as e:
            log.error(e)

        return cks

    def go_check(self, name='check'):
        func = getattr(self, name.lower(), None)
        if func:
            return func()
        else:
            raise NameError(
                'The checkpoint function {} is not defined'.format(name))


if __name__ == '__main__':
    # 10.73.75.219
    ck = CheckCheck()
    ck.host_string, ck._host_user, ck.host_pass = ('10.73.75.58', 'root',
                                                   'redhat')
    ck.beaker_name = CONST.DELL_PER510_01
    ck.ksfile = 'ati_fc_01.ks'
    print ck.go_check()
