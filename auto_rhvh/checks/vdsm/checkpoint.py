import logging


log = logging.getLogger('bender')


class CheckPoints(object):
    """"""

    def __init__(self):
        self._vdsminfo = None
        self._rhvm = None
    
    @property
    def vdsminfo(self):
        return self._vdsminfo

    @vdsminfo.setter
    def vdsminfo(self, val):
        self._vdsminfo = val

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
            host_ip = self._vdsm_info.host_info["host_ip"]
            host_name = self._vdsm_info.host_info["host_name"]
            host_pass = self._vdsm_info.host_info["host_pass"]
            cluster_name = self._vdsm_info.rhvm_info["cluster_name"]
            vlanid = self._vdsminfo.rhvm_info.get("vlan_id", None)

            if vlanid:
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
