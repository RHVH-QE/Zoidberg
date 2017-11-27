from rhvm_api import RhevmAction
from check_comm import CheckComm
from fabric.api import settings, env, run
import time
import logging

log = logging.getLogger('bender')


class RHVM(CheckComm):
    """"""

    def __init__(self):
        self._build = None  # redhat-virtualization-host-4.1-20170531.0
        self._vlanid = None  # 50
        self._rhvm = None  # An instance of RhevmAction
        self._rhvm_fqdn = None  # rhvm41-vlan50-1.lab.eng.pek2.redhat.com
        self._dc_name = None
        self._cluster_name = None
        self._host_ip = None
        self._host_name = None
        self._host_pass = None

    @property
    def build(self):
        return self._build

    @build.setter
    def build(self, val):
        self._build = val

    ##############################################
    # Create and Setup process
    ##############################################
    def _wait_host_status(self, host_name, expect_status):
        log.info("Waitting for the host %s" % expect_status)
        i = 0
        host_status = "unknown"
        while True:
            if i > 60:
                raise RuntimeError(
                    "Timeout waitting for host %s as current host status is: %s"
                    % (expect_status, host_status))
            host_status = self._rhvm.list_host(host_name)['status']
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

    def _update_network_vlan_tag(self):
        log.info("Updating network of datacenter with vlan tag")
        dc_name = self._dc_name
        vlan_id = self._vlanid
        self._rhvm.update_dc_network(
            dc_name, "ovirtmgmt", key="vlan", value=vlan_id)
        time.sleep(5)

    def _update_network_name(self, mgmt_name):
        log.info("Updating network of datacenter with custom name")
        dc_name = self._dc_name
        self._rhvm.update_dc_network(
            dc_name, "ovirtmgmt", key="name", value=mgmt_name)
        time.sleep(5)

    def _create_datacenter_and_cluster_host(self,
                                            dc_name,
                                            is_local,
                                            cluster_name,
                                            host_ip,
                                            host_name,
                                            host_pass,
                                            mgmt_name="ovirtgmgmt"):
        log.info("Creating the DC %s, cluster %s, and add the host %s" % \
                    (dc_name, cluster_name, host_name))
        try:
            AMD_CPU = "AMD"
            INTEL_CPU = "Intel"

            dc_name = self._dc_name
            cluster_name = self._cluster_name
            host_ip = self._host_ip
            host_name = self._host_name
            host_pass = self._host_pass

            if self._vlanid:
                self._update_network_vlan_tag()

            if mgmt_name != "ovirtgmgmt":
                self._update_network_name(mgmt_name)

            cmd = 'lscpu | grep "Model name"'
            ret = self.run_cmd(cmd, timeout=300)
            if ret[0]:
                if AMD_CPU in ret[1]:
                    cpu_type = "AMD Opteron G1"
                elif INTEL_CPU in ret[1]:
                    cpu_type = "Intel Conroe Family"
                else:
                    cpu_type = None
            else:
                cpu_type = None
            log.info("Creating datacenter %s and cluster %s" % (dc_name,
                                                                cluster_name))
            self._rhvm.add_datacenter(dc_name, is_local)
            time.sleep(10)
            self._rhvm.add_cluster(dc_name, cluster_name, cpu_type)
            time.sleep(10)
            log.info("Add the host %s to the cluster %s" % (host_name,
                                                            cluster_name))
            self._rhvm.add_host(host_ip, host_name, host_pass, cluster_name)
            time.sleep(60)

            self._wait_host_status(host_name, 'up')
        except Exception as e:
            log.exception(e)
            return False
        return True

    def _create_local_storage_domain(self, sd_name, data_path, host_name):
        log.info("Creating the local storage domain")
        try:
            self._rhvm.add_plain_storage_domain(
                domain_name=sd_name,
                domain_type='data',
                storage_type='localfs',
                storage_addr='',
                storage_path=data_path,
                host=host_name)
            time.sleep(60)
        except Exception as e:
            log.exception(e)
            return False
        return True

    def _create_nfs_storage_domain(self, sd_name, sd_type, storage_type,
                                   nfs_ip, nfs_pass, nfs_data_path, host_name,
                                   dc_name):
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
                domain_type=sd_type,
                storage_type=storage_type,
                storage_addr=nfs_ip,
                storage_path=nfs_data_path,
                host=host_name)
            time.sleep(60)
            self._rhvm.attach_sd_to_datacenter(sd_name, dc_name)

        except Exception as e:
            log.exception(e)
            return False
        return True

    def _create_iscsi_fc_lun(self, sd_name, sd_type, storage_type, lun_id,
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

    def _create_float_disk(self,
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

    def _attach_disk_to_vm(self, flag, vm_name, disk_name):
        log.info("Attaching the float disk to vm")
        bootable = True if flag == 1 else False

        self._rhvm.attach_disk_to_vm(disk_name, vm_name, bootable=bootable)
        time.sleep(20)

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

    def _create_vm(self, vm_name, cluster_name):
        self._rhvm.create_vm(vm_name=vm_name, cluster_name=cluster_name)
        time.sleep(30)

    ##################################################
    # Unattach and delete process
    ##################################################

    """
    def delete_vm(self, vm_name):
        log.info("Removing the vm %s" % vm_name)
        self._rhvm.remove_vm(vm_name)
        time.sleep(60)
    """

    def clean_after_check(self, vm_name, isd_name, host_name, cluster_name,
                          dc_name):
        log.info("Teardown and clean the env after check...")
        try:
            if vm_name and self._rhvm.list_vm(vm_name):
                log.info("Removing vm %s..." % vm_name)
                self._rhvm.remove_vm(vm_name)

            if host_name and self._rhvm.list_host(host_name):
                log.info("Maintenance host...")
                self._rhvm.deactive_host(host_name)
                time.sleep(60)
            
            # Some problems about the ovirt shell(CLI)
            if isd_name and self._rhvm.list_storage_domain(isd_name):
                log.info("Removing iso domain...")
                self._rhvm.remove_storage_domain(isd_name, host_name)
                time.sleep(10)

            if dc_name and self._rhvm.list_datacenter(dc_name):
                log.info("Force removing datacenter...")
                self._rhvm.remove_datacenter(dc_name, force=True)
                time.sleep(5)

            if host_name and self._rhvm.list_host(host_name):
                log.info("Removing the host...")
                self._rhvm.remove_host(host_name)
                time.sleep(5)

            if cluster_name and self._rhvm.list_cluster(cluster_name):
                log.info("Removing cluster...")
                self._rhvm.remove_cluster(cluster_name)
                time.sleep(5)

        except Exception as e:
            log.exception(e)
            return False
        return True
