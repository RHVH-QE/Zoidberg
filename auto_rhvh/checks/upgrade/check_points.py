import logging
import os
import requests
import time
import re
import consts_upgrade as CONST
from ..helpers import CheckComm
from ..helpers.rhvm_api import RhevmAction


log = logging.getLogger('bender')

class CheckPoints(object):
    """"""

    def __init__(self):
        self._update_rpm_path = None
        self._check_infos = {}
        self._add_file_name = "/etc/upgrade_test"
        self._add_file_content = "test"
        self._update_file_name = "/etc/my.cnf"
        self._update_file_content = "# test"
        self._kernel_space_rpm = None
        self._user_space_rpms_set = None
        self._rhvm = None
        self._rhvm_fqdn = None
        self._dc_name = None
        self._cluster_name = None
        self._host_name = None
        self._default_gateway = None
        self._default_nic = None
        self._host_ip = None
        self._host_vlanid = None
        self._host_cpu_type = None
        self._source_build = None
        self._target_build = None
        self._host_string = None
        self._remotecmd = None
        self._beaker_name = None
        self._host_pass = None

    @property
    def remotecmd(self):
        return self._remotecmd

    @remotecmd.setter
    def remotecmd(self, val):
        self._remotecmd = val

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

    @property
    def host_string(self):
        return self._host_string

    @host_string.setter
    def host_string(self, val):
        self._host_string = val

    @property
    def beaker_name(self):
        return self._beaker_name

    @beaker_name.setter
    def beaker_name(self, val):
        self._beaker_name = val

    @property
    def host_pass(self):
        return self._host_pass

    @host_pass.setter
    def host_pass(self, val):
        self._host_pass = val

    ######################################################################
    # public methods used both by CheckPoints and UpgradeProcess
    ######################################################################
    def _check_host_status_on_rhvm(self):
        if not self._host_name:
            return True

        log.info("Check host status on rhvm.")

        count = 0
        while (count < CONST.CHK_HOST_ON_RHVM_STAT_MAXCOUNT):
            host = self._rhvm.list_host(key="name", value=self._host_name)
            if host and host.get('status') == 'up':
                break
            count = count + 1
            time.sleep(CONST.CHK_HOST_ON_RHVM_STAT_INTERVAL)
        else:
            log.error("Host is not up on rhvm.")
            return False
        log.info("Host is up on rhvm.")
        return True

    def _enter_system(self, flag="manual"):
        log.info("Reboot and log into system...")

        if flag == "manual":
            cmd = "systemctl reboot"
            self.remotecmd.run_cmd(cmd, timeout=10)

        self.remotecmd.disconnect()
        count = 0
        while (count < CONST.ENTER_SYSTEM_MAXCOUNT):
            time.sleep(CONST.ENTER_SYSTEM_INTERVAL)
            ret = self.remotecmd.run_cmd(
                "imgbase w", timeout=CONST.ENTER_SYSTEM_TIMEOUT)
            if not ret[0]:
                count = count + 1
            else:
                break

        log.info("Reboot and log into system finished.")
        return ret

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
            "findmnt": "findmnt -r -n"
        }

        for k, v in cmdmap.items():
            ret = self._remotecmd.run_cmd(v, timeout=CONST.FABRIC_TIMEOUT)
            if ret[0]:
                check_infos[k] = ret[1]
                log.info("***%s***:\n%s", k, ret[1])
            else:
                return False

        log.info('Collect %s infos on host finished.', flag)
        return True

    def _get_update_rpm_name_from_http(self):
        ver = self.target_build.split("-host-")[-1]
        update_rpm_name = None
        try:
            r = requests.get(CONST.RHVH_UPDATE_RPM_URL, verify=False)
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

        url = CONST.RHVH_UPDATE_RPM_URL + update_rpm_name
        self._update_rpm_path = '/root/' + update_rpm_name

        log.info("Fetch %s to %s", url, self._update_rpm_path)

        cmd = "curl --retry 20 --remote-time -o {} {}".format(
            self._update_rpm_path, url)
        ret = self._remotecmd.run_cmd(cmd, timeout=600)

        return ret[0]

    ##########################################
    # check methods of check points
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
        target_ver_num = self._target_build.split("-host-")[-1]

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
        if not CONST.CHECK_NEW_LVS:
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
        if CONST.CHECK_NEW_LVS:
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
        src_build_time = self._source_build.split('-')[-1].split('.')[0]
        tar_build_time = self._target_build.split('-')[-1].split('.')[0]

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
        ret = self.remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Get kernel version failed.")
            return False
        kernel_ver = ret[1]
        log.info("kernel version is %s", kernel_ver)

        # Check weak-updates:
        cmd = "ls /usr/lib/modules/{}/weak-updates/".format(kernel_ver)
        key = self._kernel_space_rpm.split('-')[1]
        ret = self.remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0] or key not in ret[1]:
            log.error('The result of "%s" is %s,  not include %s.', cmd,
                      ret[1], key)
            return False
        log.info('The result of "%s" is %s.', cmd, ret[1])

        # Check /var/imgbased/persisted-rpms
        cmd = "ls /var/imgbased/persisted-rpms"
        ret = self.remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0] or self._kernel_space_rpm not in ret[1]:
            log.error("The result of %s is %s, not include %s", cmd, ret[1],
                      self._kernel_space_rpm)
            return False
        log.info("The result of %s is %s", cmd, ret[1])

        return True

    def _check_user_space_rpm(self):
        log.info("Start to check user space rpm.")

        cmd = "rpm -qa | grep httpd"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
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

    ##########################################
    # check points
    ##########################################
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
        ck01 = self.remotecmd.check_strs_in_file(
            self._add_file_name, [self._add_file_content],
            timeout=CONST.FABRIC_TIMEOUT)
        ck02 = self.remotecmd.check_strs_in_file(
            self._update_file_name, [self._update_file_content],
            timeout=CONST.FABRIC_TIMEOUT)

        return ck01 and ck02

    def roll_back_check(self):
        log.info("Roll back.")

        cmd = "imgbase rollback"
        ret = self.remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            return False

        ret = self._enter_system()
        if not ret[0]:
            return False

        if ret[1] != self._check_infos.get("old").get("imgbase_w"):
            return False
        if not self._check_host_status_on_rhvm():
            return False

        if "-4.0-" not in self._source_build:
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
        return self.remotecmd.check_strs_in_cmd_output(
            cmd, ["No packages marked for update"], timeout=CONST.FABRIC_TIMEOUT)

    def cannot_install_check(self):
        update_rpm_name = self._get_update_rpm_name_from_http()
        self._update_rpm_path = '/root/' + update_rpm_name

        cmd = "yum install {}".format(self._update_rpm_path)
        ret = self.remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
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
            "wc -l".format(self._target_build.split('-host-')[-1])
        ret = self.remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            return False
        if ret[1].strip() != '0':
            log.error("The result of signed check is %s, not 0", ret[1])
            return False

        return True

    def knl_space_rpm_check(self):
        if "-4.0-" in self._source_build:
            raise RuntimeError(
                "The source build is 4.0, no need to check kernel space rpm.")
        return self._check_kernel_space_rpm()

    def usr_space_rpm_check(self):
        if "-4.0-" in self._source_build:
            raise RuntimeError(
                "The source build is 4.0, no need to check user space rpm.")
        return self._check_user_space_rpm()