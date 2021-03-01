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
    # security_engine_check
    ##########################################


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
                    if host and (host.get('status') == 'up' or host.get('status') == 'non_operational'):
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



    def _active_host(self):
        log.info("Active host, please wait...")
        try:
            self._rhvm.active_host(self._host_name)
        except Exception as e:
            log.error(e)
            return False

        log.info("Active host finished.")
        return True



    def rhvm_security_upgrade_process(self):
        log.info("In security mode, register rhvh via rhvm...")

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
        
        log.info("Register rhvh via rhvm with security profile selected finished.")
        return True
