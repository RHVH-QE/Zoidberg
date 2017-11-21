import logging
import requests
import os
import time
import re
from fabric.network import disconnect_all
from check_comm import CheckYoo
from constants import KS_FILES_DIR, DELL_PET105_01, DELL_PER510_01, DELL_PER515_01
from const_upgrade import CHECK_NEW_LVS, RHVM_DATA_MAP, \
    RHVH_UPDATE_RPM_URL, \
    KERNEL_SPACE_RPM_URL, \
    FABRIC_TIMEOUT, YUM_UPDATE_TIMEOUT, YUM_INSTALL_TIMEOUT, \
    CHK_HOST_ON_RHVM_STAT_MAXCOUNT, CHK_HOST_ON_RHVM_STAT_INTERVAL, \
    ENTER_SYSTEM_MAXCOUNT, ENTER_SYSTEM_INTERVAL, ENTER_SYSTEM_TIMEOUT
from rhvmapi import RhevmAction
from __builtin__ import False

log = logging.getLogger('bender')


class CheckUpgrade(CheckYoo):
    """"""

    def __init__(self):
        self._source_build = None
        self._target_build = None
        self._update_rpm_path = None
        self._check_infos = {}
        self._add_file_name = "/etc/upgrade_test"
        self._add_file_content = "test"
        self._update_file_name = "/etc/my.cnf"
        self._update_file_content = "# test"
        self._add_var_file_name = "/var/upgrade_test_var"
        self._update_var_log_file_name = "/var/log/maillog"
        self._kernel_space_rpm = None
        self._user_space_rpms_set = None
        self._default_gateway = None
        self._default_nic = None
        self._rhvm = None
        self._rhvm_fqdn = None
        self._dc_name = None
        self._cluster_name = None
        self._host_name = None
        self._host_ip = None
        self._host_vlanid = None
        self._host_cpu_type = None

    @property
    def source_build(self):
        return self._source_build

    @source_build.setter
    def source_build(self, val):
        self._source_build = val

    @property
    def target_build(self):
        return self._target_build

    @target_build.setter
    def target_build(self, val):
        self._target_build = val

    ##########################################
    # check methods
    ##########################################
    def _check_imgbased_ver(self):
        old_imgbased_ver = self._check_infos.get("old").get("imgbased_ver")
        new_imgbased_ver = self._check_infos.get("new").get("imgbased_ver")
        old_ver_nums = old_imgbased_ver.split('-')[1].split('.')
        new_ver_nums = new_imgbased_ver.split('-')[1].split('.')

        log.info("Check imgbased ver:\n  old_ver_num=%s\n  new_ver_num=%s",
                 old_ver_nums, new_ver_nums)

        if len(old_ver_nums) != len(new_ver_nums):
            log.error(
                "The lengths of old version number and new version number are not equal."
            )
            return False

        for i in range(len(new_ver_nums)):
            if int(old_ver_nums[i]) > int(new_ver_nums[i]):
                log.error(
                    "The old version number is bigger than the new version number."
                )
                return False
        return True

    def _check_update_ver(self):
        old_update_ver = self._check_infos.get("old").get("update_ver")
        new_update_ver = self._check_infos.get("new").get("update_ver")
        target_ver_num = self.target_build.split("-host-")[-1]

        log.info(
            "Check update ver:\n  old_update_ver=%s\n  new_update_ver=%s\n  target_ver_num=%s",
            old_update_ver, new_update_ver, target_ver_num)

        if "placeholder" not in old_update_ver:
            log.error("The old update version is wrong.")
            return False
        if target_ver_num not in new_update_ver:
            log.error("The new update version is wrong.")
            return False

        return True

    def _check_imgbase_w(self):
        old_imgbase_w = self._check_infos.get("old").get("imgbase_w")
        new_imgbase_w = self._check_infos.get("new").get("imgbase_w")
        old_ver = old_imgbase_w[-12:-4]
        new_ver = new_imgbase_w[-12:-4]

        log.info("Check imgbase w:\n  old_imgbase_w=%s\n  new_imgbase_w=%s",
                 old_ver, new_ver)
        # The ver number in `imgbase w` sometimes is different from the one in the build name
        # So, do not check whether the ver number is in the build name.
        '''
        if old_ver not in self.source_build:
            log.error("The old rhvh build is not the desired one.")
            return False
        if new_ver not in self.target_build:
            log.error("The new rhvh build is not the desired one.")
            return False
        '''
        if new_ver <= old_ver:
            log.error(
                "The new rhvh build version is not newer than the old one.")
            return False

        return True

    def _check_imgbase_layout(self):
        old_imgbase_w = self._check_infos.get("old").get("imgbase_w")
        new_imgbase_w = self._check_infos.get("new").get("imgbase_w")
        old_imgbase_layout = self._check_infos.get("old").get("imgbase_layout")
        new_imgbase_layout = self._check_infos.get("new").get("imgbase_layout")
        old_layout_from_imgbase_w = old_imgbase_w.split()[-1]
        new_layout_from_imgbase_w = new_imgbase_w.split()[-1]

        log.info(
            "Check imgbase layout:\n  old_imgbase_layout:\n%s\n  new_imgbase_layout:\n%s",
            old_imgbase_layout, new_imgbase_layout)

        if old_layout_from_imgbase_w not in old_imgbase_layout:
            log.error(
                "The old imgbase layer is not present in the old imgbase layout cmd."
            )
            return False
        if old_imgbase_layout not in new_imgbase_layout:
            log.error(
                "The old imgbase layer is not present in the new imgbase layout cmd."
            )
            return False
        if new_layout_from_imgbase_w not in new_imgbase_layout:
            log.error(
                "The new imgbase layer is not present in the new imgbase layout cmd."
            )
            return False

        return True

    def _check_iqn(self):
        old_iqn = self._check_infos.get("old").get("initiatorname_iscsi")
        new_iqn = self._check_infos.get("new").get("initiatorname_iscsi")

        log.info("Check iqn:\n  old_iqn=%s\n  new_iqn=%s", old_iqn, new_iqn)

        if old_iqn.split(":")[-1] != new_iqn.split(":")[-1]:
            log.error("The old iqn is not equal to the new one.")
            return False

        return True

    def _check_pool_tmeta_size(self, old_lvs, new_lvs):
        old_size = [
            x.split()[-1] for x in old_lvs if re.match(r'\[pool.*_tmeta\]', x)
        ][0]
        new_size = [
            x.split()[-1] for x in new_lvs if re.match(r'\[pool.*_tmeta\]', x)
        ][0]
        old_size = int(old_size.split('.')[0])
        new_size = int(new_size.split('.')[0])

        log.info("Check pool_tmeta size:\n  old_size=%s\n  new_size=%s",
                 old_size, new_size)

        if old_size < 1024:
            if new_size != 1024:
                log.error(
                    "The old pool_tmeta size if lower than 1024M, but the new one is not equal to 1024M."
                )
                return False
        else:
            if new_size != old_size:
                log.error(
                    "The old pool_tmeta size is bigger than 1024M, but the new one is not equal to the old one."
                )
                return False

        return True

    def _check_lv_layers(self, new_lvs):
        new_ver_1 = self._check_infos.get("new").get("imgbase_w").split()[-1]
        new_ver = new_ver_1.split("+")[0]
        for key in [new_ver_1, new_ver]:
            for line in new_lvs:
                if key in line:
                    break
            else:
                log.error("Layer %s dosn't exist.", key)
                return False

        return True

    def _check_lv_new(self, old_lvs, new_lvs):
        if not CHECK_NEW_LVS:
            return True

        log.info("Check newly add lv...")
        new_lv = {
            "home": "1024.00m",
            "tmp": "1024.00m",
            "var_log": "8192.00m",
            "var_log_audit": "2048.00m"
        }
        diff = list(set(new_lvs) - set(old_lvs))

        for k, v in new_lv.items():
            in_old = [x for x in old_lvs if re.match(r'{} '.format(k), x)]
            in_diff = [x for x in diff if re.match(r'{} '.format(k), x)]
            if in_old:
                if in_diff:
                    log.error(
                        "%s already exists in old layer, it shouldn't be changed in new layer.",
                        k)
                    return False
            else:
                if not in_diff:
                    log.error(
                        "%s doesn't exist in old layer, it should be added in new layer.",
                        k)
                    return False
                else:
                    size = in_diff[0].split()[-1]
                    if v != size:
                        log.error(
                            "%s is added in new layer, but it's size %s is not equal to the desired %s",
                            k, size, v)
                        return False

        return True

    def _check_lvs(self):
        old_lvs = [
            x.strip()
            for x in self._check_infos.get("old").get("lvs").split("\r\n")
            if "WARNING" not in x
        ]
        new_lvs = [
            x.strip()
            for x in self._check_infos.get("new").get("lvs").split("\r\n")
        ]

        diff = list(set(old_lvs) - set(new_lvs))
        if len(diff) >= 2 or (len(diff) == 1 and not re.match(
                r'\[pool.*_tmeta\]', diff[0])):
            log.error("new lvs doesn't include items in old lvs. diff=%s",
                      diff)
            return False

        log.info("Check lvs.")

        ret1 = self._check_lv_layers(new_lvs)
        ret2 = self._check_lv_new(old_lvs, new_lvs)
        ret3 = self._check_pool_tmeta_size(old_lvs, new_lvs)

        return ret1 and ret2 and ret3

    def _check_findmnt(self):
        old_findmnt = [
            x.strip()
            for x in self._check_infos.get("old").get("findmnt").split('\r\n')
        ]
        new_findmnt = [
            x.strip()
            for x in self._check_infos.get("new").get("findmnt").split('\r\n')
        ]
        diff = list(set(new_findmnt) - set(old_findmnt))
        new_ver = self._check_infos.get("new").get("imgbase_w").split()[
            - 1].replace("-", "--")

        log.info("Check findmnt:\n  diff=%s", diff)

        new_mnt = [new_ver]
        if CHECK_NEW_LVS:
            new_mnt = new_mnt + ['/home', '/tmp', '/var/log', '/var/log/audit']

        for key in new_mnt:
            in_old = [x for x in old_findmnt if key in x]
            in_diff = [x for x in diff if key in x]

            if in_old:
                if key == new_ver:
                    log.error("New layer %s shouldn't present in old findmnt.",
                              new_ver)
                    return False
                if in_diff:
                    log.error(
                        "Mount point %s already exists in old layer, it shouldn't be changed in new layer.",
                        key)
                    return False
            else:
                if not in_diff:
                    log.error(
                        "Mount point %s hasn't been created in new layer.",
                        key)
                    return False

        return True

    def _check_need_to_verify_new_lv(self):
        src_build_time = self.source_build.split('-')[-1].split('.')[0]
        tar_build_time = self.target_build.split('-')[-1].split('.')[0]

        if src_build_time > "20170616" or tar_build_time <= "20170616":
            log.info("No need to check newly added lv.")
            return False

        return True

    def _check_cockpit_connection(self):
        log.info("Check cockpit connection.")

        url = "http://{}:9090".format(self.host_string)
        try:
            r = requests.get(url, verify=False)
            if r.status_code == 200:
                ret = True
            else:
                log.error("Cockpit cannot be connected.")
                ret = False
        except Exception as e:
            log.error(e)
            ret = False

        return ret

    def _check_kernel_space_rpm(self):
        log.info("Start to check kernel space rpm.")

        # Get kernel version:
        cmd = "uname -r"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Get kernel version failed.")
            return False
        kernel_ver = ret[1]
        log.info("kernel version is %s", kernel_ver)

        # Check weak-updates:
        cmd = "ls /usr/lib/modules/{}/weak-updates/".format(kernel_ver)
        key = self._kernel_space_rpm.split('-')[1]
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0] or key not in ret[1]:
            log.error('The result of "%s" is %s,  not include %s.', cmd,
                      ret[1], key)
            return False
        log.info('The result of "%s" is %s.', cmd, ret[1])

        # Check /var/imgbased/persisted-rpms
        cmd = "ls /var/imgbased/persisted-rpms"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0] or self._kernel_space_rpm not in ret[1]:
            log.error("The result of %s is %s, not include %s", cmd, ret[1],
                      self._kernel_space_rpm)
            return False
        log.info("The result of %s is %s", cmd, ret[1])

        return True

    def _check_user_space_rpm(self):
        log.info("Start to check user space rpm.")

        cmd = "rpm -qa | grep httpd"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check user space rpm httpd faild. The result of "%s" is %s',
                cmd, ret[1])
            return False
        log.info('The result of "%s" is %s', cmd, ret[1])

        user_space_rpms_set = set(ret[1].splitlines())

        if not self._user_space_rpms_set:
            self._user_space_rpms_set = user_space_rpms_set
        else:
            if self._user_space_rpms_set ^ user_space_rpms_set:
                log.error("User space rpm httpd is not persisted.")
                return False

        return True

    def _check_iptables_status(self):
        log.info("Start to check iptables status.")

        cmd = "systemctl status iptables | grep 'Active: active' --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check iptables status failed. The result of "%s" is %s',
                cmd, ret[1])
            return False
        log.info('The result of "%s" is %s', cmd, ret[1])

        if "Active: active" in ret[1]:
            log.info('iptables is active.')
            return True
        else:
            log.info('iptables is not active.')
            return False

    def _check_firewalld_status(self):
        log.info("Start to check firewalld status.")

        cmd = "systemctl status firewalld | grep 'Active: active' --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        log.info('The result of "%s" is %s', cmd, ret[1])

        if "Active: active" in ret[1]:
            log.info('firewalld is active.')
            return False
        else:
            log.info('firewalld is not active.')
            return True

    def _start_ntpd(self):
        log.info("Start ntpd and enable ntpd...")
        cmd = "systemctl start ntpd.service"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Start ntpd failed.")
            return False
        log.info("Start ntpd successful.")
        ret01 = True

        cmd = "systemctl enable ntpd.service"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Enable ntpd failed.")
            return False
        log.info("Enable ntpd successful.")
        ret02 = True

        return ret01 and ret02

    def _check_ntpd_status(self):
        log.info("Start to check ntpd status.")

        cmd = "systemctl status ntpd | grep 'Active: active' --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        log.info('The result of "%s" is %s', cmd, ret[1])
        if "Active: active" not in ret[1]:
            if not self._start_ntpd():
                return False
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            log.info('The result of "%s" is %s', cmd, ret[1])
            if "Active: active" not in ret01[1]:
                log.info('ntpd is not active.')
                ret_01 = False
            else:
                log.info('ntpd is active.')
                ret_01 = True
        else:
            log.info('ntpd is active.')
            ret_01 = True

        cmd = "rpm -qa | egrep 'ntp-|chrony-' --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check rpm ntp and chrony failed. The result of "%s" is %s',
                cmd, ret[1])
            return False
        log.info('The result of "%s" is %s', cmd, ret[1])
        if "ntp-" in ret[1] and "chrony-" in ret[1]:
            ret_02 = True
        else:
            ret_02 = False

        return ret_01 and ret_02

    def _check_sysstat(self):
        log.info("Start to check sysstat collect data.")

        cmd = "ls /var/log/sa"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check sysstat collect data failed. The result of "%s" is %s',
                cmd, ret[1])
            return False
        log.info('The result of "%s" is %s', cmd, ret[1])

        if "No such file or directory" not in ret[1] and "sa" in ret[1]:
            log.info('sysstat can collect data')
            return True
        else:
            log.info('sysstat can not collect data')
            return False

    def _check_ovirt_imageio_daemon_status(self):
        log.info("Start to check ovirt-imageio-daemon status.")

        cmd = "systemctl status ovirt-imageio-daemon.service | grep 'Active: active' --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check ovirt-imageio-daemon status failed. The result of "%s" is %s',
                cmd, ret[1])
            return False
        log.info('The result of "%s" is %s', cmd, ret[1])
        if "Active: active" in ret[1]:
            log.info('ovirt-imageio-daemon is active.')
            ret01 = True
        else:
            log.info('ovirt-imageio-daemon is not active.')
            ret01 = False

        cmd = "ls -ld /var/log/ovirt-imageio-daemon/"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check ovirt-imageio-daemon owership failed. The result of "%s" is %s',
                cmd, ret[1])
            return False
        log.info('The result of "%s" is %s', cmd, ret[1])
        if "vdsm" in ret[1] and "kvm" in ret[1]:
            ret02 = True
        else:
            ret02 = False

        return ret01 and ret02

    def _check_boot_dmesg_log(self):
        log.info("Start to check /var/log/boot.log and /var/log/dmesg.")

        cmd = "egrep -i 'error|fail' /var/log/boot.log --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        log.info('The result of "%s" is %s', cmd, ret[1])
        if ret[1].strip(' ') != '':
            log.info('There are error or fail info in /var/log/boot.log')
            ret01 = False
        else:
            ret01 = True

        cmd = "egrep -i 'error|fail' /var/log/dmesg --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        log.info('The result of "%s" is %s', cmd, ret[1])
        if ret[1].strip(' ') != '':
            log.info('There are error or fail info in /var/log/dmesg')
            ret02 = False
        else:
            ret02 = True

        return ret01 and ret02

    def _check_separate_volumes(self):
        log.info("Start to check /var /var/log /var/log/audit /tmp /home on separate volumes .")

        cmd = "findmnt -D | egrep '/var|/var/log|/var/log/audit|/home|/tmp' --color=never"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check separate volumes failed. The result of "%s" is %s',
                cmd, ret[1])
            return False
        log.info('The result of "%s" is %s', cmd, ret[1])

        volumes_num = len(ret[1].splitlines())
        tar_build_time = self.target_build.split('-')[-1].split('.')[0]

        # For the build after rhvh-4.1.2, there should be /var, /var/log, /var/log/audit, /tmp, /home
        if tar_build_time >= "20170706":
            if volumes_num == 5:
                log.info('Check the %d special separate volumes right.', volumes_num)
                return True
            else:
                log.info('Check the %d special separate volumes failed.', volumes_num)
                return False
        # For the build before rhvh-4.1.2, there should be only one /var
        else:
            if volumes_num == 1 and "/var" in ret[1]:
                log.info('Check /var is separate volume.')
                return True
            else:
                log.info('Check /var is not separate volume..')
                return False

    def _reinstall_rpms(self):
        log.info("Start to reinstall rpms...")

        if not self._put_repo_to_host(repo_file="rhel73.repo"):
            return False
        if not self._mv_rpm_packages_on_host(packages_path = "/var/rpms-bak", packages_bak_path = "/var/imgbased/persisted-rpms", packages_files="*"):
            return False

        if not self._install_user_space_rpm():
            return False
        # if not self._del_repo_on_host(repo_file="rhel73.repo"):
        #     return False

        return True

    def _reinstall_rpms_check(self):
        log.info("Start to check reinstall rpms...")

        # There should be no user space rpm as initial after upgrade, due to moved packages and repo
        if self._check_user_space_rpm():
            log.error('There is user space rpm! Should be no user space rpm.')
            return False
        if not self._reinstall_rpms():
            return False

        if not self._check_user_space_rpm():
            return False

        return True

    ### Upgrade tier2, added by wujian ###
    # 1-check fips status, FIPS=1

    def _check_is_fips(self, is_fips=True):
        if is_fips:
            log.info("To check FIPs=1 in old build.")

            cmd = "cat /proc/sys/crypto/fips_enabled"
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            if not ret[0] or not int(ret[1]) == 1:
                return False
            else:
                log.info("Fips now is set as 1")
        else:
            log.info("FIPs now is set as default 0")
        return True

    # 2-check kdump.service =active
    def _check_kdump_status(self):
        log.info("Start to check kdump service status.")

        cmd = "systemctl status kdump.service | grep 'Active' | awk '{print $2}'"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)

        if not ret[0]:
            return False

        if ret[0]:
            if ret[1] != 'active':
                log.error("Kdump service is inactive.")
                return False
            else:
                log.info("Kdump service is active.")
        return True

    # 3-remove vg/lv, delete old layer info on /etc/grub2.cfg
    def _remove_lv(self):
        log.info("Start to remove VG/LV")

        cmd_pv = "lvs --noheading | awk '{print $1}' | grep '^rhvh'| sed -n '1,2p'"
        cmd_vg = "lvs --noheading | awk '{print $2}' | uniq"

        ret_pv = self.run_cmd(cmd_pv, timeout=FABRIC_TIMEOUT)
        ret_vg = self.run_cmd(cmd_vg, timeout=FABRIC_TIMEOUT)

        if not ret_pv[0] or not ret_vg[0]:
            return False
        else:
            ret_pv = ret_pv[1].split('\r\n')
            for i in range(2):
                cmd = "lvremove " + str(ret_vg[1]) + "/" + ret_pv[i]
                ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
                if not ret[0]:
                    log.error('Run cmd "%s" failed, the result is %s', cmd, ret[1])
                    return False

            log.info("Remove old layer successfully!")
        return True

    def _change_grub_file(self):
        log.info("start to change /etc/grub2.cfg.")
        old_build_cmd = "lvs --noheading | awk '{print $1}' | grep '^rhvh'| sed -n '1p'"
        ret_old_build = self.run_cmd(old_build_cmd, timeout=FABRIC_TIMEOUT)
        if not ret_old_build[0]:
            return False
        ret_old_build = str(ret_old_build[1])

        cmd = "sed -i '/^menuentry.*" + ret_old_build + "/,/^}/d' /etc/grub2.cfg \
        /boot/grub2/grub.cfg"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to delete old_build info on /etc/grub2.cfg \
            /boot/grub2/grub2.cfg")
            return False

        log.info("Successfully delete old_build info on /etc/grub2.cfg \
        /boot/grub2/grub.cfg")

        return True

    # 4-Upgrade with bond network
    def _is_bond_net(self, is_bond=False):
        log.info("Start to verify if bond network.")

        if is_bond:
            cmd = "ip -f inet addr show | grep '.*bond'| uniq | awk '{print $2}'|sed -n '1,2p'"
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            if not ret[0] or ("bond" not in ret[1]):
                log.error("No bond network detected.")
                return False
            log.info("bond network works successfully.")
            return True

        return True

    def _bond_status(self):
        old_bond_info = self._check_infos.get("old").get("bond_ip")
        new_bond_info = self._check_infos.get("New").get("bond_ip")

        log.info("check bond:\n  \
        old_bond_ip:\n %s\n  \
        new_bond_ip:\n %s",
        old_bond_info, new_bond_info)

        if old_bond_info != new_bond_info:
            log.error("bond network is changed after upgrade.")
            return False

        log.info("bond network keeps its status after upgrade.")
        return True



    #################
    # checks in cases
    #################
    def basic_upgrade_check(self):
        # To check imgbase w, imgbase layout, cockpit connection
        ck01 = self._check_imgbase_w()
        ck02 = self._check_imgbase_layout()
        ck03 = self._check_cockpit_connection()
        ck04 = self._check_host_status_on_rhvm()
        ck05 = self._check_iqn()

        return ck01 and ck02 and ck03 and ck04 and ck05

    def packages_check(self):
        ck01 = self._check_imgbased_ver()
        ck02 = self._check_update_ver()

        return ck01 and ck02

    def settings_check(self):
        ck01 = self.check_strs_in_file(
            self._add_file_name, [self._add_file_content],
            timeout=FABRIC_TIMEOUT)
        ck02 = self.check_strs_in_file(
            self._update_file_name, [self._update_file_content],
            timeout=FABRIC_TIMEOUT)

        return ck01 and ck02

    def roll_back_check(self):
        log.info("Roll back.")

        cmd = "imgbase rollback"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            return False

        ret = self._enter_system()
        if not ret[0]:
            return False

        if ret[1] != self._check_infos.get("old").get("imgbase_w"):
            return False
        if not self._check_host_status_on_rhvm():
            return False

        if "-4.0-" not in self.source_build:
            '''
            # incompatible with 7.4, just cancel
            if not self._check_kernel_space_rpm():
                return False
            '''
            if not self._check_user_space_rpm():
                return False

        return True

    def cannot_update_check(self):
        cmd = "yum update"
        return self.check_strs_in_cmd_output(
            cmd, ["No packages marked for update"], timeout=FABRIC_TIMEOUT)

    def cannot_install_check(self):
        cmd = "yum install {}".format(self._update_rpm_path)
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0] and "Nothing to do" in ret[1]:
            return True
        else:
            return False

    def cmds_check(self):
        ck01 = self._check_lvs()
        ck02 = self._check_findmnt()

        return ck01 and ck02

    def signed_check(self):
        cmd = "rpm -qa --qf '%{{name}}-%{{version}}-%{{release}}.%{{arch}} (%{{SIGPGP:pgpsig}})\n' | " \
            "grep -v 'Key ID' | " \
            "grep -v 'update-{}' | " \
            "wc -l".format(self.target_build.split('-host-')[-1])
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            return False
        if ret[1].strip() != '0':
            log.error("The result of signed check is %s, not 0", ret[1])
            return False

        return True

    def knl_space_rpm_check(self):
        if "-4.0-" in self.source_build:
            raise RuntimeError(
                "The source build is 4.0, no need to check kernel space rpm.")
        return self._check_kernel_space_rpm()

    def usr_space_rpm_check(self):
        if "-4.0-" in self.source_build:
            raise RuntimeError(
                "The source build is 4.0, no need to check user space rpm.")
        return self._check_user_space_rpm()

    def avc_denied_check(self):
        log.info("Start to check avc denied errors.")

        cmd = "grep 'avc:  denied' /var/log/audit/audit.log"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                'Check avc denied errors failed. The result of "%s" is %s',
                cmd, ret[1])
            return False

        if ret[1].strip(' ') != '':
            log.error("The result of avc denied check is %s, not null", ret[1])
            return False

        log.info("The result of '%s' is null", cmd)

        return True

    def iptables_status_check(self):
        ck01 = self._check_iptables_status()
        ck02 = self._check_firewalld_status()

        return ck01 and ck02

    def ntpd_status_check(self):
        return self._check_ntpd_status()

    def sysstat_check(self):
        return self._check_sysstat()

    def ovirt_imageio_daemon_check(self):
        return self._check_ovirt_imageio_daemon_status()

    def boot_dmesg_log_check(self):
        return self._check_boot_dmesg_log()

    def separate_volumes_check(self):
        return self._check_separate_volumes()

    def etc_var_file_update_check(self):
        ck01 = self.check_strs_in_file(
            self._add_file_name, [self._add_file_content],
            timeout=FABRIC_TIMEOUT)
        ck02 = self.check_strs_in_file(
            self._update_file_name, [self._update_file_content],
            timeout=FABRIC_TIMEOUT)
        ck03 = self.check_strs_in_file(
            self._add_var_file_name, [self._add_file_content],
            timeout=FABRIC_TIMEOUT)
        ck04 = self.check_strs_in_file(
            self._update_var_log_file_name, [self._update_file_content],
            timeout=FABRIC_TIMEOUT)

        return ck01 and ck02 and ck03 and ck04

    def reinstall_rpm_check(self):
        if "-4.0-" in self.source_build:
            return True

        return self._reinstall_rpms_check()

    def update_again_unavailable_check(self):
        log.info("Start to check update again unavailable.")
        if "-4.0-" in self.source_build:
            return True

        if not self._rhvm.check_update_available(self._host_name):
            log.info("Can not update rhvh again after upgrade.")
            return True
        else:
            log.info("Can update again, should be not!")
            return False

    def no_space_update_check(self):
        if "-4.0-" in self.source_build:
            raise RuntimeError(
                "The source build is 4.0, no need to check.")

        log.info("Start to check can not upgrade if no space left.")
        cmd = "yum update -y"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)

        if "Disk Requirements" in ret[1] or "No space left on device" in ret[1]:
            return True
        else:
            log.info('The output is %s', ret[1])
            log.error("Upgrade incorrect when no enough space left.")
            return False

    ## added by wujian, upgrade tier2 checks
    # 1-fips check
    def fips_check(self):
        return self.check_strs_in_file(
            '/proc/sys/crypto/fips_enabled', ['1'], timeout=300)

    # 2-check kdump.service =active
    def kdump_check(self):
        return self._check_kdump_status()

    # 3-remove vg/lv, delete old layer info on /etc/grub2.cfg
    def delete_imgbase_check(self):
        ck01 = self._change_grub_file()
        ck02 = self._remove_lv()
        if not ck01 or not ck02:
            log.error("Cannot remove vg/lv successfully.")
            return False

        log.info("Reboot into system.")

        ret = self._enter_system()
        if not ret[0]:
            return False

        ck03 = self._check_cockpit_connection()
        ck04 = self._check_host_status_on_rhvm()
        if not ck03 or not ck04:
            log.error("Failed to work system again after remove vg/lv.")

        log.info("System work normally.")
        return True

    # 4-Upgrade with bond network
    def bond_check(self):
        ck01 = self._bond_status()
        #ck02 = self.basic_upgrade_check()
        ck02 = self._check_imgbase_w()
        ck03 = self._check_imgbase_layout()
        ck04 = self._check_cockpit_connection()
        return ck01 and ck02 and ck03 and ck04



    ##########################################
    # upgrade process
    ##########################################
    def _add_update_files(self):
        log.info("Add and update files on host...")

        ret1 = self.run_cmd(
            "echo '{}' > {}".format(self._add_file_content,
                                    self._add_file_name),
            timeout=FABRIC_TIMEOUT)
        ret2 = self.run_cmd(
            "echo '{}' >> {}".format(self._update_file_content,
                                     self._update_file_name),
            timeout=FABRIC_TIMEOUT)
        ret3 = self.run_cmd(
            "echo '{}' > {}".format(self._add_file_content,
                                    self._add_var_file_name),
            timeout=FABRIC_TIMEOUT)
        ret4 = self.run_cmd(
            "echo '{}' >> {}".format(self._update_file_content,
                                     self._update_var_log_file_name),
            timeout=FABRIC_TIMEOUT)

        log.info("Add and update files on host finished.")
        return ret1[0] and ret2[0] and ret3[0] and ret4[0]

    def __install_kernel_space_rpm_via_curl(self):
        self._kernel_space_rpm = KERNEL_SPACE_RPM_URL.split('/')[-1]
        download_path = '/root/' + self._kernel_space_rpm

        log.info("Start to install kernel space rpm %s...",
                 self._kernel_space_rpm)

        # Download kernel space rpm:
        cmd = "curl --retry 20 --remote-time -o {} {}".format(
            download_path, KERNEL_SPACE_RPM_URL)
        ret = self.run_cmd(cmd, timeout=600)
        if not ret[0]:
            log.error("Download %s failed.", KERNEL_SPACE_RPM_URL)
            return False
        log.info("Download %s succeeded.", KERNEL_SPACE_RPM_URL)

        # Install kernel space rpm:
        cmd = "yum localinstall -y {} > /root/kernel_space_rpm_install.log".format(
            download_path)
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error(
                "Install kernel space rpm %s failed, see log /root/kernel_space_rpm_install.log",
                self._kernel_space_rpm)
            return False
        log.info("Install kernel space rpm %s succeeded.",
                 self._kernel_space_rpm)

        return True

    def _install_kernel_space_rpm_via_repo(self):
        self._kernel_space_rpm = "kmod-oracleasm"
        log.info("Start to install kernel space rpm %s...",
                 self._kernel_space_rpm)

        install_log = "/root/{}.log".format(self._kernel_space_rpm)
        cmd = "yum install -y {} > {}".format(self._kernel_space_rpm,
                                              install_log)
        ret = self.run_cmd(cmd, timeout=600)
        if not ret[0]:
            log.error("Install kernel space rpm %s failed, see log %s",
                      self._kernel_space_rpm, install_log)
        log.info("Install kernel space rpm %s succeeded.",
                 self._kernel_space_rpm)

        # Check kernel space rpm:
        ret = self._check_kernel_space_rpm()
        if not ret:
            log.error("Check kernel space rpm failed.")
        log.info("Check kernel space rpm succeeded.")

        return True

    def _install_user_space_rpm(self):
        log.info("Start to install user space rpm...")

        install_log = "/root/httpd.log"
        cmd = "yum install -y httpd > {}".format(install_log)
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Install user space rpm httpd failed. Please check %s.",
                      install_log)
            return False
        log.info("Install user space rpm httpd succeeded.")

        return self._check_user_space_rpm()

    def _install_rpms(self):
        if "-4.0-" in self.source_build:
            return True

        log.info("Start to install rpms...")
        if not self._put_repo_to_host(repo_file="rhel73.repo"):
            return False
        '''
        # the kernel rpm is incompatible with 7.4, just cancel the case
        if not self._install_kernel_space_rpm_via_repo():
            return False
        '''
        if not self._install_user_space_rpm():
            return False
        if not self._del_repo_on_host(repo_file="rhel73.repo"):
            return False

        return True

    def _fill_up_space(self):
        log.info("Start to fill up space...")

        cmd = "dd if=/dev/urandom of=/test.img bs=1M count=4200"
        ret = self.run_cmd(cmd, timeout=ENTER_SYSTEM_TIMEOUT)

        log.info("Already fill up space, %s...", ret[1])
        return True

    def _delete_rpms_repo_packages(self):
        if "-4.0-" in self.source_build:
            return True

        log.info("Start to delete rpms repo and package...")

        if not self._del_repo_on_host(repo_file="rhel73.repo"):
            return False

        return True

    def _get_update_rpm_name_from_http(self):
        ver = self.target_build.split("-host-")[-1]
        update_rpm_name = None
        try:
            r = requests.get(RHVH_UPDATE_RPM_URL, verify=False)
            if r.status_code == 200:
                for line in r.text.split('\n'):
                    if line.find(ver) >= 0:
                        update_rpm_name = line.split('"')[1].strip()
                        break
            else:
                log.error(r.text)
        except Exception as e:
            log.error(e)

        return update_rpm_name

    def _fetch_update_rpm_to_host(self):
        update_rpm_name = self._get_update_rpm_name_from_http()
        if not update_rpm_name:
            log.error("Can't get the update rpm name.")
            return False

        url = RHVH_UPDATE_RPM_URL + update_rpm_name
        self._update_rpm_path = '/root/' + update_rpm_name

        log.info("Fetch %s to %s", url, self._update_rpm_path)

        cmd = "curl --retry 20 --remote-time -o {} {}".format(
            self._update_rpm_path, url)
        ret = self.run_cmd(cmd, timeout=600)

        return ret[0]

    def _put_repo_to_host(self, repo_file="rhvh.repo"):
        log.info("Put repo file %s to host...", repo_file)

        local_path = os.path.join(KS_FILES_DIR, repo_file)
        remote_path = "/etc/yum.repos.d/"
        try:
            self.put_remote_file(local_path, remote_path)
        except Exception as e:
            log.error(e)
            return False

        log.info("Put repo file %s to host finished.", repo_file)
        return True

    def _del_repo_on_host(self, repo_file="rhvh.repo"):
        log.info("Delete repo fiel %s on host...", repo_file)

        repo_path = "/etc/yum.repos.d"
        cmd = "mv {repo_path}/{repo_file} {repo_path}/{repo_file}.bak".format(
            repo_path=repo_path, repo_file=repo_file)
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to delete repo file %s", repo_file)
            return False

        log.info("Delete repo file %s finished.", repo_file)
        return True

    def _mv_rpm_packages_on_host(self, packages_path = "/var/imgbased/persisted-rpms", packages_bak_path = "/var/rpms-bak", packages_files="*"):
        if "-4.0-" in self.source_build:
            return True

        log.info("mv rpm packages %s on host...", packages_files)

        cmd = "mkdir {packages_bak_path}".format(
            packages_bak_path=packages_bak_path)
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)

        cmd = "mv {packages_path}/{packages_files} {packages_bak_path}".format(
            packages_path=packages_path, packages_files=packages_files, packages_bak_path=packages_bak_path)
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to mv rpm packages file %s", packages_files)
            return False

        log.info("Mv rpm packages file %s finished.", packages_files)
        return True

    def _set_locale_on_host(self):
        log.info("Set host to a locale that uses commas for decimals...")

        cmd = "export LC_ALL=fr_FR"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to set host to a locale")
            return False

        log.info("Set host to a locale finished.")
        return True

    def _get_host_cpu_type(self):
        log.info("Get host cpu type...")
        cmd = 'lscpu | grep "Model name"'
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if ret[0]:
            if "AMD" in ret[1]:
                cpu_type = "AMD Opteron G1"
            elif "Intel" in ret[1]:
                cpu_type = "Intel Conroe Family"
            else:
                cpu_type = None
        else:
            cpu_type = None
        self._host_cpu_type = cpu_type
        log.info("Get host cpu type finished.")

    def _get_rhvm_fqdn(self):
        log.info("Get rhvm fqdn...")
        if '-4.0-' in self.source_build:
            key = "4.0_rhvm_fqdn"
        elif '-4.1-' in self.source_build:
            key = "4.1_rhvm_fqdn"
        else:
            log.error("The version of host src build is not 4.0 or 4.1")
            return
        self._rhvm_fqdn = RHVM_DATA_MAP.get(key)
        log.info("Get rhvm fqdn finished.")

    def _gen_name(self):
        log.info("Generate dc name, cluster name, host name...")
        mc_name = self.beaker_name.split('.')[0]
        # t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        # gen_name = mc_name + '-' + t
        gen_name = mc_name

        self._dc_name = gen_name
        self._cluster_name = gen_name
        self._host_name = gen_name

        log.info("Generate names finished.")

    def _get_host_ip(self, is_vlan):
        log.info("Get host ip...")

        if not is_vlan:
            self._host_ip = self.host_string
        else:
            cmd = "ip -f inet addr show | grep 'inet 192' | awk '{print $2}'| awk -F '/' '{print $1}'"
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            if not ret[0]:
                return
            self._host_ip = ret[1]

            # get vlan id:
            cmd = """grep VLAN_ID /etc/sysconfig/network-scripts/* | awk -F '=' '{print $2}' | awk -F '"' '{print $2}'"""
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            if not ret[0]:
                return
            self._host_vlanid = ret[1]

        log.info("Get host ip finished.")

    ## replaced by _check_add_10_route
    # def _add_10_route(self):
    #     target_ip = "10.0.0.0/8"
    #
    #     log.info("Start to add %s route on host...", target_ip)
    #
    #     cmd = "ip route | grep --color=never default | head -1"
    #     ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
    #     if not ret[0]:
    #         log.error("Get default pub route failed.")
    #         return False
    #     log.info('The default pub route is "%s"', ret[1])
    #
    #     gateway = ret[1].split()[2]
    #     nic = ret[1].split()[4]
    #
    #     cmd = "ip route add {target_ip} via {gateway} dev {nic}".format(
    #         target_ip=target_ip, gateway=gateway, nic=nic)
    #     ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
    #     if not ret[0]:
    #         log.error("Add %s to route table failed.", target_ip)
    #         return False
    #
    #     cmd = "echo '{target_ip} via {gateway}' > /etc/sysconfig/network-scripts/route-{nic}".format(
    #         target_ip=target_ip, gateway=gateway, nic=nic)
    #     ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
    #     if not ret[0]:
    #         log.error("Create route-%s file failed.", nic)
    #         return False
    #
    #     log.info("Add %s route on host finished.", target_ip)
    #     return True

    ## Add is_vlan value, if True, do _add_10_route
    def _check_add_10_route(self, is_vlan=False):
        if is_vlan == True:
            target_ip = "10.0.0.0/8"

            log.info("Start to add %s route on host...", target_ip)

            cmd = "ip route | grep --color=never default | head -1"
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            if not ret[0]:
                log.error("Get default pub route failed.")
                return False
            log.info('The default pub route is "%s"', ret[1])

            gateway = ret[1].split()[2]
            nic = ret[1].split()[4]

            cmd = "ip route add {target_ip} via {gateway} dev {nic}".format(
                target_ip=target_ip, gateway=gateway, nic=nic)
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            if not ret[0]:
                log.error("Add %s to route table failed.", target_ip)
                return False

            cmd = "echo '{target_ip} via {gateway}' > /etc/sysconfig/network-scripts/route-{nic}".format(
                target_ip=target_ip, gateway=gateway, nic=nic)
            ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
            if not ret[0]:
                log.error("Create route-%s file failed.", nic)
                return False

            log.info("Add %s route on host finished.", target_ip)
        else:
            log.info("Network is acttive without vlan.")

        return True


    def _del_vlan_route(self):
        log.info("Start to delete the default vlan route...")

        cmd = "ip route | grep --color=never default | grep ' 192.'"
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Get default vlan route failed.")
            return False
        log.info('The default vlan route is "%s"', ret[1])

        vlan_gateway = ret[1].split()[2]

        cmd = "ip route del default via {}".format(vlan_gateway)
        ret = self.run_cmd(cmd, timeout=FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Delete the default vlan route failed.")
            return False

        log.info("Delete the default vlan route finished.")
        return True

    def _add_host_to_rhvm(self, is_vlan=False):
        log.info("Add host to rhvm...")
        # get rhvm fqdn
        self._get_rhvm_fqdn()
        if not self._rhvm_fqdn:
            return False
        # generate data center name, cluster name, host name
        self._gen_name()
        # get host ip, vlanid
        self._get_host_ip(is_vlan)
        if not self._host_ip:
            return False
        if is_vlan and not self._host_vlanid:
            return False
        # get host cpu type
        self._get_host_cpu_type()
        if not self._host_cpu_type:
            return False

        log.info(
            "rhvm: %s, datacenter: %s, cluster_name: %s, host_name: %s, host_ip: %s, vlanid: %s, cpu_type: %s",
            self._rhvm_fqdn, self._dc_name, self._cluster_name,
            self._host_name, self._host_ip, self._host_vlanid,
            self._host_cpu_type)

        try:
            self._rhvm = RhevmAction(self._rhvm_fqdn)

            self._del_host_on_rhvm()

            log.info("Add datacenter %s", self._dc_name)
            self._rhvm.add_datacenter(self._dc_name)

            if is_vlan:
                # ifup bond0.50 and slaves, due to one bug 1475728 in rhvh 4.1 #
                cmd1 = "ifup p1p1"
                cmd2 = "ifup p1p2"
                cmd3 = "ifup bond0.50"
                ret1 = self.run_cmd(cmd1, timeout=FABRIC_TIMEOUT)
                ret2 = self.run_cmd(cmd2, timeout=FABRIC_TIMEOUT)
                ret3 = self.run_cmd(cmd3, timeout=FABRIC_TIMEOUT)

                cmd4 = "ip a s"
                ret4 = self.run_cmd(cmd4, timeout=FABRIC_TIMEOUT)
                log.info('The vlan ip info of "%s" is %s', cmd4, ret4[1])
                ## end ##

                log.info("Update network with vlan %s", self._host_vlanid)
                self._rhvm.update_network(self._dc_name, "vlan",
                                          self._host_vlanid)

            log.info("Add cluster %s", self._cluster_name)
            self._rhvm.add_cluster(self._dc_name, self._cluster_name,
                                   self._host_cpu_type)

            log.info("Add host %s", self._host_name)
            self._rhvm.add_host(self._host_ip, self._host_name, self.host_pass,
                                self._cluster_name)
        except Exception as e:
            log.error(e)
            return False

        log.info("Add host to rhvm finished.")
        return True

    def _del_host_on_rhvm(self):
        if not self._rhvm:
            return

        count = 0
        while (count < 3):
            try:
                if self._host_name:
                    log.info("Try to remove host %s", self._host_name)
                    self._rhvm.remove_host(self._host_name)
                    self._rhvm.del_host_events(self._host_name)

                if self._cluster_name:
                    log.info("Try to remove cluster %s", self._cluster_name)
                    self._rhvm.remove_cluster(self._cluster_name)

                if self._dc_name:
                    log.info("Try to remove data_center %s", self._dc_name)
                    self._rhvm.remove_datacenter(self._dc_name)
            except Exception as e:
                log.error(e)
                time.sleep(20)
                count = count + 1
            else:
                break

    def _check_host_status_on_rhvm(self):
        if not self._host_name:
            return True

        log.info("Check host status on rhvm.")

        count = 0
        while (count < CHK_HOST_ON_RHVM_STAT_MAXCOUNT):
            host = self._rhvm.list_host(key="name", value=self._host_name)
            if host and host.get('status') == 'up':
                break
            count = count + 1
            time.sleep(CHK_HOST_ON_RHVM_STAT_INTERVAL)
        else:
            log.error("Host is not up on rhvm.")
            return False
        log.info("Host is up on rhvm.")
        return True

    def _enter_system(self, flag="manual"):
        log.info("Reboot and log into system...")

        if flag == "manual":
            cmd = "systemctl reboot"
            self.run_cmd(cmd, timeout=10)

        disconnect_all()
        count = 0
        while (count < ENTER_SYSTEM_MAXCOUNT):
            time.sleep(ENTER_SYSTEM_INTERVAL)
            ret = self.run_cmd("imgbase w", timeout=ENTER_SYSTEM_TIMEOUT)
            if not ret[0]:
                count = count + 1
            else:
                break

        log.info("Reboot and log into system finished.")
        return ret

    def _yum_update(self):
        log.info(
            "Run yum update cmd, please wait...(you could check /root/yum_update.log on host)"
        )

        cmd = "yum -y update > /root/yum_update.log"
        ret = self.run_cmd(cmd, timeout=YUM_UPDATE_TIMEOUT)

        log.info("Run yum update cmd finished.")
        return ret[0]

    def _yum_install(self):
        log.info(
            "Run yum install cmd, please wait...(you could check /root/yum_install.log on host)"
        )

        cmd = "yum -y install {} > /root/yum_install.log".format(
            self._update_rpm_path)
        ret = self.run_cmd(cmd, timeout=YUM_INSTALL_TIMEOUT)

        log.info("Run yum install cmd finished.")
        return ret[0]

    def _rhvm_upgrade(self):
        log.info("Run rhvm upgrade, please wait...")

        try:
            self._rhvm.upgrade_host(self._host_name)
        except Exception as e:
            log.error(e)
            return False

        log.info("Run rhvm upgrade finished.")
        return True

    def _yum_update_process(self, is_vlan=False, is_bond=False):
        log.info("Start to upgrade rhvh via yum update cmd...")

        """
        #is_vlan=True will check if add 10.0.0.0/8 route
        #is_vlan=False will not check if add 10.0.0.0/8 route
        """
        """
        if not self._check_is_fips(is_fips=True):
            return False
        """
        if not self._is_bond_net(is_bond):
            return False
        if not self._check_add_10_route(is_vlan):
            return False

        if not self._add_update_files():
            return False
        if not self._put_repo_to_host():
            return False

        if not is_bond:
            if not self._add_host_to_rhvm(is_vlan):       ###add "is_vlan" value to activate vlan
                return False
            if not self._check_host_status_on_rhvm():
                return False

        if not self._check_cockpit_connection():
            return False
        if not self._install_rpms():
            #return False
            log.info("Install rpms maybe failed.")
        if not self._yum_update():
            return False
        if not self._enter_system()[0]:
            return False

        log.info("Upgrading rhvh via yum update cmd finished.")
        return True

    def _yum_install_process(self):
        log.info("Start to upgrade rhvh via yum install cmd...")

        if not self._fetch_update_rpm_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._install_rpms():
            return False
        if not self._mv_rpm_packages_on_host():
            return False
        if not self._set_locale_on_host():
            return False
        if not self._yum_install():
            return False
        if not self._enter_system()[0]:
            return False

        log.info("Upgrading rhvh via yum install finished.")
        return True

    def _rhvm_upgrade_process(self):
        log.info("Start to upgrade rhvh via rhvm...")

        #if not self._add_10_route():
        if not self._check_add_10_route(is_vlan=True):
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm(is_vlan=True):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False

        log.info("Upgrade rhvh via rhvm finished.")
        return True

    def _yum_update_lack_space_process(self):
        log.info("Start to upgrade rhvh via yum update when no enough space left...")

        if not self._add_update_files():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._fill_up_space():
            return False

        log.info("Fill up space before upgrading rhvh via yum update finished.")
        return True

    def _collect_infos(self, flag):
        log.info('Collect %s infos on host...', flag)

        self._check_infos[flag] = {}
        check_infos = self._check_infos[flag]

        cmdmap = {
            "imgbased_ver": "rpm -qa |grep --color=never imgbased",
            "update_ver": "rpm -qa |grep --color=never update",
            "imgbase_w": "imgbase w",
            "imgbase_layout": "imgbase layout",
            # "os_release": "cat /etc/os-release",
            "initiatorname_iscsi": "cat /etc/iscsi/initiatorname.iscsi",
            "lvs":
            # "lvs -a -o lv_name,vg_name,lv_size,pool_lv,origin --noheadings --separator ' '",
            "lvs -a -o lv_name,lv_size, --unit=m --noheadings --separator ' '",
            "findmnt": "findmnt -r -n",
            "bond_ip": "ip -f inet addr show | grep 'inet 10' | awk '{print $2}'|awk -F '/' '{print $1}'",
        }

        for k, v in cmdmap.items():
            ret = self.run_cmd(v, timeout=FABRIC_TIMEOUT)
            if ret[0]:
                check_infos[k] = ret[1]
                log.info("***%s***:\n%s", k, ret[1])
            else:
                return False

        log.info('Collect %s infos on host finished.', flag)
        return True

    def go_check(self):
        disconnect_all()
        cks = {}
        try:
            if not self._collect_infos('old'):
                raise RuntimeError("Failed to collect old infos.")

            if "yum_update" in self.ksfile:
                #ret = self._yum_update_process()
                if re.split(r'_|\.', self.ksfile)[3] == 'vlan':
                    ret = self._yum_update_process(is_vlan=True, is_bond=False)
                elif re.split(r'_|\.', self.ksfile)[3] == 'bond':
                    ret = self._yum_update_process(is_vlan=False, is_bond=True)
                else:
                    ret = self._yum_update_process(is_vlan=False, is_bond=False)
            elif "yum_install" in self.ksfile:
                ret = self._yum_install_process()
            elif "rhvm_upgrade" in self.ksfile:
                ret = self._rhvm_upgrade_process()
            elif "lack_space" in self.ksfile:
                ret = self._yum_update_lack_space_process()

            if not ret:
                raise RuntimeError("Failed to run upgrade.")

            if not self._collect_infos('new'):
                raise RuntimeError("Failed to collect new infos.")

            cks = self.run_cases()
        except Exception as e:
            log.error(e)
        finally:
            self._del_host_on_rhvm()
            return cks


def log_cfg_for_unit_test():
    from utils import ResultsAndLogs
    logs = ResultsAndLogs()
    logs.logger_name = "unit_test.log"
    logs.img_url = "upgrade/test"
    logs.get_actual_logger("upgrade")


if __name__ == '__main__':
    log_cfg_for_unit_test()
    log = logging.getLogger('bender')

    ck = CheckUpgrade()
    ck.host_string, ck.host_user, ck.host_pass = ('10.73.75.35', 'root',
                                                  'redhat')
    ck.source_build = 'redhat-virtualization-host-4.1-20170808.0'
    ck.target_build = 'redhat-virtualization-host-4.1-20171117.0'
    ck.beaker_name = DELL_PER510_01
    ck.ksfile = 'atu_rhvm_upgrade.ks'

    print ck.go_check()
