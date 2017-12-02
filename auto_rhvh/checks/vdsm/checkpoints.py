import logging
import re

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
            time.sleep(10)
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
            host_ip = self._vdsm_info.host_info["host_ip"]
            host_name = self._vdsm_info.host_info["host_name"]
            host_pass = self._vdsm_info.host_info["host_pass"]
            dc_name = self._vdsminfo.rhvm_info["dc_name"]
            cluster_name = self._vdsm_info.rhvm_info["cluster_name"]
            vlan_id = self._vdsminfo.rhvm_info.get("vlan_id", None)

            if vlanid:
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