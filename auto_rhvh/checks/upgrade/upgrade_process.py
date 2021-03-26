import logging
import requests
import os
import time
import re
import paramiko
from fabric.api import settings, run
import consts_upgrade as CONST
from ..helpers import CheckComm
from ..helpers.rhvm_api import RhevmAction
from check_points import CheckPoints

log = logging.getLogger('bender')


class UpgradeProcess(CheckPoints):

    ##########################################
    # upgrade process
    ##########################################
    def _add_update_files(self):
        log.info("Add and update files on host...")

        ret1 = self._remotecmd.run_cmd(
            "echo '{}' > {}".format(self._add_file_content,
                                    self._add_file_name),
            timeout=CONST.FABRIC_TIMEOUT)
        ret2 = self._remotecmd.run_cmd(
            "echo '{}' >> {}".format(self._update_file_content,
                                     self._update_file_name),
            timeout=CONST.FABRIC_TIMEOUT)
        ret3 = self._remotecmd.run_cmd(
            "echo '{}' > {}".format(self._add_file_content,
                                    self._add_var_file_name),
            timeout=CONST.FABRIC_TIMEOUT)
        ret4 = self._remotecmd.run_cmd(
            "echo '{}' >> {}".format(self._update_file_content,
                                     self._update_var_log_file_name),
            timeout=CONST.FABRIC_TIMEOUT)

        # RHEVM-27458
        ret5 = self._remotecmd.run_cmd(
            "mkdir /etc/upgrade_test_dir", timeout=CONST.FABRIC_TIMEOUT)
        time.sleep(3)
        ret6 = self._remotecmd.run_cmd(
            "echo '{}' > {}".format(self._add_dir_file_content,
             self._add_dir_file_name), timeout=CONST.FABRIC_TIMEOUT)

        log.info("Add and update files on host finished.")
        return ret1[0] and ret2[0] and ret3[0] and ret4[0]

    def __install_kernel_space_rpm_via_curl(self):
        self._kernel_space_rpm = CONST.KERNEL_SPACE_RPM_URL.split('/')[-1]
        download_path = '/root/' + self._kernel_space_rpm

        log.info("Start to install kernel space rpm %s...",
                 self._kernel_space_rpm)

        # Download kernel space rpm:
        cmd = "curl --retry 20 --remote-time -o {} {}".format(
            download_path, CONST.KERNEL_SPACE_RPM_URL)
        ret = self._remotecmd.run_cmd(cmd, timeout=600)
        if not ret[0]:
            log.error("Download %s failed.", CONST.KERNEL_SPACE_RPM_URL)
            return False
        log.info("Download %s succeeded.", CONST.KERNEL_SPACE_RPM_URL)

        # Install kernel space rpm:
        cmd = "yum localinstall -y {} > /root/kernel_space_rpm_install.log".format(
            download_path)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
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
        ret = self._remotecmd.run_cmd(cmd, timeout=600)
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

    def _install_rpms(self):
        if "-4.0-" in self._source_build:
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

    def _del_repo_on_host(self, repo_file="rhvh.repo"):
        log.info("Delete repo fiel %s on host...", repo_file)

        repo_path = "/etc/yum.repos.d"
        cmd = "mv {repo_path}/{repo_file} {repo_path}/{repo_file}.bak".format(
            repo_path=repo_path, repo_file=repo_file)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to delete repo file %s", repo_file)
            return False

        log.info("Delete repo file %s finished.", repo_file)
        return True

    def _install_userspace_svc_node_exporter(self):
        if "-4.0-" in self._source_build:
            return True

        log.info("Start to install userspace service node_exporter...")
        install_svc_log = "/root/node_exporter.log"

        #setup the node_exporter repo
        cmd_setRepo = "curl -s https://packagecloud.io/install/repositories/prometheus-rpm/release/script.rpm.sh | sudo bash > {}".format(install_svc_log)
        ret_setRepo = self._remotecmd.run_cmd(cmd_setRepo, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_setRepo[0]:
            log.error("Setup node_exporter repo failed. Please check %s.", install_svc_log)
            return False

        #install the node_exporter service
        cmd_install = "yum install -y node_exporter >> {}".format(install_svc_log)
        ret_install = self._remotecmd.run_cmd(cmd_install, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_install[0]:
            log.error("Install userspace service node_exporter failed. Please check %s.", install_svc_log)
            return False

        log.info("Install userspace service node_exporter succeeded.")

        #start the node_exporter service
        cmd_start = "systemctl start node_exporter"
        ret_start = self._remotecmd.run_cmd(cmd_start, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_start[0]:
            log.error(
                'Start userspace service node_exporter failed. The result of "%s" is "%s"',
                cmd_start, ret_start[1])
            return False
        log.info('The result of "%s" is %s', cmd_start, ret_start[1])

        #check the node_exporter service status 
        cmd_status = "systemctl status node_exporter | grep active"
        ret_status = self._remotecmd.run_cmd(cmd_status, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_status[0] or "active (running)" not in ret_status[1]:
            log.error('Check node_exporter status failed. The result of "%s" is "%s"', cmd_status, ret_status[1])
            return False
        log.info('The result of "%s" is %s', cmd_status, ret_status[1])

        #delete the node_exporter repo
        if not self._del_repo_on_host(repo_file="prometheus-rpm_release.repo"):
            return False

        return True

    def _install_two_versions_of_svc(self):
        log.info("Start to install userspace service vdsm-hook-nestedvt...")

        install_svc_log = "/root/vdsm_hook_nestedvt.log"
        url_35 = CONST.USER_RPMS.get("download_url_35")
        url_39 = CONST.USER_RPMS.get("download_url_39")
        rpm_name_35 = CONST.USER_RPMS.get("rpm_name_35")
        rpm_name_39 = CONST.USER_RPMS.get("rpm_name_39")

        cmd_download1 = "curl -o {rpm_name_35} {url_35}".format(rpm_name_35=rpm_name_35, url_35=url_35)
        cmd_download2 = "curl -o {rpm_name_39} {url_39}".format(rpm_name_39=rpm_name_39, url_39=url_39)

        ret_download = self._remotecmd.run_cmd(cmd_download1, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_download[0]:
            log.error("Download rpm failed. Please check %s.", install_svc_log)
            return False

        ret_download = self._remotecmd.run_cmd(cmd_download2, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_download[0]:
            log.error("Download rpm failed. Please check %s.", install_svc_log)
            return False
        
        #install the rpms
        cmd_install = "yum install -y {rpm_name_35} >> {install_svc_log}".format(rpm_name_35=rpm_name_35, install_svc_log=install_svc_log)
        ret_install = self._remotecmd.run_cmd(cmd_install, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_install[0]:
            log.error("Install vdsm-hook-nestedvt failed. Please check %s.", install_svc_log)
            return False
        log.info("Install vdsm-hook-nestedvt succeeded.")

        cmd_install = "yum install -y {rpm_name_39} >> {install_svc_log}".format(rpm_name_39=rpm_name_39, install_svc_log=install_svc_log)
        ret_install = self._remotecmd.run_cmd(cmd_install, timeout=CONST.FABRIC_TIMEOUT)
        if not ret_install[0]:
            log.error("Install vdsm-hook-nestedvt failed. Please check %s.", install_svc_log)
            return False
        log.info("Install vdsm-hook-nestedvt succeeded.")

        #check 
        cmd_check = "ls /var/imgbased/persisted-rpms/"
        ret_check = self._remotecmd.run_cmd(cmd_check, timeout=CONST.FABRIC_TIMEOUT)
        
        if ret_check[0] and rpm_name_35 in ret_check[1] and rpm_name_39 in ret_check[1]:
            log.info("The rpms are found in /var/imgbased/persisted-rpms/.")
            return True
        else:
            log.error(
                'Persiste userspace service failed. The result of "%s" is "%s"',
                cmd_check, ret_check[1])
            return False

    
    def _config_lvm_filter(self):
        log.info("Start to config lvm filter...")
        
        #setup the LVM filter
        cmd_conf_filter = "vdsm-tool config-lvm-filter"
        ret_conf_filter = self._remotecmd.run_cmd(cmd_conf_filter, timeout=CONST.FABRIC_TIMEOUT)
        
        if ret_conf_filter[0]:
            if "Configure LVM filter? [yes,NO]" in ret_conf_filter[1]:
                cmd_confirm = "yes"
                ret_confirm = self._remotecmd.run_cmd(cmd_confirm, timeout=CONST.FABRIC_TIMEOUT)

                if ret_confirm[0] and "Please reboot to verify the LVM configuration" in ret_confirm[1]:
                    log.info("Setup lvm filter successful. Will reboot the system.")
                    return True
                else:
                    log.error("The result of command: %s is: %s", cmd_confirm, ret_confirm[1])
                    return False
                
            if "LVM filter is already configured for Vdsm" in ret_conf_filter[1]:
                log.info("LVM filter is configed. Will reboot the system.")
                return True
        else:
            log.error("Setup lvm filter failed. The result of command: %s is: %s", cmd_conf_filter, ret_conf_filter[1])
            return False
    
    def _set_locale_on_host(self):
        log.info("Set host to a locale that uses commas for decimals...")

        cmd = "export LC_ALL=fr_FR"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to set host to a locale")
            return False

        log.info("Set host to a locale finished.")
        return True

    def _remove_audit_log(self):
        log.info("Remove audit log for checking avc denied errors after upgrade.")

        cmd = "test -e {name} && mv {name} {name}.bak".format(
            name="/var/log/audit/audit.log")
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to remove audit log.")
            return False

        log.info("Remove audit log finished.")
        return True

    def _get_host_cpu_type(self):
        log.info("Get host cpu type...")
        cmd = 'lscpu | grep "Model name"'
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if ret[0]:
            if "AMD EPYC" in ret[1]:
                cpu_type = "AMD EPYC"
            elif "AMD" in ret[1]:
                cpu_type = "AMD Opteron G5"
            elif "Intel" in ret[1]:
                cpu_type = "Intel Nehalem Family"
            else:
                cpu_type = None
        else:
            cpu_type = None
        self._host_cpu_type = cpu_type
        log.info("Get host cpu type finished.")

    def _get_rhvm_fqdn(self):
        log.info("Get rhvm fqdn...")
        if '-4.0-' in self._source_build:
            key = "4.0_rhvm_fqdn"
        elif '-4.1-' in self._source_build:
            key = "4.1_rhvm_fqdn"
        elif '-4.2-' in self._source_build:
            key = "4.2_rhvm_fqdn"
        elif '-4.4.' in self._source_build:
            key = "4.4_rhvm_fqdn"
        else:
            log.error("The version of host src build is not 4.0 or 4.1 or 4.2 or 4.4.x")
            return
        self._rhvm_fqdn = CONST.RHVM_DATA_MAP.get(key)
        log.info("Get rhvm fqdn finished.")

    def _gen_name(self):
        log.info("Generate dc name, cluster name, host name, storage domain name, VMs name...")
        mc_name = self._beaker_name.split('.')[0]
        # t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        # gen_name = mc_name + '-' + t
        gen_name = mc_name

        self._dc_name = gen_name
        self._cluster_name = gen_name
        self._host_name = gen_name
        self._sd_name = gen_name
        self._vm_name = gen_name

        log.info("Generate names finished.")

    def _get_nfs_info(self):
        log.info("Getting NFS storage informations...")

        self._nfs_ip = CONST.NFS_INFO.get("ip")
        self._nfs_pass = CONST.NFS_INFO.get("password")
        self._nfs_data_path = CONST.NFS_INFO.get("data_path")
        log.info("Getting NFS finished.")
    
    def _get_disk_size(self):
        log.info("Getting disk size...")
        self._disk_size = CONST.DISK_INFO.get("size")
        log.info("Getting disk size finished.")

    def _get_host_ip(self, is_vlan, is_bond):
        log.info("Get host ip...")

        if is_bond:
            # print network info
            cmd_ip = "ip a s"
            ret_ip = self._remotecmd.run_cmd(cmd_ip, timeout=CONST.FABRIC_TIMEOUT)
            log.info('The bond ip info of "%s" is %s', cmd_ip, ret_ip[1])

            # get bond ip
            cmd = "ip a s | grep -A 5 bond0: | grep 'inet 10.' | awk '{print $2}' | awk -F '/' '{print $1}'"
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                return
            self._host_ip = ret[1]
            log.info("The host ip is: %s", self._host_ip)
            
        ''' if not is_vlan:
            self._host_ip = self._host_string
        else: '''

        if is_vlan:
            # ifup p1p1.50, bond0.50 and slaves, due to one bug 1475728 in rhvh 4.1 #
            cmd1 = "nmcli connection up id enp6s0f0" #"ifup p1p1"
            cmd2 = "nmcli connection up id enp6s0f0.50" #"ifup p1p1.50"
            cmd3 = "nmcli connection up id enp6s0f1" #"ifup p1p2"
            
            vlan_name="bond0.50"
            if '-4.4.0' in self._source_build or '-4.4.1' in self._source_build:
                vlan_name = "VLAN connection bond0.50"
            cmd4 = "nmcli connection up id '{vlan_name}'".format(vlan_name=vlan_name) #"ifup bond0.50"
            
            ret1 = self._remotecmd.run_cmd(cmd1, timeout=CONST.FABRIC_TIMEOUT)
            ret2 = self._remotecmd.run_cmd(cmd2, timeout=CONST.FABRIC_TIMEOUT)
            ret3 = self._remotecmd.run_cmd(cmd3, timeout=CONST.FABRIC_TIMEOUT)
            ret4 = self._remotecmd.run_cmd(cmd4, timeout=CONST.FABRIC_TIMEOUT)
            time.sleep(3)

            cmd5 = "ip a s"
            ret5 = self._remotecmd.run_cmd(cmd5, timeout=CONST.FABRIC_TIMEOUT)
            log.info('The vlan ip info of "%s" is %s', cmd5, ret5[1])
            ## end ##

            cmd = "ip -f inet addr show | grep 'inet 192.168.50' | awk '{print $2}'| awk -F '/' '{print $1}'"
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                return
            self._host_ip = ret[1]
            log.info("The host ip is: %s", self._host_ip)

            # get vlan id:
            #cmd = """grep VLAN_ID /etc/sysconfig/network-scripts/* | awk -F '=' '{print $2}' | awk -F '"' '{print $2}'"""
            cmd = "grep VLAN_ID /etc/sysconfig/network-scripts/* | awk -F '=' '{print $2}'"
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                return
            self._host_vlanid = ret[1]
            log.info("The vlan id is: %s", self._host_vlanid)
            
        if not is_vlan and not is_bond:
            self._host_ip = self._host_string
            log.info("The host ip is: %s", self._host_ip)

        log.info("Get host ip finished.")

    def _add_10_route(self):
        target_ip = "10.0.0.0/8"

        log.info("Start to add %s route on host...", target_ip)

        cmd = "ip route | grep --color=never default | head -1"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Get default pub route failed.")
            return False
        log.info('The default pub route is "%s"', ret[1])

        gateway = ret[1].split()[2]
        nic = ret[1].split()[4]

        cmd = "ip route add {target_ip} via {gateway} dev {nic}".format(
            target_ip=target_ip, gateway=gateway, nic=nic)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Add %s to route table failed.", target_ip)
            return False

        cmd = "echo '{target_ip} via {gateway}' > /etc/sysconfig/network-scripts/route-{nic}".format(
            target_ip=target_ip, gateway=gateway, nic=nic)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Create route-%s file failed.", nic)
            return False

        log.info("Add %s route on host finished.", target_ip)
        return True

    def _setup_vlan_over_bond(self):
        
        cmd = "nmcli connection add type bond con-name bond0 ifname bond0 bond.options 'mode=active-backup'"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Create bond failed.")
            return False
        time.sleep(3)

        cmd = "nmcli connection modify bond0 ipv4.method disabled"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Set IPv4 mode of bond failed.")
            return False
        time.sleep(1)

        cmd = "nmcli connection modify bond0 ipv6.method ignore"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Set IPv6 of bond failed.")
            return False
        time.sleep(1)

        cmd = "nmcli connection add type ethernet slave-type bond con-name bond0-port1 ifname enp2s0f0 master bond0"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Add enp2s0f0 to bond failed.")
            return False
        time.sleep(5)

        cmd = "nmcli connection add type ethernet slave-type bond con-name bond0-port1 ifname enp2s0f1 master bond0"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Add enp2s0f1 to bond failed.")
            return False
        time.sleep(5)

        cmd = "nmcli connection up bond0"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Up bond0 failed.")
            return False
        time.sleep(3)

        cmd = "nmcli connection add type vlan con-name bond0.50 ifname bond0.50 vlan.parent bond0 vlan.id 50"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Add vlan over bond failed.")
            return False
        time.sleep(3)

        cmd = "nmcli connection up bond0.50"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Up bond0.50 failed.")
            return False
        time.sleep(3)

        log.info('Add vlan over bond successful.')
        return True

    def _change_vlan_route_metric(self):
        
        log.info("Start to change default vlan route metric on host...")

        cmd = "ip route | grep --color=never default | grep bond0.50 | head -1"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Get default vlan route failed.")
            return False
        log.info('The default vlan route is "%s"', ret[1])

        default_vlan_route = ret[1]
        #gateway = ret[1].split()[2]
        nic = ret[1].split()[4]
        str_before_metric = ret[1].split("metric")[0]
        new_vlan_route = str_before_metric + "metric 100"
        
        #delete the default vlan route
        cmd = "ip route del {vlan_route} ".format(vlan_route=default_vlan_route)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Delete default vlan route %s failed.", default_vlan_route)
            return False

        #add a new vlan route, only the metric is different from default vlan route
        cmd = "ip route add {new_vlan_route}".format(new_vlan_route=new_vlan_route)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Add vlan route %s failed.", cmd)
            return False

        #create route file
        cmd = "echo '{new_vlan_route}' > /etc/sysconfig/network-scripts/route-{nic}".format(new_vlan_route=new_vlan_route, nic=nic)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Create route-%s file failed.", nic)
            return False

        log.info("Add %s vlan route on host finished.", new_vlan_route)
        return True
    
    def _del_vlan_route(self):
        log.info("Start to delete the default vlan route...")

        cmd = "ip route | grep --color=never default | grep ' 192.'"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Get default vlan route failed.")
            return False
        log.info('The default vlan route is "%s"', ret[1])

        vlan_gateway = ret[1].split()[2]

        cmd = "ip route del default via {}".format(vlan_gateway)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Delete the default vlan route failed.")
            return False

        log.info("Delete the default vlan route finished.")
        return True

    def _add_host_route_for_rhvm(self):
        log.info("Start to add host route from rhvm to host...")
        
        # get rhvh fqdn
        self._get_rhvm_fqdn()
        if not self._rhvm_fqdn:
            return False
        fqdn = self._rhvm_fqdn

        # get rhvm's ip
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(fqdn, username="root", port=22, password="redhat")
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
            "ip -f inet addr show | grep 'inet 10.' | awk '{print $2}'| awk -F '/' '{print $1}'")

        rhvm_ip = ssh_stdout.read()
        rhvm_ip = rhvm_ip.strip().replace('\n', '').replace('\r', '').strip()
        log.info("The IP of rhvm is %s", rhvm_ip)
        ssh.close()

        # get the default pubilc route and the gaetway of host
        cmd = "ip route | grep --color=never default | head -1"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Get default pub route failed.")
            return False
        log.info('The default pub route is "%s"', ret[1])
        host_gateway = ret[1].split()[2]

        # add host route for rhvm
        cmd = "ip route add {rhvm_ip} via {host_gateway} dev bond0".format(rhvm_ip=rhvm_ip, host_gateway=host_gateway)
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Add %s to route table failed.", rhvm_ip)
            return False
        time.sleep(10)

        cmd = "ip route"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Add %s to route table failed.", rhvm_ip)
            return False
        log.info("The result of %s is %s", cmd, ret)
        time.sleep(10)

        log.info("Add rhvm %s host route finished.", rhvm_ip)

        return True
    
    def _add_host_route_for_repo(self):
        log.info("Start to add host route for the repo...")

        # get the gateway in public route
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self._host_ip, username="root", port=22, password="redhat")
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ip route | grep --color=never default | head -1")

        gateway = ssh_stdout.read()
        host_gateway = gateway.split()[2]
        log.info("The gateway of host is %s", host_gateway)
        time.sleep(10)

        # add host route for the repo
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
            "ip route add 10.66.10.22 via {host_gateway} dev ovirtmgmt".format(host_gateway=host_gateway))
        time.sleep(10)
        
        # check ip route after adding the host route
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ip route")
        route = ssh_stdout.read()
        log.info("After adding host route, the route is: %s", route)

        # close the ssh connection
        ssh.close()

        log.info("Add host route for repo %s finished.", "10.66.10.22")
        return True
    
    def _add_host_to_rhvm(self, is_vlan=False, is_bond=False, is_local=False):
        log.info("Add host to rhvm...")
        # get rhvm fqdn
        self._get_rhvm_fqdn()
        if not self._rhvm_fqdn:
            return False
        # generate data center name, cluster name, host name
        self._gen_name()
        # get host ip, vlanid
        self._get_host_ip(is_vlan, is_bond)
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
            if is_local:
                self._rhvm.add_datacenter(self._dc_name, is_local=True)
            else:
                self._rhvm.add_datacenter(self._dc_name)

            if is_vlan:
                log.info("Update network with vlan %s", self._host_vlanid)
                self._rhvm.update_network(self._dc_name, "vlan",
                                          self._host_vlanid)

            log.info("Add cluster %s", self._cluster_name)
            self._rhvm.add_cluster(self._dc_name, self._cluster_name,
                                   self._host_cpu_type)

            log.info("Add host %s", self._host_name)
            self._rhvm.add_host(self._host_ip, self._host_name, self._host_pass,
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
                    host = self._rhvm.list_host(key="name", value=self._host_name)
                    if host and (host.get('status') == 'up'): #or host.get('status') == 'non_operational'
                        log.info("Try to maintenance host %s", self._host_name)
                        self._rhvm.deactive_host(self._host_name)
                        time.sleep(10)

                existing_sd = self._rhvm.list_storage_domain(self._sd_name)
                if self._sd_name and existing_sd:
                    log.info("Try to remove storage domain %s", self._sd_name)
                    self._destory_sd_after_test(self._sd_name, self._host_name)

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

    def _yum_upgrade(self, yum_cmd):
        # Should deactive host on rhvm before upgrade
        self._rhvm.deactive_host(self._host_name)

        if yum_cmd == 'update':
            cmd = "yum -y update > /root/yum_upgrade.log"
        elif yum_cmd == 'install':
            cmd = "yum -y install {} > /root/yum_upgrade.log".format(
                self._update_rpm_path)
        else:
            log.error(
                "yum cmd is {} not in [update, install]!".format(yum_cmd))
            return False

        log.info(
            "Run yum {} cmd, please wait...(you could check /root/yum_upgrade.log on host)".format(
                yum_cmd)
        )
        result = True
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.YUM_INSTALL_TIMEOUT)
        if not ret[0]:
            result = False
        else:
            ret = self._remotecmd.run_cmd(
                "cat /root/yum_upgrade.log", timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                result = False
            else:
                if re.search('failed', ret[1], re.IGNORECASE):
                    result = False

        log.info("Run yum {} cmd finished.".format(yum_cmd))

        #TODO: should active host after upgrade
        #But there is no activate API in rhvm_api
        return result

    def _active_host(self):
        log.info("Active host, please wait...")
        try:
            self._rhvm.active_host(self._host_name)
        except Exception as e:
            log.error(e)
            return False

        log.info("Active host finished.")
        return True
    
    def _deactive_rollback_active(self):
        # deactive the host
        log.info("Maintain the host, then rollback.")
        self._rhvm.deactive_host(self._host_name)

        # rollback and reboot the host
        cmd = "imgbase rollback"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            return False

        ret = self._enter_system()
        if not ret[0]:
            return False

        # active the host
        log.info("Active the host after rollback.")
        if not self._active_host():
            return False

        return True
    
    def _rhvm_upgrade(self):
        log.info("Run rhvm upgrade, please wait...")

        try:
            self._rhvm.upgrade_host(self._host_name)
        except Exception as e:
            log.error(e)
            return False

        log.info("Run rhvm upgrade finished.")
        return True

    def _fill_up_space(self):
        log.info("Start to fill up space...")

        cmd = "dd if=/dev/urandom of=/test.img bs=1M count=4200"
        ret = self._remotecmd.run_cmd(cmd, timeout=5*CONST.ENTER_SYSTEM_TIMEOUT)

        log.info("Already fill up space, %s...", ret[1])
        return True

    def upload_upgrade_log(self, local_path):
        cmd = "mount | grep 'var_log ' || " \
            "mount /dev/mapper/`ls -al /dev/mapper | grep -e 'var_log '| awk '{print $9}'` /var/log"
        self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        try:
            self._remotecmd.get_remote_file(
                "/var/log/imgbased.log", local_path)
        except ValueError:
            pass

    #Create VM related functions
    #peyu 2020-07-31
    #Add nfs storage
    def _clean_nfs_path(self, nfs_ip, nfs_pass, nfs_data_path):
        log.info("Cleaning the nfs path")
        cmd = "rm -rf %s/*" % nfs_data_path
        with settings(
            warn_only=True,
            host_string='root@' + nfs_ip,
            password=nfs_pass):
            ret = run(cmd)
        if ret.failed:
            raise RuntimeError("Failed to cleanup the nfs path %s" % nfs_data_path)

    def _create_nfs_sd(self, sd_name, sd_type, nfs_ip, nfs_data_path, host_name):
        log.info("Creating the nfs storage domain %s" % sd_name)
        self._rhvm.add_plain_storage_domain(
            domain_name=sd_name,
            domain_type=sd_type,
            storage_type='nfs',
            storage_addr=nfs_ip,
            storage_path=nfs_data_path,
            host=host_name)
        time.sleep(60)

    def _attach_sd_to_dc(self, sd_name, dc_name):
        log.info("Attaching the storage domain %s to Data Centers %s" % (sd_name, dc_name))
        self._rhvm.attach_sd_to_datacenter(sd_name=sd_name, dc_name=dc_name)
        time.sleep(30)
        return True
    
    def _destory_sd_after_test(self, sd_name, host_name):
        log.info("Destorying the storage domain %s to host %s" % (sd_name, host_name))
        try:
            self._rhvm.remove_storage_domain(sd_name, host_name, destroy=True)
            time.sleep(30)
        except Exception as e:
            log.exception(e)
            return False            
        return True
    
    def _create_nfs_storage_domain(self):
        log.info("Creating nfs storage domain and attach it to Data Centers...")
        
        try:
            host_name = self._host_name
            sd_name = self._sd_name
            sd_type = 'data'
            dc_name = self._dc_name

            # Get nfs infomations
            self._get_nfs_info()

            # Clean the nfs path
            nfs_ip = self._nfs_ip
            nfs_passwd = self._nfs_pass
            nfs_data_path = self._nfs_data_path
            self._clean_nfs_path(nfs_ip, nfs_passwd, nfs_data_path)

            # Create the nfs storage domain
            self._create_nfs_sd(sd_name, sd_type, nfs_ip, nfs_data_path, host_name)

            # Attach the sd to datacenter
            self._attach_sd_to_dc(sd_name, dc_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    def _create_local_data_path(self, data_path, mount):
        log.info("Creating the local data path")
        cmd = "test -r %s" % data_path
        ret = self._remotecmd.run_cmd(cmd)
        if not ret[0]:
            cmd = "mkdir -p %s" % data_path
            self._remotecmd.run_cmd(cmd)
        else:
            cmd = "rm -rf %s/*" % data_path
            self._remotecmd.run_cmd(cmd)
        cmd = "chmod 0755 %s" % data_path
        ret = self._remotecmd.run_cmd(cmd)
        if not ret[0]:
            raise RuntimeError("Faile to chmod %s" % data_path)
        cmd = "chown 36:36 %s" % data_path
        ret = self._remotecmd.run_cmd(cmd)
        if not ret[0]:
            raise RuntimeError("Faile to chown %s" % data_path)

        if mount:
            # get Volume group name
            cmd_lvs = "lvs | grep home"
            ret_lvs = self._remotecmd.run_cmd(cmd_lvs, timeout=CONST.FABRIC_TIMEOUT)
            if not ret_lvs[0]:
                log.error("Failed to get logic volume.")
                return False
            vg_name = ret_lvs[1].split()[1]
            pool_name = ret_lvs[1].split()[4]
            mount_name = vg_name + "-data"
            if "-" in vg_name:
                mount_name = vg_name.replace("-","--") + "-data"

            # create lv
            # the parameter -y should be add
            cmd = "lvcreate -y -L 25G {vg_name} -n data".format(vg_name=vg_name)
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                raise RuntimeError("Faile to create lv. The result is '%s'" % ret[1])
            
            cmd = "mkfs.ext4 /dev/mapper/{mount_name}".format(mount_name=mount_name)
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                raise RuntimeError("Faile to make file system. The result is '%s'" % ret[1])
            
            cmd = "echo '/dev/mapper/{mount_name} {data_path} ext4 defaults,discard 1 2' >> /etc/fstab".format(mount_name=mount_name, data_path=data_path)
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                raise RuntimeError("Faile to modify fstab. The result is '%s'" % ret[1])
            
            cmd = "mount {data_path}".format(data_path=data_path)
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                raise RuntimeError("Faile to mount. The result is '%s'" % ret[1])
            
            cmd = "mount -a"
            ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
            if not ret[0]:
                raise RuntimeError("Faile to run mount -a. The result is '%s'" % ret[1])
            
            cmd = "chown 36:36 %s" % data_path
            ret = self._remotecmd.run_cmd(cmd)
            if not ret[0]:
                raise RuntimeError("Faile to chown %s" % data_path)
            cmd = "chmod 0755 %s" % data_path
            ret = self._remotecmd.run_cmd(cmd)
            if not ret[0]:
                raise RuntimeError("Faile to chmod %s" % data_path)

    def _add_local_storage_domain(self, sd_name, data_path, host_name):
        log.info("Creating the local storage domain")
        self._rhvm.add_plain_storage_domain(
            domain_name=sd_name,
            domain_type='data',
            storage_type='localfs',
            storage_addr='',
            storage_path=data_path,
            host=host_name)
        time.sleep(60)

    def _create_local_storage_domain(self, mount=False):
        log.info("Create local storage domain and attach it...")
        try:
            host_name = self._host_name
            sd_name = self._sd_name
            dc_name = self._dc_name
            
            # Create local data directory
            data_path = CONST.LOCAL_STORAGE_INFO.get("local_data_path")
            self._create_local_data_path(data_path, mount)

            # Create local storage domain
            self._add_local_storage_domain(sd_name, data_path, host_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    #peyu 2020-07-31
    #Create VMs, attach disk to VMs
    def _create_vm(self, vm_name, cluster_name):
        log.info("Creating VM %s", vm_name)
        self._rhvm.create_vm(vm_name=vm_name, cluster_name=cluster_name)
        time.sleep(30)

    #Create a float disk for vm using
    def _create_float_disk(self, disk_name):
        log.info("Creating a float disk for VM")
        
        disk_type = "nfs"
        sd_name = self._sd_name

        if disk_type == "localfs" or disk_type == "nfs":
            disk_size = self._disk_size
            self._rhvm.create_float_image_disk(sd_name, disk_name, disk_size)
        
        time.sleep(60)

    def _attach_disk_to_vm(self, vm_name, disk_name):
        log.info("Attaching the float disk to VM %s", vm_name)
        bootable = True
        self._rhvm.attach_disk_to_vm(disk_name, vm_name, bootable=bootable)
        time.sleep(30)

    def _create_vms_with_disk(self,vm_quantity=1):
        log.info("Creating VMs with disk...")
        try:
            cluster_name = self._cluster_name

            value = 1
            while value <= vm_quantity:
                vm_name = self._vm_name + '_vm' + str(value)
                disk_name = vm_name + '_Disk1'
                
                # Create the vm
                self._create_vm(vm_name, cluster_name)
                
                # Get disk info
                self._get_disk_size()

                # Create the float disk
                self._create_float_disk(disk_name)

                # Attach the disk to vm
                self._attach_disk_to_vm(vm_name, disk_name)

                value += 1

        except Exception as e:
            log.exception(e)
            return False
        return True

    #peyu 2020-07-31
    #Operations on VM
    def _wait_vm_status(self, vm_name, expect_status):
        log.info("Waitting the VM to status %s" % expect_status)
        i = 0
        vm_status = "unknown"
        while True:
            if i > 30:
                log.error("VM status is %s, not %s" % (vm_status, expect_status))
                return False
            vm_status = self._rhvm.list_vm(vm_name)['status']
            log.info("The VM status is: %s" % vm_status)
            if vm_status == expect_status:
                return True
            time.sleep(10)
            i += 1

    def _start_vm(self, vm_name):
        log.info("Start up the VM %s" % vm_name)

        try:
            self._rhvm.operate_vm(vm_name, 'start')
            time.sleep(60)

            # Wait the vm is up
            self._wait_vm_status(vm_name, 'up')

        except Exception as e:
            log.exception(e)
            return False

        log.info("Start VM %s finished.", vm_name)
        return True

    def _reboot_vm(self, vm_name):
        log.info("Reboot the VM %s" % vm_name)

        try:
            self._rhvm.operate_vm(vm_name, 'reboot')
            time.sleep(60)

            # Wait the vm is up
            self._wait_vm_status(vm_name, 'up')

        except Exception as e:
            log.exception(e)
            return False

        log.info("Reboot VM %s finished.", vm_name)
        return True

    def _poweroff_vm(self, vm_name):
        log.info("Poweroff the VM %s" % vm_name)

        try:
            self._rhvm.operate_vm(vm_name, 'stop')
            time.sleep(60)

            # Wait the vm is down
            self._wait_vm_status(vm_name, 'down')

        except Exception as e:
            log.exception(e)
            return False

        log.info("Poweroff VM %s finished.", vm_name)
        return True

    def _delete_vm(self, vm_name):
        log.info("Removing the VM %s" % vm_name)
        self._rhvm.remove_vm(vm_name)
        time.sleep(60)

    def _start_then_poweroff_vms(self, vm_quantity=1):
        log.info("Starting the VMs, then poweroff them...")
        
        try:
            value = 1
            while value <= vm_quantity:
                vm_name = self._vm_name + '_vm' + str(value)
                                
                if not self._start_vm(vm_name):
                    return False
                value += 1

            num = 1
            while num <= vm_quantity:
                vm_name = self._vm_name + '_vm' + str(num)
                                
                if not self._poweroff_vm(vm_name):
                    return False
                num += 1

        except Exception as e:
            log.exception(e)
            return False
        return True

    def _delete_vms_after_test(self, vm_quantity=1):
        log.info("Deleting VMs after test...")
        try:
            value = 1
            while value <= vm_quantity:
                vm_name = self._vm_name + '_vm' + str(value)
                if not vm_name or not self._rhvm.list_vm(vm_name):
                    raise RuntimeError("VM not exists")

                self._delete_vm(vm_name)
                value += 1
        except Exception as e:
            log.exception(e)
            return False
        return True


    def _bug_1837864_workaround_441_to_442_only(self):
        time.sleep(20)
        cmd = "sed -i '/^filter = /s/^filter = /#filter = /' /etc/lvm/lvm.conf"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Delete lvm filter failed.")
            return False
        log.info("Successfully deleted lvm filter.")
        time.sleep(20)

        cmd = "sed -n '/^#filter = /p' /etc/lvm/lvm.conf"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        log.info("The commented lvm filter is: %s", ret[1])
        
        return True
    
    #The following are functions related to test process control
    def yum_update_process(self):
        log.info("Start to upgrade rhvh via yum update cmd...")

        if not self._add_update_files():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._install_rpms():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._get_sssd_permissions('old'):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._install_userspace_svc_node_exporter():
            return False
        if not self._remove_audit_log():
            return False
        if not self._yum_upgrade('update'):
            return False
        #if not self._check_host_status_on_rhvm():
            #return False
        if not self._enter_system()[0]:
            return False
        if not self._get_sssd_permissions('new'):
            return False
        if not self._sssd_check():
            return False

        log.info("Upgrading rhvh via yum update cmd finished.")
        return True

    def yum_install_process(self):
        log.info("Start to upgrade rhvh via yum install cmd...")

        if not self._fetch_update_rpm_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        # if not self._bug_1837864_workaround_441_to_442_only():#this workaround only for 4.4.1 upgrade to 4.4.2
        #     return False
        if not self._check_cockpit_connection():
            return False
        if not self._install_rpms():
            return False
        if not self._mv_rpm_packages_on_host():
            return False
        if not self._set_locale_on_host():
            return False
        if not self._yum_upgrade('install'):
            return False
        if not self._enter_system()[0]:
            return False

        log.info("Upgrading rhvh via yum install finished.")
        return True

    def rhvm_upgrade_process(self):
        log.info("Start to upgrade rhvh via rhvm...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm(is_vlan=True):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        # if not self._bug_1837864_workaround_441_to_442_only():#this workaround only for 4.4.1 upgrade to 4.4.2
        #     return False
        if not self._check_cockpit_connection():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False

        log.info("Upgrade rhvh via rhvm finished.")
        return True

    def rhvm_upgrade_create_vms_process(self):
        log.info("Start to add VMs and upgrade rhvh via rhvm...")

        if not self._add_10_route():
            return False
        if not self._add_update_files():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._create_nfs_storage_domain():
            return False
        if not self._create_vms_with_disk(vm_quantity=3):
            return False
        if not self._start_then_poweroff_vms(vm_quantity=3):
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        time.sleep(120) # Waiting sd status become up
        if not self._start_then_poweroff_vms(vm_quantity=3):
            return False
        if not self._delete_vms_after_test(vm_quantity=3):
            return False
        if not self._enter_system(flag="auto")[0]:
            return False

        log.info("Add VMs and upgrade rhvh via rhvm finished.")
        return True

    def yum_local_storage_update_process(self):
        log.info("Start to add VMs on local storage, then upgrade rhvh via yum update cmd...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm(is_local=True):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._create_local_storage_domain(mount=False):
            return False
        if not self._create_vms_with_disk():
            return False
        if not self._start_then_poweroff_vms():
            return False
        if not self._check_cockpit_connection():
            return False
        if self._yum_upgrade('update'):
            log.error("Upgrade is not blocked.")
            return False

        log.info("Add VMs on local storage, then upgrade rhvh via yum update cmd finished.")
        return True
    
    def yum_local_storage_update_process_normal(self):
        log.info("Start to add VMs on local storage, then upgrade rhvh via RHVM...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm(is_local=True):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._create_local_storage_domain(mount=True):
            return False
        if not self._create_vms_with_disk():
            return False
        if not self._start_then_poweroff_vms():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        time.sleep(120) # Waiting sd status become up
        if not self._start_then_poweroff_vms():
            return False
        if not self._delete_vms_after_test():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False

        log.info("Add VMs on local storage, then upgrade rhvh via RHVM finished.")
        return True
    def rhvm_upgrade_config_and_reboot_process(self):
        log.info("Start to upgrade rhvh via rhvm...")

        if not self._add_10_route():
            return False
        if not self._register_rhsm_insights():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._config_lvm_filter():
            return False
        if not self._enter_system()[0]:
            return False
        if not self._get_lvm_filter('old'):
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False
        if not self._get_lvm_filter('new'):
            return False
        if not self._check_lvm_filter():
            return False

        log.info("Upgrade rhvh via rhvm finished.")
        return True
    
    def rhvm_failed_upgrade_process(self):
        log.info("Start to upgrade rhvh via rhvm...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_lvm_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._rhvm_upgrade():
            if not self._check_failed_status_on_rhvm():
                return False
        else:
            return False
        if not self._enter_system(flag="auto")[0]:
            return False

        log.info("Upgrade rhvh via rhvm finished.")
        return True
    
    def rhvm_bond_vlan_upgrade_process(self):
        log.info("Start to upgrade rhvh via rhvm...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._setup_vlan_over_bond():
            return False
        if not self._edit_grubenv_file():
            return False
        if not self._get_openvswitch_permissions('old'):
            return False
        if not self._add_host_to_rhvm(is_vlan=True):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False
        if not self._get_openvswitch_permissions('new'):
            return False
        if not self._openvswitch_check():
            return False

        log.info("Upgade rhvh via rhvm finished.")
        return True
   
    def yum_update_lack_space_process(self):
        if "-4.0-" in self._source_build:
            raise RuntimeError(
                "The source build is 4.0, no need to check.")

        log.info("Start to upgrade rhvh via yum update when no enough space left...")

        if not self._add_update_files():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._fill_up_space():
            return False

        log.info("Fill up space before upgrading rhvh via yum update finished.")
        return True

    def rhvm_update_iscsi_process(self):
        log.info("Start to upgrade iscsi rhvh via rhvm...")

        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm(is_vlan=False):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False

        log.info("Upgrade iscsi rhvh via rhvm finished.")
        return True

    def rhvm_update_bond_process(self):
        log.info("Start to upgrade rhvh with bond via rhvm...")

        if not self._put_repo_to_host():
            return False
        if not self._add_host_route_for_rhvm():
            return False
        if not self._add_host_to_rhvm(is_bond=True):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._add_host_route_for_repo():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False

        log.info("Upgrade rhvh with bond via rhvm finished.")
        return True

    def yum_update_vlan_process(self):
        log.info("Start to upgrade rhvh with vlan via yum update cmd...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm(is_vlan=True):
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._check_cockpit_connection():
            return False
        if not self._collect_service_status('old'):
            return False
        if not self._yum_upgrade('update'):
            return False
        if not self._enter_system()[0]:
            return False
        if not self._check_cockpit_connection():
            return False

        log.info("Upgrading rhvh with vlan via yum update finished.")
        return True

    def yum_upgrade_and_rollback_process(self, yum_cmd=False):
        log.info("Start to upgrade rhvh and then rollback...")

        if not self._add_update_files():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        # upgrade from RHVM side or run `yum update`
        if yum_cmd:    
            if not self._yum_upgrade('update'):
                return False
            if not self._enter_system()[0]:
                return False
            if not self._active_host():
                return False
        else:
            if not self._rhvm_upgrade():
                return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._deactive_rollback_active():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        
        log.info("Upgrading rhvh and rollback finished.")
        return True

    def rhvm_normal_upgrade_process(self):
        log.info("Start to upgrade rhvh via rhvm, then will check subscription-manager...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False
        if not self._remove_repo_on_host():
            return False

        log.info("Upgrade rhvh via rhvm finished, start to check subscription-manager...")
        return True

    def rhvm_rhsm_upgrade_process(self):
        log.info("Start to register to RHSM, then upgrade rhvh via rhvm...")

        if not self._add_10_route():
            return False
        if not self._register_and_subscrib():
            return False
        if not self._enable_repos():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False
        
        log.info("Register to RHSM and upgrade rhvh via rhvm finished.")
        return True

    def rhvm_fips_upgrade_process(self):
        log.info("Start to enable fips mode, then upgrade rhvh via rhvm...")

        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._enable_fips_mode():
            return False
        if not self._enter_system()[0]:
            return False
        if not self._check_fips_mode():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False
        
        log.info("In fips mode, upgrade rhvh via rhvm finished.")
        return True

    def rhvm_security_upgrade_process(self):
        log.info("In security mode, upgrade rhvh via rhvm...")

        if not self._check_openscap_config():
            return False
        if not self._add_10_route():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._rhvm_upgrade():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._enter_system(flag="auto")[0]:
            return False
        
        log.info("Register to RHSM and upgrade rhvh via rhvm finished.")
        return True

    def duplicate_service_yum_update_process(self):
        log.info("Start to upgrade rhvh via yum update cmd...")

        if not self._install_two_versions_of_svc():
            return False
        if not self._put_repo_to_host():
            return False
        if not self._add_host_to_rhvm():
            return False
        if not self._check_host_status_on_rhvm():
            return False
        if not self._yum_upgrade('update'):
            return False
        if not self._enter_system()[0]:
            return False
        if not self._active_host():
            return False
        if not self._check_host_status_on_rhvm():
            return False

        log.info("Upgrading rhvh via yum update cmd finished.")
        return True