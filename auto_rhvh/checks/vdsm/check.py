import logging
import re
import time
import functools
from fabric.api import settings, run, local
from consts_vdsm import RHVM_INFO, MACHINE_INFO, NFS_INFO
from ..helpers import CheckComm
from ..helpers.vdsmapi import RhevmAction

log = logging.getLogger('bender')

rhvm_fqdn_tpl = "rhvmx_vlany_fqdn"
datacenter_name_tpl = "atv_tpl_dc"
cluster_name_tpl = "atv_tpl_cs"
host_name_tpl = "atv_tpl_host"
sd_name_tpl = "atv_tpl_sd"
isd_name_tpl = "atv_tpl_isd"
vm_name_tpl = "atv_tpl_vm"
disk0_name_tpl = "atv_tpl_disk0"
disk1_name_tpl = "atv_tpl_disk1"


class CheckVdsm(CheckComm):
    """"""

    def __init__(self):
        self._build = None  # redhat-virtualization-host-4.1-20170531.0
        self._vlanid = None  # 50
        self._rhvm = None  # instance of RhevmAction
        self._rhvm_fqdn = None  # rhvm41-vlan50-1.lab.eng.pek2.redhat.com
        self._dc_info = {}  # {"dc_name": vdsm_fc_dc, "is_local": False}
        self._cluster_info = {}  # {"cluster_name": cluster_name, "cpu_type": "AMD Opteron G1"}
        # {"host_ip": host_ip, "host_pass": host_pass, "host_name": vdsm_fc_host}
        self._host_info = {}
        self._sd_info = {}  # {"storage_type": "localfs", "data_path": "/home/data"}
        # {"network_type": bond, "slaves": [nic1, nic2]}
        self._network_info = {}
        self._vm_info = {}  # {"vm_name": vm_name}
        self._disk_info = {}  # {"disk0": {"disk_name": disk0_name, "disk_type": disk0_type}}

    @property
    def build(self):
        return self._build

    @build.setter
    def build(self, val):
        self._build = val

    def checkpoint(text):
        def decorator(func):
            @functools.wraps(func)
            def ckp(*args, **kw):
                log.info(text)
                ret = func(*args, **kw)
                return ret
            return ckp
        return decorator

    ##########################################
    # Before checking, creating dc, cluster
    ##########################################
    def _get_host_version(self):
        BUILD_4_0 = "-4.0-"
        BUILD_4_1 = "-4.1-"
        if BUILD_4_0 in self._build:
            build_ver = "40"
        elif BUILD_4_1 in self._build:
            build_ver = "41"
        else:
            build_ver = None
        return build_ver

    def _get_host_vlanid(self):
        if re.search("vlan|bv", self.ksfile):
            if MACHINE_INFO[self.beaker_name].get('vlan', None):
                self._vlanid = MACHINE_INFO[self.beaker_name]['vlan']['id']
            else:
                if MACHINE_INFO[self.beaker_name].get('bv', None):
                    self._vlanid = MACHINE_INFO[self.beaker_name]['bv']['vlan_id']

    def _get_rhvm_fqdn(self):
        build_ver = self._get_host_version()
        if not build_ver:
            raise RuntimeError("The version of host build is not 4.0 or 4.1")
        else:
            bv_key = build_ver

        vi_key = "50"
        self._get_host_vlanid()
        if self._vlanid:
            vi_key = self._vlanid

        k1 = rhvm_fqdn_tpl.replace('x', bv_key)
        k2 = k1.replace('y', vi_key)
        self._rhvm_fqdn = RHVM_INFO.get(k2)

    def _get_rhvm(self):
        self._get_rhvm_fqdn()
        self._rhvm = RhevmAction(self._rhvm_fqdn)
        log.info("Testing on rhvm %s" % self._rhvm_fqdn)

    def _get_dc_info(self):
        scen = self.ksfile.split('_')[1]
        dc_name = datacenter_name_tpl.replace('tpl', scen)
        is_local = False
        if re.search('local', self.ksfile):
            is_local = True
        self._dc_info = {"dc_name": dc_name, "is_local": is_local}

    def _create_datacenter(self):
        self._get_dc_info()
        log.info("Creating datacenter %s" % self._dc_info["dc_name"])
        dc_name = self._dc_info["dc_name"]
        is_local = self._dc_info["is_local"]

        # Create datacenter
        self._rhvm.create_datacenter(dc_name, is_local)
        time.sleep(5)

    def _get_cluster_info(self):
        AMD_CPU = "AMD"
        INTEL_CPU = "Intel"

        scen = self.ksfile.split('_')[1]
        cluster_name = cluster_name_tpl.replace('tpl', scen)
        self._cluster_info.update({"cluster_name": cluster_name})

        cmd = 'lscpu | grep "Model name"'
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if ret[0]:
            if AMD_CPU in ret[1]:
                cpu_type = "AMD Opteron G1"
            elif INTEL_CPU in ret[1]:
                cpu_type = "Intel Conroe Family"
            else:
                cpu_type = None
        else:
            cpu_type = None
        self._cluster_info.update({"cpu_type": cpu_type})

    def _create_cluster(self):
        self._get_cluster_info()
        log.info("Creating cluster %s" % self._cluster_info["cluster_name"])
        dc_name = self._dc_info["dc_name"]
        cluster_name = self._cluster_info["cluster_name"]
        cpu_type = self._cluster_info["cpu_type"]
        self._rhvm.create_cluster(dc_name, cluster_name, cpu_type)
        time.sleep(5)

    def _setup_ifcfg_network_ip(self):
        log.info("Setting up the network by ifcfg files")
        if re.search("bondi", self.ksfile):
            self._set_ifcfg_bond()
        elif re.search("vlani", self.ksfile):
            self._set_ifcfg_vlan()
        else:
            self._set_ifcfg_bv()
        host_ip = self._get_network_ip()

        return host_ip

    def _get_network_ip(self):
        if re.search("vlan|bv", self.ksfile):
            cmd = "ls /etc/sysconfig/network-scripts | egrep 'ifcfg-.*\.' | awk -F '-' '{print $2}'"
        else:
            cmd = "ls /etc/sysconfig/network-scripts | egrep 'ifcfg-bond[0-9]$' | awk -F '-' '{print $2}'"
        # Get the device
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if not ret[0]:
            raise RuntimeError("Faile to get the network device")
        device = ret[1]

        # get ip addr:
        cmd = "ip -f inet addr show %s|grep inet|awk '{print $2}'|awk -F'/' '{print $1}'" % device
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if not ret[0]:
            raise RuntimeError(
                "Failed to get the ip address of device %s" % device)
        return ret[1]

    def _get_host_ip(self):
        if re.search("bondi|vlani|bvi", self.ksfile):
            host_ip = self._setup_ifcfg_network_ip()
        elif re.search("bonda|vlana|bva", self.ksfile):
            host_ip = self._get_network_ip()
        else:
            host_ip = self.host_string

        return host_ip

    def _get_host_pass(self):
        host_pass = MACHINE_INFO[self.beaker_name]['password']
        return host_pass

    def _get_host_info(self):
        host_ip = self._get_host_ip()

        self._host_info.update({"host_ip": host_ip})

        scen = self.ksfile.split('_')[1]
        host_name = host_name_tpl.replace('tpl', scen)
        self._host_info.update({"host_name": host_name})

        host_pass = self._get_host_pass()
        self._host_info.update({"host_pass": host_pass})

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
            time.sleep(10)
            i += 1

    def _update_network_vlan_tag(self):
        log.info("Updating network of datacenter with vlan tag")
        dc_name = self._dc_info["dc_name"]
        vlan_id = self._vlanid
        self._rhvm.update_dc_network(
            dc_name, "ovirtmgmt", key="vlan", value=vlan_id)
        time.sleep(5)

    def _update_network_name(self, mgmt_name):
        log.info("Updating network of datacenter with custom name")
        dc_name = self._dc_info["dc_name"]
        self._rhvm.update_dc_network(
            dc_name, "ovirtmgmt", key="name", value=mgmt_name)
        time.sleep(5)

    ##########################################
    # CheckPoint ca0_create_new_host_check
    ##########################################
    def ca0_create_new_host_check(self):
        log.info("Checking host can be added...")
        try:
            self._get_host_info()

            host_ip = self._host_info["host_ip"]
            host_name = self._host_info["host_name"]
            host_pass = self._host_info["host_pass"]
            cluster_name = self._cluster_info["cluster_name"]

            if self._vlanid:
                self._update_network_vlan_tag()

            if re.search("vlani", self.ksfile):
                # Change the default ovitgmgmt name
                mgmt_name = "atvmgmt"
                self._update_network_name(mgmt_name)

            self._rhvm.create_new_host(
                host_ip, host_name, host_pass, cluster_name)

            self._wait_host_status(host_name, 'up')
        except Exception as e:
            log.exception(e)
            return False

        return True

    ##########################################
    # CheckPoint cl2_include_rhgs_pkg_check
    ##########################################
    def cl2_include_rhgs_pkg_check(self):
        log.info("Checking the rhgs server package is included in rhvh")
        cmd = "rpm -qa|grep glusterfs|wc -l"
        ret = self.remotecmd.run_cmd(cmd)
        if not ret[0]:
            log.error("RHGS package is not complete")
            return False
        cmd = "service glusterd status|grep Active"
        ret = self.remotecmd.run_cmd(cmd)
        if ret[0] and re.search("(running)", ret[1]):
            return True
        else:
            log.error("glusterd service is not running")
            return False

    def cl3_fcoe_service_check(self):
        log.info("Checking the fcoe related service is running")
        ck_services = ["fcoe.service", "lldpad.service", "lldpad.service"]
        for ck_service in ck_services:
            cmd = "service %s status" % ck_service
            ret = self.remotecmd.run_cmd(cmd)
            if ret[0] and re.search("(running)", ret[1]):
                continue
            else:
                log.error("%s service is not running" % ck_service)
                return False
        return True

    def _get_sd_info(self):
        scen = self.ksfile.split('_')[1]
        sd_name = sd_name_tpl.replace('tpl', scen)
        isd_name = isd_name_tpl.replace('tpl', scen)
        self._sd_info.update({"sd_name": sd_name})
        self._sd_info.update({"isd_name": isd_name})
        if re.search("local", self.ksfile):
            data_path = MACHINE_INFO[self.beaker_name]["local"]["data_path"]
            self._sd_info.update({
                "storage_type": "localfs",
                "data_path": data_path})
        elif re.search("nfs", self.ksfile):
            nfs_ip = NFS_INFO["ip"]
            nfs_password = NFS_INFO["password"]
            nfs_data_path = NFS_INFO["data_path"]
            nfs_iso_path = NFS_INFO["iso_path"]
            self._sd_info.update({
                "storage_type": "nfs",
                "nfs_ip": nfs_ip,
                "nfs_password": nfs_password,
                "nfs_data_path": nfs_data_path,
                "nfs_iso_path": nfs_iso_path})
        elif re.search("fc", self.ksfile):
            boot_lun = MACHINE_INFO[self.beaker_name]["fc"]["boot_lun"]
            avl_luns = MACHINE_INFO[self.beaker_name]["fc"]["avl_luns"]
            self._sd_info.update({
                "storage_type": "fcp",
                "boot_lun": boot_lun,
                "avl_luns": avl_luns})
        else:
            boot_lun = MACHINE_INFO[self.beaker_name]["scsi"]["boot_lun"]
            avl_luns = MACHINE_INFO[self.beaker_name]["scsi"]["avl_luns"]
            lun_addr = MACHINE_INFO[self.beaker_name]["scsi"]["lun_address"]
            lun_port = MACHINE_INFO[self.beaker_name]["scsi"]["lun_port"]
            lun_target = MACHINE_INFO[self.beaker_name]["scsi"]["lun_target"]
            self._sd_info.update({
                "storage_type": "iscsi",
                "boot_lun": boot_lun,
                "avl_luns": avl_luns,
                "lun_addr": lun_addr,
                "lun_port": lun_port,
                "lun_target": lun_target})

    def _create_local_data_path(self, data_path):
        log.info("Creating the local data path")
        cmd = "test -r %s" % data_path
        ret = self.remotecmd.run_cmd(cmd)
        if not ret[0]:
            cmd = "mkdir -p %s" % data_path
            self.remotecmd.run_cmd(cmd)
        else:
            cmd = "rm -rf %s/*" % data_path
            self.remotecmd.run_cmd(cmd)
        cmd = "chmod 777 %s" % data_path
        ret = self.remotecmd.run_cmd(cmd)
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
            host_name = self._host_info['host_name']
            self._get_sd_info()
            sd_name = self._sd_info['sd_name']
            storage_type = self._sd_info['storage_type']
            if not storage_type == "localfs":
                raise RuntimeError(
                    "Storage type is %s, not localfs" % storage_type)

            # Create local data directory
            data_path = self._sd_info['data_path']
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
            raise RuntimeError(
                "Failed to cleanup the nfs path %s" % nfs_data_path)

    def _create_nfs_storage_domain(self, sd_name, sd_type, nfs_ip, nfs_data_path, host_name):
        log.info("Creating the nfs storage domain")
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
            host_name = self._host_info['host_name']
            self._get_sd_info()
            sd_name = self._sd_info['sd_name']
            sd_type = 'data'
            dc_name = self._dc_info['dc_name']
            storage_type = self._sd_info['storage_type']
            if not storage_type == "nfs":
                raise RuntimeError(
                    "Storage type is %s, not nfs" % storage_type)

            # Clean the nfs path
            nfs_ip = NFS_INFO["ip"]
            nfs_passwd = NFS_INFO["password"]
            nfs_data_path = NFS_INFO["data_path"][0]
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
            host_name = self._host_info['host_name']
            self._get_sd_info()
            isd_name = self._sd_info['isd_name']
            sd_type = 'iso'
            dc_name = self._dc_info['dc_name']
            storage_type = self._sd_info['storage_type']
            if not storage_type == "nfs":
                raise RuntimeError(
                    "Storage type is %s, not nfs" % storage_type)

            # Clean the nfs path
            nfs_ip = NFS_INFO["ip"]
            nfs_passwd = NFS_INFO["password"]
            nfs_iso_path = NFS_INFO["iso_path"][0]
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
        ret = self.remotecmd.run_cmd(cmd)
        if ret[0] and ret[1]:
            vg = ret[1].split()[1]
        else:
            # If there is lvm on the lun, get the vg from lvm
            cmd = "lsblk -l %s|grep lvm|awk '{print $1}'" % pv
            ret = self.remotecmd.run_cmd(cmd)
            if ret[0] and ret[1]:
                alvm_blk = ret[1].split()[0]
                new_alvm_blk = alvm_blk.replace("--", "##")
                alvm_prefix = new_alvm_blk.split('-')[0]
                vg = alvm_prefix.replace("##", "-")

            # If there is partition on the lun, get all of them
            cmd = "lsblk -l %s|grep 'part'|awk '{print $1}'" % pv
            ret = self.remotecmd.run_cmd(cmd)
            if ret[0]:
                for blk_part in ret[1].split():
                    lun_parts.append("/dev/mapper/" + blk_part)

        # Delete the lun
        cmd = "dd if=/dev/zero of=%s bs=50M count=10" % pv
        self.remotecmd.run_cmd(cmd)

        # Delete the partition if exists
        if lun_parts:
            for lun_part in lun_parts:
                cmd = "dd if=/dev/zero of=%s bs=50M count=10" % lun_part
                self.remotecmd.run_cmd(cmd)

        # Delete the vg if exists
        if vg:
            cmd = "dmsetup remove /dev/%s/*" % vg
            self.remotecmd.run_cmd(cmd)

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
            host_name = self._host_info['host_name']
            self._get_sd_info()
            sd_name = self._sd_info['sd_name']
            dc_name = self._dc_info['dc_name']
            storage_type = self._sd_info['storage_type']
            if not storage_type == "fcp":
                raise RuntimeError("Storage type is %s, not fc" % storage_type)

            # Clean the fc lun
            lun_id = self._sd_info["avl_luns"][0]
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
            host_name = self._host_info['host_name']
            self._get_sd_info()
            sd_name = self._sd_info['sd_name']
            dc_name = self._dc_info['dc_name']
            storage_type = self._sd_info['storage_type']
            if not storage_type == "iscsi":
                raise RuntimeError(
                    "Storage type is %s, not iscsi" % storage_type)

            # Clean the fc lun
            lun_id = self._sd_info["avl_luns"][0]
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

    def _get_network_info(self):
        if re.search("bondi", self.ksfile):
            if not MACHINE_INFO[self.beaker_name].get("bond", None):
                raise RuntimeError("%s not support bond test" %
                                   self.beaker_name)
            slaves = MACHINE_INFO[self.beaker_name]["bond"]["slaves"]
            self._network_info.update(
                {"network_mode": "bond", "slaves": slaves})

        if re.search("vlani", self.ksfile):
            if not MACHINE_INFO[self.beaker_name].get("vlan", None):
                raise RuntimeError("%s not support vlan test" %
                                   self.beaker_name)
            id = MACHINE_INFO[self.beaker_name]["vlan"]["id"]
            nics = MACHINE_INFO[self.beaker_name]["vlan"]["nics"]
            static_ip = MACHINE_INFO[self.beaker_name]["vlan"]["static_ip"]
            self._network_info.update({
                "network_mode": "vlan", "id": id, "nics": nics, "static_ip": static_ip})

        if re.search("bvi", self.ksfile):
            if not MACHINE_INFO[self.beaker_name].get("bv", None):
                raise RuntimeError("%s not support bv test" % self.beaker_name)
            bond_name = MACHINE_INFO[self.beaker_name]["bv"]["bond_name"]
            vlan_id = MACHINE_INFO[self.beaker_name]["bv"]["vlan_id"]
            slaves = MACHINE_INFO[self.beaker_name]["bv"]["slaves"]
            static_ip = MACHINE_INFO[self.beaker_name]["bv"]["static_ip"]
            self._network_info.update({
                "network_mode": "bv",
                "bond_name": bond_name,
                "vlan_id": vlan_id,
                "slaves": slaves,
                "static_ip": static_ip})
        return True

    def _get_ifcfg_str(self, network_mode):
        res = {}
        bootproto = "dhcp"
        if re.search("02", self.ksfile):
            bootproto = "static"

        if network_mode == "bond":
            bond_name = "bond0"
            slaves = self._network_info["slaves"]

            # Get the original ip nic
            cmd = "ip a s|grep %s" % self.host_string
            ret = self.remotecmd.run_cmd(cmd)
            primary_nic = ret[1].split()[-1]
            prefix = ret[1].split()[1].split('/')[-1]

            # Create the ifcfg file
            if bootproto == "dhcp":
                bond_ifcfg_str = """\
BONDING_OPTS="mode=active-backup miimon=100 primary={primary}"
BOOTPROTO="dhcp"
DEVICE="{device}"
IPV6INIT="no"
IPV6_AUTOCONF="no"
NM_CONTROLLED="no"
ONBOOT="yes"
PEERNTP="yes"
TYPE="Bond"\
                """.format(primary=primary_nic, device=bond_name)
            else:
                cmd = "ip r s|grep %s|grep default" % primary_nic
                ret = self.remotecmd.run_cmd(cmd)
                gateway = ret[1].split()[2]
                bond_ifcfg_str = """\
BONDING_OPTS="mode=active-backup miimon=100 primary={primary}"
BOOTPROTO="static"
DEVICE="{device}"
IPV6INIT="no"
IPV6_AUTOCONF="no"
NM_CONTROLLED="no"
ONBOOT="yes"
PEERNTP="yes"
TYPE="Bond"
IPADDR="{ipaddr}"
PREFIX="{prefix}"
GATEWAY="{gateway}"\
                """.format(
                    primary=primary_nic,
                    device=bond_name,
                    ipaddr=self.host_string,
                    prefix=prefix,
                    gateway=gateway)
            res.update({bond_name: bond_ifcfg_str})

            for slave in slaves:
                slave_ifcfg_str = """\
DEVICE="{device}"
MASTER="{bond}"
NM_CONTROLLED="no"
ONBOOT="yes"
SLAVE="yes"\
                """
                slave_ifcfg_str = slave_ifcfg_str.format(
                    device=slave, bond=bond_name)
                res.update({slave: slave_ifcfg_str})

        elif network_mode == "vlan":
            vlan_id = self._network_info["id"]
            nic = self._network_info["nics"][0]
            nic_vlan = nic + '.' + vlan_id

            nic_ifcfg_str = """\
DEVICE="{device}"
NM_CONTROLLED="no"
ONBOOT="yes"\
            """.format(device=nic)
            res.update({nic: nic_ifcfg_str})

            if bootproto == "dhcp":
                vlan_ifcfg_str = """\
BOOTPROTO="dhcp"
DEVICE="{device}"
IPV6INIT="no"
IPV6_AUTOCONF="no"
NM_CONTROLLED="no"
ONBOOT="yes"
PEERNTP="yes"
VLAN="yes"\
                """.format(device=nic_vlan)
            else:
                static_ip = self._network_info["static_ip"]
                prefix = "24"
                gateway = "192.168.%s.1" % vlan_id
                vlan_ifcfg_str = """\
BOOTPROTO="static"
DEVICE="{device}"
IPV6INIT="no"
IPV6_AUTOCONF="no"
NM_CONTROLLED="no"
ONBOOT="yes"
PEERNTP="yes"
VLAN="yes"
IPADDR="{ipaddr}"
PREFIX="{prefix}"
GATEWAY="{gateway}"\
                """.format(device=nic_vlan, ipaddr=static_ip, prefix=prefix, gateway=gateway)
            res.update({nic_vlan: vlan_ifcfg_str})

        else:  # This is for vlan over bond case
            bond_name = self._network_info["bond_name"]
            vlan_id = self._network_info["vlan_id"]
            slaves = self._network_info["slaves"]
            bv = bond_name + '.' + vlan_id

            bond_ifcfg_str = """\
BONDING_OPTS="mode=active-backup miimon=100"
DEVICE="{device}"
NM_CONTROLLED="no"
ONBOOT="yes"
TYPE="Bond"\
            """.format(device=bond_name)
            res.update({bond_name: bond_ifcfg_str})

            for slave in slaves:
                slave_ifcfg_str = """\
DEVICE="{device}"
MASTER="{bond}"
NM_CONTROLLED="no"
ONBOOT="yes"
SLAVE="yes"\
                """
                slave_ifcfg_str = slave_ifcfg_str.format(
                    device=slave, bond=bond_name)
                res.update({slave: slave_ifcfg_str})

            if bootproto == "dhcp":
                bv_ifcfg_str = """\
BOOTPROTO="dhcp"
DEVICE="{device}"
IPV6INIT="no"
IPV6_AUTOCONF="no"
NM_CONTROLLED="no"
ONBOOT="yes"
PEERNTP="yes"
VLAN="yes"\
                """.format(device=bv)
            else:
                static_ip = self._network_info["static_ip"]
                prefix = "24"
                gateway = "192.168.%s.1" % vlan_id

                bv_ifcfg_str = """\
BOOTPROTO="static"
DEVICE="{device}"
IPV6INIT="no"
IPV6_AUTOCONF="no"
NM_CONTROLLED="no"
ONBOOT="yes"
PEERNTP="yes"
VLAN="yes"
IPADDR="{ipaddr}"
PREFIX="{prefix}"
GATEWAY="{gateway}"\
                """.format(device=bv, ipaddr=static_ip, prefix=prefix, gateway=gateway)
            res.update({bv: bv_ifcfg_str})

        return res

    def _set_ifcfg_bond(self):
        self._get_network_info()
        if not self._network_info.get("network_mode", None) == "bond":
            raise RuntimeError("Not support to do bond test")

        ifcfg_str_dict = self._get_ifcfg_str("bond")

        # Create ifcfg-bond file
        from tempfile import mkstemp
        for dev, ifcfg_str in ifcfg_str_dict.items():
            s, tcfg = mkstemp()
            cmd = "echo '%s' > %s" % (ifcfg_str, tcfg)
            local(cmd)

            dcfg = "/etc/sysconfig/network-scripts/ifcfg-%s" % dev
            self.remotecmd.put_remote_file(tcfg, dcfg)

        # Restart the network
        cmd = "service network restart"
        ret = self.remotecmd.run_cmd(cmd, timeout=150)
        if not ret[0]:
            raise RuntimeError(ret[1])

    def _avoid_disc(self):
        # Add the route to avoid the disconnection from remote server
        cmd = "ip route list|grep default"
        ret = self.remotecmd.run_cmd(cmd)
        pub_gw = ret[1].split()[2]

        cmd = "ip route add 10.0.0.0/8 via %s" % pub_gw
        self.remotecmd.run_cmd(cmd)

    def _set_ifcfg_vlan(self):
        self._get_network_info()
        if not self._network_info.get("network_mode", None) == "vlan":
            raise RuntimeError("Not support to do vlan test")

        vlan_id = self._network_info["id"]
        nic = self._network_info["nics"][0]
        nic_vlan = nic + '.' + vlan_id

        ifcfg_str_dict = self._get_ifcfg_str("vlan")

        from tempfile import mkstemp
        for dev, ifcfg_str in ifcfg_str_dict.items():
            s, tcfg = mkstemp()
            cmd = "echo '%s' > %s" % (ifcfg_str, tcfg)
            local(cmd)

            dcfg = "/etc/sysconfig/network-scripts/ifcfg-%s" % dev
            self.remotecmd.put_remote_file(tcfg, dcfg)

        # Add a gateway to avoid the disconnection by restart the network
        self._avoid_disc()

        # Bring up the vlan ip, may create the internal default gateway
        cmd = "ifup %s" % nic_vlan
        ret = self.remotecmd.run_cmd(cmd, timeout=150)
        if not ret[0]:
            raise RuntimeError(ret[1])

    def _set_ifcfg_bv(self):
        self._get_network_info()
        if not self._network_info.get("network_mode", None) == "bv":
            raise RuntimeError("Not support to do bv test")

        ifcfg_str_dict = self._get_ifcfg_str("bv")

        # Create the ifcfg-dev file
        from tempfile import mkstemp
        for dev, ifcfg_str in ifcfg_str_dict.items():
            s, tcfg = mkstemp()
            cmd = "echo '%s' > %s" % (ifcfg_str, tcfg)
            local(cmd)

            dcfg = "/etc/sysconfig/network-scripts/ifcfg-%s" % dev
            self.remotecmd.put_remote_file(tcfg, dcfg)

        # Add a gateway to avoid the disconnection by restart the network
        self._avoid_disc()

        # Bring up the vlan ip, may create the internal default gateway
        cmd = "service network restart"
        ret = self.remotecmd.run_cmd(cmd, timeout=150)
        if not ret[0]:
            raise RuntimeError(ret[1])

    def _get_vm_info(self):
        scen = self.ksfile.split('_')[1]
        vm_name = vm_name_tpl.replace('tpl', scen)
        self._vm_info.update({"vm_name": vm_name})

    def _create_vm(self):
        log.info("Creating a VM")
        self._get_vm_info()
        vm_name = self._vm_info["vm_name"]
        cluster_name = self._cluster_info["cluster_name"]
        self._rhvm.create_vm(vm_name=vm_name, cluster=cluster_name)
        time.sleep(30)

    def _get_disk_info(self):
        scen = self.ksfile.split('_')[1]
        disk0_name = disk0_name_tpl.replace('tpl', scen)
        disk0_type = self._sd_info["storage_type"]
        self._disk_info.update({"disk0":
                                {"disk_name": disk0_name,
                                 "disk_type": disk0_type}
                                })
        if disk0_type == "localfs" or disk0_type == "nfs":
            disk_size = "30589934592"
            self._disk_info["disk0"].update({"disk_size": disk_size})
        else:
            disk1_name = disk1_name_tpl.replace('tpl', scen)
            disk1_type = self._sd_info["storage_type"]
            self._disk_info.update({"disk1":
                                    {"disk_name": disk1_name,
                                     "disk_type": disk1_type}
                                    })
            if disk0_type == "fcp":
                lun_addr = ""
                lun_port = ""
                lun_target = ""
                lun_id = MACHINE_INFO[self.beaker_name]["fc"]["avl_luns"][1]
                second_lun_id = MACHINE_INFO[self.beaker_name]["fc"]["avl_luns"][2]
            else:  # This is "iscsi" type
                lun_id = MACHINE_INFO[self.beaker_name]["scsi"]["avl_luns"][1]
                lun_addr = MACHINE_INFO[self.beaker_name]["scsi"]["lun_address"]
                lun_port = MACHINE_INFO[self.beaker_name]["scsi"]["lun_port"]
                lun_target = MACHINE_INFO[self.beaker_name]["scsi"]["lun_target"]
                second_lun_id = MACHINE_INFO[self.beaker_name]["scsi"]["avl_luns"][2]
            self._disk_info["disk0"].update({"lun_id": lun_id})
            self._disk_info["disk0"].update({"lun_addr": lun_addr})
            self._disk_info["disk0"].update({"lun_port": lun_port})
            self._disk_info["disk0"].update({"lun_target": lun_target})
            self._disk_info["disk1"].update({"lun_id": second_lun_id})
            self._disk_info["disk1"].update({"lun_addr": lun_addr})
            self._disk_info["disk1"].update({"lun_port": lun_port})
            self._disk_info["disk1"].update({"lun_target": lun_target})

    def _create_float_disk(self, flag):
        """
        Create a float disk for vm using
        :param flag: "disk0" or "disk1"
        :return:
        """
        log.info("Creating a float disk for VM")
        self._get_disk_info()
        disk_name = self._disk_info[flag]["disk_name"]
        disk_type = self._disk_info[flag]["disk_type"]
        sd_name = self._sd_info["sd_name"]
        host_name = self._host_info["host_name"]
        if disk_type == "localfs" or disk_type == "nfs":
            disk_size = self._disk_info[flag]["disk_size"]
            self._rhvm.create_float_image_disk(sd_name, disk_name, disk_size)
        else:
            lun_id = self._disk_info[flag]["lun_id"]
            lun_addr = self._disk_info[flag]["lun_addr"]
            lun_port = self._disk_info[flag]["lun_port"]
            lun_target = self._disk_info[flag]["lun_target"]

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
        vm_name = self._vm_info["vm_name"]
        disk_name = self._disk_info[flag]["disk_name"]
        self._rhvm.attach_disk_to_vm(disk_name, vm_name, bootable=bootable)
        time.sleep(30)

    ##########################################
    # CheckPoint cv1_create_vm_with_disk_check
    ##########################################
    def cv1_create_vm_with_disk_check(self):
        log.info("Checking the disk can be added to vm...")
        try:
            # Create the vm
            self._create_vm()

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
                log.error("VM status is %s, not %s" %
                          (vm_status, expect_status))
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
            vm_name = self._vm_info["vm_name"]
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
            vm_name = self._vm_info["vm_name"]
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
            host_name = self._host_info["host_name"]

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
            host_name = self._host_info["host_name"]
            self._rhvm.remove_host(host_name)
        except Exception as e:
            log.exception(e)
            return False
        return True

    #################################################
    # Before checking, create the datacenter, cluster
    #################################################
    def _setup_before_check(self):
        log.info("Setup before check...")

        try:
            self._get_rhvm()

            # Create datacenter
            self._create_datacenter()

            # Creating cluster
            self._create_cluster()

        except Exception as e:
            log.exception(e)
            return False
        return True

    #################################################
    # After checking, remove the cluster, datacenter
    #################################################
    def _teardown_after_check(self):
        log.info("Teardown after check...")
        try:
            dc_name = self._dc_info.get("dc_name", None)
            cluster_name = self._cluster_info.get("cluster_name", None)
            host_name = self._host_info.get("host_name", None)
            isd_name = self._sd_info.get("isd_name", None)
            vm_name = self._vm_info.get("vm_name", None)

            if vm_name and self._rhvm.list_vm(vm_name):
                log.info("Removing vm %s..." % vm_name)
                self._rhvm.remove_vm(vm_name)

            if host_name and self._rhvm.list_host(host_name):
                log.info("Maintenance host...")
                self._rhvm.deactive_host(host_name)
                time.sleep(60)

            if isd_name and self._rhvm.list_storage_domain(isd_name):
                log.info("Removing iso domain...")
                self._rhvm.remove_storage_domain(isd_name, host_name)
                time.sleep(5)

            if dc_name and self._rhvm.list_datacenter(dc_name):
                log.info("Force removing datacenter...")
                self._rhvm.remove_datacenter(dc_name, force=True)

            if host_name and self._rhvm.list_host(host_name):
                log.info("Removing host...")
                self._rhvm.remove_host(host_name)

            if cluster_name and self._rhvm.list_cluster(cluster_name):
                log.info("Removing cluster...")
                self._rhvm.remove_cluster(cluster_name)
        except Exception as e:
            log.exception(e)

    def run_cases(self):
        cks = {}
        try:
            # get checkpoint cases map
            disorder_checkpoint_cases_map = self.casesmap.get_checkpoint_cases_map(
                self.ksfile, self.beaker_name)
            checkpoint_cases_map_list = sorted(
                disorder_checkpoint_cases_map.items(), key=lambda item: item[0])

            # run check
            log.info("Start to run check points, please wait...")

            for l in checkpoint_cases_map_list:
                checkpoint = l[0]
                cases = l[1]
                self.run_checkpoint(checkpoint, cases, cks)
        except Exception as e:
            log.exception(e)

        return cks

    def run_checkpoint(self, checkpoint, cases, cks):
        try:
            log.info("Start to run checkpoint:%s for cases:%s",
                     checkpoint, cases)
            ck = self.call_func_by_name(checkpoint)
            if ck:
                newck = 'passed'
            else:
                newck = 'failed'
            for case in cases:
                if not re.search("RHEVM-[0-9]+", case):
                    continue
                cks[case] = newck
        except Exception as e:
            log.error(e)
        finally:
            log.info("Run checkpoint:%s for cases:%s finished.",
                     checkpoint, cases)

    def go_check(self):
        self.remotecmd.disconnect()

        is_setup_success = self._setup_before_check()

        cks = self.run_cases() if is_setup_success else {}

        self._teardown_after_check()

        return cks


def log_cfg_for_unit_test():
    from utils import ResultsAndLogs
    logs = ResultsAndLogs()
    logs.logger_name = "unit_test.log"
    logs.img_url = "vdsm/test"
    logs.get_actual_logger("vdsm")


if __name__ == '__main__':
    log_cfg_for_unit_test()
    log = logging.getLogger('bender')

    ck = CheckVdsm()
    ck.host_string, ck.host_user, ck.host_pass = ('10.73.73.17', 'root',
                                                  'redhat')
    ck.build = 'redhat-virtualization-host-4.1-20170531.0'
    ck.beaker_name = 'dell-per515-01.lab.eng.pek2.redhat.com'
    ck.ksfile = 'atv_bondi_02.ks'

    print ck.go_check()
