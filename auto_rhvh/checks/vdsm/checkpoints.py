import logging
import re
import time
from fabric.api import settings, run


log = logging.getLogger('bender')


class CheckPoints(object):
    """"""

    def __init__(self):
        self._ksfile = None
        self._vdsminfo = None
        self._remotecmd = None
        self._rhvm = None

    @property
    def ksfile(self):
        return self._ksfile

    @ksfile.setter
    def ksfile(self, val):
        self._ksfile = val

    @property
    def vdsminfo(self):
        return self._vdsminfo

    @vdsminfo.setter
    def vdsminfo(self, val):
        self._vdsminfo = val

    @property
    def remotecmd(self):
        return self._remotecmd

    @remotecmd.setter
    def remotecmd(self, val):
        self._remotecmd = val

    def set_rhvm(self):
        self._rhvm = self._vdsminfo.rhvm

    def _wait_host_status(self, host_name, expect_status):
        log.info("Waitting for the host %s" % expect_status)
        i = 0
        host_status = "unknown"
        while True:
            if i > 60:
                raise RuntimeError("Timeout waitting for host %s as current host status is: %s" % (
                    expect_status, host_status))
            host_status = self._rhvm.list_host(host_name)['status']
            log.info("HOST: %s" % host_status)
            if host_status == expect_status:
                break
            elif host_status == 'install_failed':
                raise RuntimeError("Host is not %s as current status is: %s" % (
                    expect_status, host_status))
            elif host_status == 'non_operational':
                raise RuntimeError("Host is not %s as current status is: %s" % (
                    expect_status, host_status))
            time.sleep(15)
            i += 1

    def _update_network_vlan_tag(self, dc_name, vlan_id):
        log.info("Updating network of datacenter with vlan tag")
        self._rhvm.update_dc_network(
            dc_name, "ovirtmgmt", key="vlan", value=vlan_id)
        time.sleep(5)

    def _update_network_name(self, dc_name, mgmt_name):
        log.info("Updating network of datacenter with custom name")
        self._rhvm.update_dc_network(
            dc_name, "ovirtmgmt", key="name", value=mgmt_name)
        time.sleep(5)

    ##########################################
    # CheckPoint ca0_create_new_host_check
    ##########################################
    def ca0_create_new_host_check(self):
        log.info("Checking host can be added...")
        try:
            host_ip = self._vdsminfo.host_info["host_ip"]
            host_name = self._vdsminfo.host_info["host_name"]
            host_pass = self._vdsminfo.host_info["host_pass"]
            dc_name = self._vdsminfo.rhvm_info["dc_name"]
            cluster_name = self._vdsminfo.rhvm_info["cluster_name"]
            vlan_id = self._vdsminfo.rhvm_info.get("vlan_id", None)

            if vlan_id:
                self._update_network_vlan_tag(dc_name, vlan_id)

            if re.search("vlani", self._ksfile):
                # Change the default ovitgmgmt name
                mgmt_name = "atvmgmt"
                self._update_network_name(dc_name, mgmt_name)

            self._rhvm.create_new_host(
                host_ip, host_name, host_pass, cluster_name)

            self._wait_host_status(host_name, 'up')
        except Exception as e:
            log.exception(e)
            return False

        return True

    ##########################################
    # CheckPoint cl3_fcoe_service_check
    ##########################################
    def cl3_fcoe_service_check(self):
        log.info("Checking the fcoe related service is running")
        ck_services = ["fcoe.service", "lldpad.service", "lldpad.service"]
        for ck_service in ck_services:
            cmd = "service %s status" % ck_service
            ret = self._remotecmd.run_cmd(cmd)
            if ret[0] and re.search("(running)", ret[1]):
                continue
            else:
                log.error("%s service is not running" % ck_service)
                return False
        return True

    def _create_local_data_path(self, data_path):
        log.info("Creating the local data path")
        cmd = "test -r %s" % data_path
        ret = self._remotecmd.run_cmd(cmd)
        if not ret[0]:
            cmd = "mkdir -p %s" % data_path
            self._remotecmd.run_cmd(cmd)
        else:
            cmd = "rm -rf %s/*" % data_path
            self._remotecmd.run_cmd(cmd)
        cmd = "chmod 777 %s" % data_path
        ret = self._remotecmd.run_cmd(cmd)
        if not ret[0]:
            raise RuntimeError("Faile to chmod %s" % data_path)

    def _create_local_storage_domain(self, sd_name, data_path, host_name):
        log.info("Creating the local storage domain")
        self._rhvm.create_plain_storage_domain(
            sd_name=sd_name,
            sd_type='data',
            storage_type='localfs',
            storage_addr='',
            storage_path=data_path,
            host=host_name)
        time.sleep(60)

    def _attach_sd_to_dc(self, sd_name, dc_name):
        log.info("Attaching the storage domain %s to %s" % (sd_name, dc_name))
        self._rhvm.attach_sd_to_datacenter(sd_name=sd_name, dc_name=dc_name)
        time.sleep(30)
        return True

    ##########################################
    # CheckPoint cl1_create_local_sd_check
    ##########################################
    def cl1_create_local_sd_check(self):
        log.info("Checking local storage domain can be created and attached...")
        try:
            host_name = self._vdsminfo.host_info['host_name']
            sd_name = self._vdsminfo.storage_info['sd_name']
            storage_type = self._vdsminfo.storage_info['storage_type']
            if not storage_type == "localfs":
                raise RuntimeError(
                    "Storage type is %s, not localfs" % storage_type)

            # Create local data directory
            data_path = self._vdsminfo.storage_info['data_path']
            self._create_local_data_path(data_path)

            # Create local storage domain
            self._create_local_storage_domain(sd_name, data_path, host_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

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

    def _create_nfs_storage_domain(self, sd_name, sd_type, nfs_ip, nfs_data_path, host_name):
        log.info("Creating the nfs storage domain %s" % sd_name)
        self._rhvm.create_plain_storage_domain(
            sd_name=sd_name,
            sd_type=sd_type,
            storage_type='nfs',
            storage_addr=nfs_ip,
            storage_path=nfs_data_path,
            host=host_name)
        time.sleep(60)

    ##########################################
    # CheckPoint cn1_create_nfs_sd_check
    ##########################################
    def cn1_create_nfs_sd_check(self):
        log.info("Checking nfs storage domain can be created...")
        try:
            host_name = self._vdsminfo.host_info['host_name']
            sd_name = self._vdsminfo.storage_info['sd_name']
            sd_type = 'data'
            dc_name = self._vdsminfo.rhvm_info['dc_name']
            storage_type = self._vdsminfo.storage_info['storage_type']
            if not storage_type == "nfs":
                raise RuntimeError("Storage type is %s, not nfs" % storage_type)

            # Clean the nfs path
            nfs_ip = self._vdsminfo.storage_info["nfs_ip"]
            nfs_passwd = self._vdsminfo.storage_info["nfs_password"]
            nfs_data_path = self._vdsminfo.storage_info["nfs_data_path"]
            self._clean_nfs_path(nfs_ip, nfs_passwd, nfs_data_path)

            # Create the nfs storage domain
            self._create_nfs_storage_domain(
                sd_name, sd_type, nfs_ip, nfs_data_path, host_name)

            # Attach the sd to datacenter
            self._attach_sd_to_dc(sd_name, dc_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    ##########################################
    # CheckPoint cn2_create_iso_sd_check
    ##########################################
    def cn2_create_iso_sd_check(self):
        log.info("Checking iso storage domain can be created...")
        try:
            host_name = self._vdsminfo.host_info['host_name']
            isd_name = self._vdsminfo.storage_info['isd_name']
            sd_type = 'iso'
            dc_name = self._vdsminfo.rhvm_info['dc_name']
            storage_type = self._vdsminfo.storage_info['storage_type']
            if not storage_type == "nfs":
                raise RuntimeError("Storage type is %s, not nfs" % storage_type)

            # Clean the nfs path
            nfs_ip = self._vdsminfo.storage_info["nfs_ip"]
            nfs_passwd = self._vdsminfo.storage_info["nfs_password"]
            nfs_iso_path = self._vdsminfo.storage_info["nfs_iso_path"]
            self._clean_nfs_path(nfs_ip, nfs_passwd, nfs_iso_path)

            # Create the iso storage domain
            self._create_nfs_storage_domain(
                isd_name, sd_type, nfs_ip, nfs_iso_path, host_name)

            # Attach the sd to datacenter
            self._attach_sd_to_dc(isd_name, dc_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    def _clear_fc_scsi_lun(self, lun_id):
        log.info("Clearing the fc or scsi lun to ensure the it's clean")
        pv = "/dev/mapper/%s" % lun_id
        vg = None
        lun_parts = []

        # Get the vg name if there exists
        cmd = "pvs|grep %s" % lun_id
        ret = self._remotecmd.run_cmd(cmd)
        if ret[0] and ret[1]:
            vg = ret[1].split()[1]
        else:
            # If there is lvm on the lun, get the vg from lvm
            cmd = "lsblk -l %s|grep lvm|awk '{print $1}'" % pv
            ret = self._remotecmd.run_cmd(cmd)
            if ret[0] and ret[1]:
                alvm_blk = ret[1].split()[0]
                new_alvm_blk = alvm_blk.replace("--", "##")
                alvm_prefix = new_alvm_blk.split('-')[0]
                vg = alvm_prefix.replace("##", "-")

            # If there is partition on the lun, get all of them
            cmd = "lsblk -l %s|grep 'part'|awk '{print $1}'" % pv
            ret = self._remotecmd.run_cmd(cmd)
            if ret[0]:
                for blk_part in ret[1].split():
                    lun_parts.append("/dev/mapper/" + blk_part)

        # Delete the lun
        cmd = "dd if=/dev/zero of=%s bs=50M count=10" % pv
        self._remotecmd.run_cmd(cmd)

        # Delete the partition if exists
        if lun_parts:
            for lun_part in lun_parts:
                cmd = "dd if=/dev/zero of=%s bs=50M count=10" % lun_part
                self._remotecmd.run_cmd(cmd)

        # Delete the vg if exists
        if vg:
            cmd = "dmsetup remove /dev/%s/*" % vg
            self._remotecmd.run_cmd(cmd)

    def _create_fc_scsi_storage_domain(self, sd_name, sd_type, storage_type, lun_id, host_name):
        log.info("Creating the fc or scsi direct lun storage domain")
        self._rhvm.create_fc_scsi_storage_domain(
            sd_name=sd_name,
            sd_type=sd_type,
            storage_type=storage_type,
            lun_id=lun_id,
            host=host_name)
        time.sleep(60)

    ##########################################
    # CheckPoint cf1_create_fc_sd_check
    ##########################################
    def cf1_create_fc_sd_check(self):
        log.info("Checking the fc storage domain can be created...")
        try:
            host_name = self._vdsminfo.host_info['host_name']
            sd_name = self._vdsminfo.storage_info['sd_name']
            dc_name = self._vdsminfo.rhvm_info['dc_name']
            storage_type = self._vdsminfo.storage_info['storage_type']
            if not storage_type == "fcp":
                raise RuntimeError("Storage type is %s, not fc" % storage_type)

            # Clean the fc lun
            lun_id = self._vdsminfo.storage_info["avl_luns"][0]
            self._clear_fc_scsi_lun(lun_id)

            # Create the fc storage domain
            self._create_fc_scsi_storage_domain(
                sd_name,
                'data',
                storage_type,
                lun_id,
                host_name)

            # Attach the sd to datacenter
            self._attach_sd_to_dc(sd_name, dc_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    ##########################################
    # CheckPoint cf1_create_scsi_sd_check
    ##########################################
    def cs1_create_scsi_sd_check(self):
        log.info("Checking the scsi storage domain can be created...")
        try:
            host_name = self._vdsminfo.host_info['host_name']
            sd_name = self._vdsminfo.storage_info['sd_name']
            dc_name = self._vdsminfo.rhvm_info['dc_name']
            storage_type = self._vdsminfo.storage_info['storage_type']
            if not storage_type == "iscsi":
                raise RuntimeError("Storage type is %s, not iscsi" % storage_type)

            # Clean the fc lun
            lun_id = self._vdsminfo.storage_info["avl_luns"][0]
            self._clear_fc_scsi_lun(lun_id)

            # Create the fc storage domain
            self._create_fc_scsi_storage_domain(
                sd_name,
                'data',
                storage_type,
                lun_id,
                host_name)

            # Attach the sd to datacenter
            self._attach_sd_to_dc(sd_name, dc_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    def _create_vm(self, vm_name, cluster_name):
        log.info("Creating a VM")
        self._rhvm.create_vm(vm_name=vm_name, cluster=cluster_name)
        time.sleep(30)

    def _create_float_disk(self, flag):
        """
        Create a float disk for vm using
        :param flag: "disk0" or "disk1"
        :return:
        """
        log.info("Creating a float disk for VM")
        disk_name = self._vdsminfo.disk_info[flag]["disk_name"]
        disk_type = self._vdsminfo.disk_info[flag]["disk_type"]
        sd_name = self._vdsminfo.storage_info["sd_name"]
        host_name = self._vdsminfo.host_info["host_name"]
        if disk_type == "localfs" or disk_type == "nfs":
            disk_size = self._vdsminfo.disk_info[flag]["disk_size"]
            self._rhvm.create_float_image_disk(sd_name, disk_name, disk_size)
        else:
            lun_id = self._vdsminfo.disk_info[flag]["lun_id"]
            lun_addr = self._vdsminfo.disk_info[flag]["lun_addr"]
            lun_port = self._vdsminfo.disk_info[flag]["lun_port"]
            lun_target = self._vdsminfo.disk_info[flag]["lun_target"]

            self._rhvm.create_float_direct_lun_disk(
                disk_name=disk_name,
                host_name=host_name,
                lun_type=disk_type,
                lun_id=lun_id,
                lun_addr=lun_addr,
                lun_port=lun_port,
                lun_target=lun_target)
        time.sleep(60)

    def _attach_disk_to_vm(self, flag):
        log.info("Attaching the float disk to VM")
        bootable = True if flag == "disk0" else False
        vm_name = self._vdsminfo.vm_info["vm_name"]
        disk_name = self._vdsminfo.disk_info[flag]["disk_name"]
        self._rhvm.attach_disk_to_vm(disk_name, vm_name, bootable=bootable)
        time.sleep(30)

    ##########################################
    # CheckPoint cv1_create_vm_with_disk_check
    ##########################################
    def cv1_create_vm_with_disk_check(self):
        log.info("Checking the disk can be added to vm...")
        try:
            cluster_name = self._vdsminfo.rhvm_info["cluster_name"]
            vm_name = self._vdsminfo.vm_info["vm_name"]
            # Create the vm
            self._create_vm(vm_name, cluster_name)

            # Create the float disk
            self._create_float_disk("disk0")

            # Attach the disk to vm
            self._attach_disk_to_vm("disk0")
        except Exception as e:
            log.exception(e)
            return False
        return True

    ###############################################
    # CheckPoint cv1_attach_second_disk_to_vm_check
    ###############################################
    def cv2_attach_second_disk_to_vm_check(self):
        log.info("Checking the second disk can be added to vm...")
        try:
            # Create the float disk
            self._create_float_disk("disk1")

            # Attach the disk to vm
            self._attach_disk_to_vm("disk1")
        except Exception as e:
            log.exception(e)
            return False
        return True

    def _wait_vm_status(self, vm_name, expect_status):
        log.info("Waitting the vm to status %s" % expect_status)
        i = 0
        vm_status = "unknown"
        while True:
            if i > 30:
                log.error("VM status is %s, not %s" % (vm_status, expect_status))
                return False
            vm_status = self._rhvm.list_vm(vm_name)['status']
            log.info("VM: %s" % vm_status)
            if vm_status == expect_status:
                return True
            time.sleep(10)
            i += 1

    def _start_vm(self, vm_name):
        log.info("Start up the vm %s" % vm_name)

        self._rhvm.operate_vm(vm_name, 'start')
        time.sleep(60)

        # Wait the vm is up
        self._wait_vm_status(vm_name, 'up')

    def _reboot_vm(self, vm_name):
        log.info("Reboot the vm %s" % vm_name)

        self._rhvm.operate_vm(vm_name, 'reboot')
        time.sleep(60)

        # Wait the vm is up
        self._wait_vm_status(vm_name, 'up')

    def _poweroff_vm(self, vm_name):
        log.info("Poweroff the vm %s" % vm_name)
        self._rhvm.operate_vm(vm_name, 'stop')
        time.sleep(60)

        # Wait the vm is down
        self._wait_vm_status(vm_name, 'down')

    ##########################################
    # CheckPoint cv2_vm_life_cycle_check
    ##########################################
    def cv3_vm_life_cycle_check(self):
        log.info("Checking the vm lifecycle...")
        try:
            vm_name = self._vdsminfo.vm_info["vm_name"]
            if not vm_name or not self._rhvm.list_vm(vm_name):
                raise RuntimeError("VM not exists")

            # Start up the vm
            self._start_vm(vm_name)

            # Reboot the vm
            self._reboot_vm(vm_name)

            # Poweroff the vm
            self._poweroff_vm(vm_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    def _delete_vm(self, vm_name):
        log.info("Removing the vm %s" % vm_name)
        self._rhvm.remove_vm(vm_name)
        time.sleep(60)

    ##########################################
    # CheckPoint cv3_delete_vm_check
    ##########################################
    def cv9_delete_vm_check(self):
        log.info("Checking the vm can be deleted...")
        try:
            vm_name = self._vdsminfo.vm_info["vm_name"]
            if not vm_name or not self._rhvm.list_vm(vm_name):
                raise RuntimeError("VM not exists")

            self._delete_vm(vm_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    ##########################################
    # CheckPoint cz1_maintenance_host_check
    ##########################################
    def cz1_maintenance_host_check(self):
        log.info("Checking the host can be maintenanced...")
        try:
            host_name = self._vdsminfo.host_info["host_name"]

            self._rhvm.deactive_host(host_name)

            self._wait_host_status(host_name, "maintenance")
        except Exception as e:
            log.exception(e)
            return False
        return True

    ##########################################
    # CheckPoint cz2_remove_host_check
    ##########################################
    def cz2_remove_host_check(self):
        log.info("Checking the host can be removed...")
        try:
            host_name = self._vdsminfo.host_info["host_name"]
            self._rhvm.remove_host(host_name)
        except Exception as e:
            log.exception(e)
            return False
        return True
