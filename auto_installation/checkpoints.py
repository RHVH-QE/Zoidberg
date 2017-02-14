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
        ret = None
        try:
            with settings(
                    host_string=self.host_string,
                    user=self.host_user,
                    password=self.host_pass,
                    disable_known_hosts=True,
                    connection_attempts=60):
                ret = get(remote_path, local_path)
                if ret.succeeded:
                    return True
                else:
                    return False
        except Exception:
            return False

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

        if os.path.exists(LOCAL_CHECKDATA_MAP_PKL):
            os.system('rm -f {}'.format(LOCAL_CHECKDATA_MAP_PKL))

        ret = self.get_remote_file(REMOTE_CHECKDATA_MAP_PKL,
                                   LOCAL_CHECKDATA_MAP_PKL)
        if ret:
            fp = open(LOCAL_CHECKDATA_MAP_PKL, 'rb')
            self._checkdata_map = pickle.load(fp)
            fp.close()

            log.info("Change %s to data finished", CHECKDATA_MAP_PKL)

            return True
        else:
            raise ValueError("Can't get checkdata_map")

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

    def _check_device_ifcfg_value(self, nic, key_value_map):
        patterns = []
        for key, value in key_value_map.items():
            patterns.append(re.compile(r'^{}="?{}"?$'.format(key, value)))

        ifcfg_file = "/etc/sysconfig/network-scripts/ifcfg-{}".format(nic)
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

    def _check_manual_partition_mnt_fstype(self):
        vgname = self._checkdata_map.get('volgroup').get('name')
        lvpre = '/dev/mapper/{}'.format(vgname)
        boot_device = self._checkdata_map.get('boot').get('device')

        df_patterns = []
        logvol_map = self._checkdata_map.get('logvol')
        for lv in logvol_map:
            if lv == 'pool' or lv == 'swap':
                continue
            fstype = logvol_map.get(lv).get('fstype')
            name = logvol_map.get(lv).get('name')
            if lv == '/':
                pattern = re.compile(
                    r'^{}-rhvh.*{}.*{}'.format(lvpre, fstype, lv))
            else:
                pattern = re.compile(
                    r'^{}-{}.*{}.*{}'.format(lvpre, name, fstype, lv))

            df_patterns.append(pattern)

        pattern = re.compile(r'^{}.*ext4.*/boot'.format(boot_device))
        df_patterns.append(pattern)

        return self.match_strs_in_cmd_output(
            'df -Th', df_patterns, timeout=300)

    def _check_manual_partition_size(self):
        # check lv size
        vgname = self._checkdata_map.get('volgroup').get('name')
        logvol_map = self._checkdata_map.get('logvol')
        for lv in logvol_map:
            if logvol_map.get(lv).get('grow'):
                cmd = "expr {} - $(lvs --noheadings -o size --unit=m --nosuffix {}/{} | sed -r 's/\s*([0-9]+)\..*/\\1/')".format(
                    logvol_map.get(lv).get('size'), vgname,
                    logvol_map.get(lv).get('name'))

                ck = self.check_strs_in_cmd_output(cmd, '-', timeout=300)
            else:
                cmd = "lvs --noheadings -o size --unit=m --nosuffix {}/{} | sed -r 's/\s*([0-9]+)\..*/\\1/'".format(
                    vgname, logvol_map.get(lv).get('name'))
                ck = self.check_strs_in_cmd_output(
                    cmd, logvol_map.get(lv).get('size'), timeout=300)
            if not ck:
                return False
        # check /boot size
        ck = self._check_boot_size()

        return ck

    def _check_auto_partition_mnt_fstype(self):
        vgname = self._checkdata_map.get('volgroup').get('name')
        lvpre = '/dev/mapper/{}'.format(vgname)
        boot_device = self._checkdata_map.get('boot').get('device')
        df_patterns = [
            re.compile(r'^{}-rhvh.*ext4.*/'.format(lvpre)),
            re.compile(r'^{}.*ext4.*/boot'.format(boot_device)),
            re.compile(r'^{}-var.*ext4.*/var'.format(lvpre))
        ]

        return self.match_strs_in_cmd_output(
            'df -Th', df_patterns, timeout=300)

    def _check_auto_partition_size(self):
        vgname = self._checkdata_map.get('volgroup').get('name')
        # check /var
        cmd = "lvs --noheadings -o size --unit=m --nosuffix {}/{} | sed -r 's/\s*([0-9]+)\..*/\\1/'".format(
            vgname, 'var')
        ck01 = self.check_strs_in_cmd_output(cmd, '15360', timeout=300)
        # check /
        cmd = "expr 6 \* 1024 - $(lvs --noheadings -o size --unit=m --nosuffix {}/{} | sed -r 's/\s*([0-9]+)\..*/\\1/')".format(
            vgname, 'root')
        ck02 = self.check_strs_in_cmd_output(cmd, '-', timeout=300)
        # check /boot
        ck03 = self._check_boot_size()

        return ck01 and ck02 and ck03

    def _check_boot_size(self):
        boot_device = self._checkdata_map.get('boot').get('device')
        boot_size = int(self._checkdata_map.get('boot').get('size')) * 1024
        cmd = "fdisk -s {}".format(boot_device)

        return self.check_strs_in_cmd_output(cmd, str(boot_size), timeout=300)

    def install_check(self):
        return self.check_strs_in_cmd_output(
            'nodectl check', 'Status: OK', timeout=300)

    def manually_partition_check(self):
        # check mount points and fstype using df
        ck01 = self._check_manual_partition_mnt_fstype()
        # check size and pool
        ck02 = self._check_manual_partition_size()

        return ck01 and ck02

    def auto_partition_check(self):
        # check mount points and fstype using df
        ck01 = self._check_auto_partition_mnt_fstype()
        # check /, /var, /boot size
        ck02 = self._check_auto_partition_size()

        return ck01 and ck02

    def static_network_check(self):
        nic = self._checkdata_map.get('network').get('static').get('device')
        ipv4 = self._checkdata_map.get('network').get('static').get('ip')
        netmask = self._checkdata_map.get('network').get('static').get(
            'netmask')
        gateway = self._checkdata_map.get('network').get('static').get(
            'gateway')
        onboot = self._checkdata_map.get('network').get('static').get('onboot')

        key_value_map = {}
        key_value_map['BOOTPROTO'] = 'static'
        key_value_map['IPADDR'] = ipv4
        key_value_map['NETMASK'] = netmask
        key_value_map['GATEWAY'] = gateway
        key_value_map['ONBOOT'] = onboot

        ck01 = self._check_device_ifcfg_value(nic, key_value_map)

        ck02 = self._check_device_ipv4_address(nic, ipv4)

        ck03 = self._check_device_connected([nic])

        return ck01 and ck02 and ck03

    def bond_check(self):
        bond_device = self._checkdata_map.get('network').get('bond').get(
            'device')
        bond_slaves = self._checkdata_map.get('network').get('bond').get(
            'slaves')
        bond_opts = self._checkdata_map.get('network').get('bond').get('opts')
        bond_onboot = self._checkdata_map.get('network').get('bond').get(
            'onboot')

        key_value_map = {}
        key_value_map['DEVICE'] = bond_device
        key_value_map['TYPE'] = 'Bond'
        key_value_map['BONDING_OPTS'] = bond_opts
        key_value_map['ONBOOT'] = bond_onboot

        ck01 = self._check_bond_has_slave(bond_device, bond_slaves)
        ck02 = self._check_device_ifcfg_value(bond_device, key_value_map)
        ck03 = self._check_device_connected([bond_device] + bond_slaves)

        return ck01 and ck02 and ck03

    def vlan_check(self):
        vlan_device = self._checkdata_map.get('network').get('vlan').get(
            'device')
        vlan_id = self._checkdata_map.get('network').get('vlan').get('id')
        vlan_onboot = self._checkdata_map.get('network').get('vlan').get(
            'onboot')

        key_value_map = {}
        key_value_map['DEVICE'] = vlan_device
        key_value_map['TYPE'] = 'Vlan'
        key_value_map['BOOTPROTO'] = 'dhcp'
        key_value_map['VLAN_ID'] = vlan_id
        key_value_map['ONBOOT'] = vlan_onboot

        ck01 = self._check_device_ifcfg_value(vlan_device, key_value_map)
        ck02 = self._check_device_connected([vlan_device])

        return ck01 and ck02

    def bond_vlan_check(self):
        ck01 = self.bond_check()
        ck02 = self.vlan_check()
        return ck01 and ck02

    def nic_stat_dur_install_check(self):
        nic_device = self._checkdata_map.get('network').get('nic').get(
            'device')
        nic_onboot = self._checkdata_map.get('network').get('nic').get(
            'onboot')
        nic_status_dur_install = self._checkdata_map.get('network').get(
            'nic').get('status')

        key_value_map = {}
        key_value_map['DEVICE'] = nic_device
        key_value_map['ONBOOT'] = nic_onboot

        ck01 = not nic_status_dur_install
        ck02 = self._check_device_ifcfg_value(nic_device, key_value_map)
        ck03 = self._check_device_connected(
            [nic_device], expected_result='false')

        return ck01 and ck02 and ck03

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

    def multi_disks_check(self):
        pass

    def check(self):
        # set checkdata_map
        self._set_checkdata_map()
        # get checkpoint cases map
        checkpoint_cases_map = self._get_checkpoint_cases_map()

        # run check
        log.info("Start to run check points, please wait...")
        cks = {}
        for checkpoint, cases in checkpoint_cases_map.items():
            ck = self.go_check(checkpoint)
            for case in cases:
                cks[case] = ck

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
    ck.host_string, ck._host_user, ck.host_pass = ('10.66.148.9', 'root',
                                                   'redhat')
    ck.beaker_name = CONST.DELL_PET105_01
    ck.ksfile = 'ati_local_01.ks'
    print ck.go_check()
