import time
import logging
from fabric.api import settings, env, run
from rhvm_api import RhevmAction
from remote_cmd import RemoteCmd

log = logging.getLogger('bender')


class RHVM(RhevmAction):
    """"""

    def __init__(self, fqdn_name, dc_name, cluster_name, host_ip, host_name,
                 host_pass):
        RhevmAction.__init__(self, fqdn_name)
        self._fqdn_name = fqdn_name
        self._dc_name = dc_name
        self._cluster_name = cluster_name
        self._host_ip = host_ip
        self._host_name = host_name
        self._host_pass = host_pass
        self._vlanid = None  # 50
        #self._remotecmd = RemoteCmd(host_ip, "root", "redhat")
        self._rhvm = None  # An instance of RHVM

    @property
    def vlan(self):
        return self._vlanid

    @vlan.setter
    def vlan(self, val):
        self._vlanid = val

    def set_rhvm(self):
        self._rhvm = RHVM(self._fqdn_name, self._dc_name, self._cluster_name,
                          self._host_ip, self._host_name, self._host_pass)

    def _wait_host_status(self, host_name, expect_status):
        log.info("Waitting for the host %s" % expect_status)
        i = 0
        host_status = "unknown"
        while True:
            if i > 50:
                raise RuntimeError(
                    "Timeout waitting for host %s as current host status is: %s"
                    % (expect_status, host_status))
            host_status = self._rhvm.list_host("name", host_name)['status']
            log.info("HOST: %s" % host_status)
            if host_status == expect_status:
                break
            elif host_status == 'install_failed':
                raise RuntimeError("Host is not %s as current status is: %s" %
                                   (expect_status, host_status))
            elif host_status == 'non_operational':
                raise RuntimeError("Host is not %s as current status is: %s" %
                                   (expect_status, host_status))
            time.sleep(10)
            i += 1

    def _wait_vm_status(self, vm_name, expect_status):
        log.info("Waitting the vm to the status %s" % expect_status)
        i = 0
        vm_status = "unknown"
        while True:
            if i > 30:
                log.error("VM status is %s, not %s" % (vm_status,
                                                       expect_status))
                return False

            vm_status = self._rhvm.list_vm(vm_name)['status']
            log.info("VM: %s" % vm_status)

            if vm_status == expect_status:
                return True
            time.sleep(10)
            i += 1

    ##############################################
    # Create and Setup process
    ##############################################

    def create_datacenter_and_cluster_host(self,
                                           is_local,
                                           cpu,
                                           vlanid,
                                           mgmt_name="ovirtgmgmt"):
        """
        Usage: 
            rhvm = RHVM("rhvm42-vlan50-1.lab.eng.pek2.redhat.com", "yzhao_dc2", "yzhao_cluster2", "192.168.50.114", "yzhao_host2", "redhat")
            rhvm.set_rhvm()
            rhvm.create_datacenter_and_cluster_host(False, "AMD", 50, "networkyzhao")
        """
        
        log.info("Creating the DC %s, cluster %s, and add the host %s" % \
                    (self._dc_name, self._cluster_name, self._host_name))

        if cpu == "AMD":
            cpu_type = "AMD Opteron G1"
        elif cpu == "Intel":
            cpu_type = "Intel Conroe Family"
        else:
            cpu_type = None

        try:
            log.info("Creating datacenter %s and cluster %s" %
                     (self._dc_name, self._cluster_name))
            self._rhvm.add_datacenter(self._dc_name, is_local)
            time.sleep(10)

            if vlanid:
                self._rhvm.update_dc_network(self._dc_name, "ovirtmgmt",
                                             "vlan", vlanid)
            if mgmt_name != "ovirtmgmt":
                self._rhvm.update_dc_network(self._dc_name, "ovirtmgmt",
                                             "name", mgmt_name)

            self._rhvm.add_cluster(self._dc_name, self._cluster_name, cpu_type)
            time.sleep(10)
            log.info("Add the host %s to the cluster %s" %
                     (self._host_name, self._cluster_name))

            self._rhvm.add_host(self._host_ip, self._host_name,
                                self._host_pass, self._cluster_name)
            time.sleep(60)

            self._wait_host_status(self._host_name, 'up')

        except Exception as e:
            log.exception(e)
            return False
        return True

    def create_local_storage_domain(self, sd_name, domain_type, data_path,
                                    host_name):
        log.info("Creating the local storage domain")
        try:
            self._rhvm.add_plain_storage_domain(
                domain_name=sd_name,
                domain_type=domain_type,
                storage_type='localfs',
                storage_addr='',
                storage_path=data_path,
                host=host_name)
            time.sleep(60)
        except Exception as e:
            log.exception(e)
            return False
        return True

    def create_nfs_storage_domain(self, sd_name, domain_type, nfs_ip, nfs_pass,
                                  nfs_data_path, host_name, dc_name):
        log.info("Clean up the nfs path.")
        cmd = "rm -rf %s/*" % nfs_data_path
        with settings(
                warn_only=True, host_string='root@' + nfs_ip,
                password=nfs_pass):
            ret = run(cmd)
        if ret.failed:
            raise RuntimeError(
                "Failed to clean up the nfs path %s." % nfs_data_path)
        try:
            log.info(
                "Creating the nfs storage domain, the storage type is data or iso."
            )
            self._rhvm.add_plain_storage_domain(
                domain_name=sd_name,
                domain_type=domain_type,
                storage_type="nfs",
                storage_addr=nfs_ip,
                storage_path=nfs_data_path,
                host=host_name)
            time.sleep(80)
            self._rhvm.attach_sd_to_datacenter(sd_name, dc_name)

        except Exception as e:
            log.exception(e)
            return False
        return True

    def create_iscsi_fc_lun(self, sd_name, sd_type, storage_type, lun_id,
                            host_name, dc_name):
        log.info("creating the fc or iscsi direct lun storage domain")
        try:
            self._rhvm.add_fc_scsi_storage_domain(
                sd_name=sd_name,
                sd_type=sd_type,
                storage_type=storage_type,
                lun_id=lun_id,
                host=host_name)
            time.sleep(60)
            self._rhvm.attach_sd_to_datacenter(sd_name, dc_name)

        except Exception as e:
            log.exception(e)
            return False
        return True

    def create_float_disk(self,
                          disk_name,
                          disk_type,
                          disk_size,
                          sd_name,
                          host_name,
                          lun_id=None,
                          lun_addr=None,
                          lun_port=None,
                          lun_target=None):
        """
        Create a float disk for vm using
        """
        log.info("Creating a float disk for vm")
        if disk_type == "localfs" or disk_type == "nfs":
            self._rhvm.create_float_image_disk(sd_name, disk_name, disk_size)
        else:
            self._rhvm.create_float_direct_lun_disk(
                disk_name=disk_name,
                host_name=host_name,
                lun_type=disk_type,
                lun_id=lun_id,
                lun_addr=lun_addr,
                lun_port=lun_port,
                lun_target=lun_target)
        time.sleep(60)

    def attach_floatdisk_to_vm(self, flag, vm_name, disk_name):
        log.info("Attaching the float disk to vm")
        bootable = True if flag == 1 else False

        self._rhvm.attach_disk_to_vm(disk_name, vm_name, bootable=bootable)
        time.sleep(20)

    def create_new_vm(self, vm_name, cluster_name):
        log.info("Creating a new vm...")
        self._rhvm.create_vm(vm_name=vm_name, cluster_name=cluster_name)
        time.sleep(30)

    ##################################################
    # Unattach and delete process
    ##################################################

    def clean_after_check(self, vm_name, host_name, cluster_name, dc_name):
        log.info("Teardown and clean the env after check...")
        log.info("Removing the vm...")
        if vm_name and self._rhvm.list_vm(vm_name):
            log.info("Removing vm %s..." % vm_name)
            if self._rhvm.list_vm(vm_name)['status'] == "up":
                self._rhvm.operate_vm(vm_name, "stop")
                self._wait_vm_status(vm_name, "down")

            self._rhvm.remove_vm(vm_name)
            time.sleep(20)

        try:
            if host_name and self._rhvm.list_host("name", host_name):
                log.info("Maintenance host...")
                self._rhvm.deactive_host(host_name)
                time.sleep(30)

        except Exception as e:
            log.exception(e)

        finally:
            # Should delete the not master type storagedomains
            log.info("Delete all the storagedomains of the datacenter...")
            for sd_name, master_type in self._rhvm.list_dc_storage(
                    dc_name).items():
                if master_type == "false":
                    self._rhvm.remove_storage_domain(sd_name, host_name)
                    time.sleep(5)

            if self._rhvm.list_dc_storage(dc_name):
                for sd_name, master_type in self._rhvm.list_dc_storage(
                        dc_name).items():
                    self._rhvm.remove_storage_domain(sd_name, host_name)
                time.sleep(5)

                # Should delete not the master storagedomain firstly
                """
                if isd_name and self._rhvm.list_storage_domain(isd_name):
                    log.info("Removing iso domain...")
                    self._rhvm.remove_storage_domain(isd_name, host_name)
                    time.sleep(10)
                """
            try:
                if host_name and self._rhvm.list_host("name", host_name):
                    log.info("Removing the host...")
                    self._rhvm.remove_host(host_name)
                    time.sleep(10)

                if cluster_name and self._rhvm.list_cluster(cluster_name):
                    log.info("Removing cluster...")
                    self._rhvm.remove_cluster(cluster_name)
                    time.sleep(10)

                if dc_name and self._rhvm.list_datacenter(dc_name):
                    log.info("Force removing datacenter...")
                    self._rhvm.remove_datacenter(dc_name, force=True)
                    time.sleep(10)

            except Exception as e:
                log.exception(e)
                return False
            return True


if __name__ == "__main__":
    rhvm = RHVM("rhvm42-vlan50-1.lab.eng.pek2.redhat.com", "yzhao_dc1",
                "yzhao_cluster1", "10.66.8.176", "yzhao_host1", "redhat")
    rhvm.set_rhvm()
    # rhvm.create_datacenter_and_cluster_host(False, "Intel", None, "ovirtmgmt")
    # rhvm.create_nfs_storage_domain("yzhao_data", "data", "10.66.148.11", "redhat", "/home/jiawu/nfs2", "yzhao_host1", "yzhao_dc1")
    # rhvm.create_nfs_storage_domain("yzhao_iso", "iso", "10.66.148.11", "redhat", "/home/jiawu/nfs1", "yzhao_host1", "yzhao_dc1")
    #rhvm.create_float_disk("yzhao_disk1", "nfs", 21474836480, "yzhao_data", "yzhao_host1")  # 20G
    #rhvm.create_new_vm("yzhao_vm", "yzhao_cluster1")
    #rhvm.attach_floatdisk_to_vm(1, "yzhao_vm", "yzhao_disk1")
    #rhvm.start_vm("yzhao_vm")

    rhvm.clean_after_check("yzhao_vm", "yzhao_host1", "yzhao_cluster1",
                           "yzhao_dc1")
