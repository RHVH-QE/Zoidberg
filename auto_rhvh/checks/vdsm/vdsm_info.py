import logging
import re
import time
import functools
from fabric.api import settings, run, local
from ..check_comm import CheckComm
from ..vdsmapi import RhevmAction
from consts_vdsm import RHVM_INFO, MACHINE_INFO, NFS_INFO

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


class VdsmInfo(object):
    """"""
    def __init__(self):
        self._build = None  # redhat-virtualization-host-4.1-20170531.0
        self._remotecmd = None
        self._ksfile = None

        self.rhvm_info = {}  # {"rhvm_fqdn": rhvm41-vlan50-1.lab.eng.pek2.redhat.com, "vlan_id": 50}
        self.rhvm = None
        self.host_info = {}  # {"host_ip": host_ip, "host_pass": host_pass, "host_name": vdsm_fc_host}
        self.storage_info = {}  # {"storage_type": "localfs", "data_path": "/home/data"}
        self.network_info = {}  # {"network_type": bond, "slaves": [nic1, nic2]}
        self.vm_info = {}  # {"vm_name": vm_name}
        self.disk_info = {}  # {"disk0": {"disk_name": disk0_name, "disk_type": disk0_type}}

    @property
    def build(self):
        return self._build

    @build.setter
    def build(self, val):
        self._build = val

    @property
    def remotecmd(self):
        return self._remotecmd

    @remotecmd.setter
    def remotecmd(self, val):
        self._remotecmd = val

    @property
    def ksfile(self):
        return self._ksfile

    @ksfile.setter
    def ksfile(self, val):
        self._ksfile = val

    @property
    def beaker_name(self):
        return self._beaker_name

    @beaker_name.setter
    def beaker_name(self, val):
        self._beaker_name = val

    ###################################################################
    # rhvm info:
    # {
    #   "rhvm_fqdn": rhvm41-vlan50-1.lab.eng.pek2.redhat.com, 
    #   "vlan_id": 50,
    #   "dc_name": vdsm_fc_dc, 
    #   "is_local": False,
    #   "cluster_name": cluster_name, 
    #   "cpu_type": "AMD Opteron G1"
    # }
    ###################################################################
    def _get_rhvm_info(self):
        self._get_host_vlanid()
        self._get_rhvm_fqdn()
        self.rhvm = RhevmAction(self.rhvm_info["rhvm_fqdn"])

        self._get_dc_info()
        self._get_cluster_info()

    def _get_host_version(self):
        BUILD_4_0 = "-4.0-"
        BUILD_4_1 = "-4.1-"
        BUILD_4_2 = "-4.2-"
        if BUILD_4_0 in self._build:
            build_ver = "40"
        elif BUILD_4_1 in self._build:
            build_ver = "41"
        elif BUILD_4_2 in self._build:
            build_ver = "42"
        else:
            build_ver = None
        return build_ver

    def _get_host_vlanid(self):
        if re.search("vlan|bv", self.ksfile):
            if MACHINE_INFO[self.beaker_name].get('vlan', None):
                vlan_id = MACHINE_INFO[self.beaker_name]['vlan']['id']
            else:
                if MACHINE_INFO[self.beaker_name].get('bv', None):
                    vlan_id = MACHINE_INFO[self.beaker_name]['bv']['vlan_id']
            
            self.rhvm_info.update({"vlan_id": vlan_id})

    def _get_rhvm_fqdn(self):
        build_ver = self._get_host_version()
        if not build_ver:
            raise RuntimeError("The version of host build is not 4.0/4.1/4.2")
        else:
            bv_key = build_ver

        vi_key = "50"  # Default to use vlan50 rhvm
        vlan_id = self.rhvm_info.get("vlan_id", None)
        if vlan_id:
            vi_key = vlan_id

        k1 = rhvm_fqdn_tpl.replace('x', bv_key)
        k2 = k1.replace('y', vi_key)
        rhvm_fqdn = RHVM_INFO.get(k2)

        self.rhvm_info.update({"rhvm_fqdn": rhvm_fqdn})

    def _get_dc_info(self):
        scen = self.ksfile.split('_')[1]
        dc_name = datacenter_name_tpl.replace('tpl', scen)
        is_local = False
        if re.search('local', self.ksfile):
            is_local = True
        self.rhvm_info.update({"dc_name": dc_name, "is_local": is_local})

    def _get_cluster_info(self):
        AMD_CPU = "AMD"
        INTEL_CPU = "Intel"

        scen = self.ksfile.split('_')[1]
        cluster_name = cluster_name_tpl.replace('tpl', scen)
        self.rhvm_info.update({"cluster_name": cluster_name})

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
        self.rhvm_info.update({"cpu_type": cpu_type})

    ###################################################################
    # network info:
    # {
    #   "network_mode": bond, 
    #   "slaves": [nic1, nic2]
    # }
    ###################################################################
    def _get_network_info(self):
        if re.search("bondi", self.ksfile):
            if not MACHINE_INFO[self.beaker_name].get("bond", None):
                raise RuntimeError("%s not support bond test" %
                                   self.beaker_name)
            slaves = MACHINE_INFO[self.beaker_name]["bond"]["slaves"]
            self.network_info.update(
                {"network_mode": "bond", "slaves": slaves})

        if re.search("vlani", self.ksfile):
            if not MACHINE_INFO[self.beaker_name].get("vlan", None):
                raise RuntimeError("%s not support vlan test" %
                                   self.beaker_name)
            id = MACHINE_INFO[self.beaker_name]["vlan"]["id"]
            nics = MACHINE_INFO[self.beaker_name]["vlan"]["nics"]
            static_ip = MACHINE_INFO[self.beaker_name]["vlan"]["static_ip"]
            self.network_info.update({
                "network_mode": "vlan", "id": id, "nics": nics, "static_ip": static_ip})

        if re.search("bvi", self.ksfile):
            if not MACHINE_INFO[self.beaker_name].get("bv", None):
                raise RuntimeError("%s not support bv test" % self.beaker_name)
            bond_name = MACHINE_INFO[self.beaker_name]["bv"]["bond_name"]
            vlan_id = MACHINE_INFO[self.beaker_name]["bv"]["vlan_id"]
            slaves = MACHINE_INFO[self.beaker_name]["bv"]["slaves"]
            static_ip = MACHINE_INFO[self.beaker_name]["bv"]["static_ip"]
            self.network_info.update({
                "network_mode": "bv",
                "bond_name": bond_name,
                "vlan_id": vlan_id,
                "slaves": slaves,
                "static_ip": static_ip})
        return True

    #####################################################################
    # host info:
    # {
    #   "host_ip": host_ip, 
    #   "host_pass": host_pass, 
    #   "host_name": vdsm_fc_host
    # }
    #####################################################################
    def _get_host_info(self):
        host_ip = self._get_host_ip()

        self.host_info.update({"host_ip": host_ip})

        scen = self.ksfile.split('_')[1]
        host_name = host_name_tpl.replace('tpl', scen)
        self.host_info.update({"host_name": host_name})

        host_pass = self._get_host_pass()
        self.host_info.update({"host_pass": host_pass})

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
        if not self.network_info.get("network_mode", None) == "bond":
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
        if not self.network_info.get("network_mode", None) == "vlan":
            raise RuntimeError("Not support to do vlan test")

        vlan_id = self.network_info["id"]
        nic = self.network_info["nics"][0]
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
        if not self.network_info.get("network_mode", None) == "bv":
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

    ##############################################################
    # storage_info:
    # {"storage_type": "localfs", "data_path": "/home/data"}
    ##############################################################
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

    ##############################################################
    # vm info:
    # {"vm_name": vm_name}
    ##############################################################
    def _get_vm_info(self):
        scen = self.ksfile.split('_')[1]
        vm_name = vm_name_tpl.replace('tpl', scen)
        self._vm_info.update({"vm_name": vm_name})

    ##############################################################
    # disk info:
    # {"disk0": {"disk_name": disk0_name, "disk_type": disk0_type}}
    ##############################################################
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

    def get(self):
        self._get_rhvm_info()
        self._get_network_info()
        self._get_host_info()
        self._get_storage_info()
        self._get_disk_info()
        self._get_vm_info()
