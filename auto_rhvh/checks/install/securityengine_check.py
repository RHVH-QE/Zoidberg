import logging
import os
import time
from ..helpers.rhvm_api import RhevmAction
import attr

log = logging.getLogger('bender')

DC_NAME = "security_engine_dc"
CLUSTER_NAME = "security_engine_cluster"
HOST_NAME = "security_engine_host"
RHVM_FQDN = "vm-197-117.lab.eng.pek2.redhat.com"


@attr.s
class SecurityEngineCheck(object):

    ##########################################
    # security_engine_check
    ##########################################

    remotecmd = attr.ib()
    expected_securityengine = attr.ib()
    
    def _add_host_to_rhvm(self):
        log.info("Add host to rhvm...")
        log.info(
            "rhvm: %s, datacenter: %s, cluster_name: %s, host_name: %s, host_ip: %s",
            RHVM_FQDN, DC_NAME, CLUSTER_NAME,
            HOST_NAME, self.remotecmd.host_string)

        try:
            self._rhvm = RhevmAction(RHVM_FQDN)

            self._del_host_on_rhvm()

            log.info("Add datacenter %s", DC_NAME)
            self._rhvm.add_datacenter(RHVM_FQDN)

            log.info("Add cluster %s", self._cluster_name)
            self._rhvm.add_cluster(RHVM_FQDN, CLUSTER_NAME, "undefined")

            log.info("Add host %s", self._host_name)
            self._rhvm.add_host(self.remotecmd.host_string, HOST_NAME, self.remotecmd.host_pass,
                                CLUSTER_NAME)

            log.info("Active host, please wait...")
            self._rhvm.active_host(HOST_NAME)
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

                host = self._rhvm.list_host(key="name", value=HOST_NAME)
                if host and (host.get('status') == 'up' or host.get('status') == 'non_operational'):
                    log.info("Try to maintenance host %s", HOST_NAME)
                    self._rhvm.deactive_host(HOST_NAME)
                    time.sleep(10)

                log.info("Try to remove host %s", HOST_NAME)
                self._rhvm.remove_host(HOST_NAME)
                self._rhvm.del_host_events(HOST_NAME)
                
                log.info("Try to remove cluster %s", CLUSTER_NAME)
                self._rhvm.remove_cluster(CLUSTER_NAME)

                log.info("Try to remove data_center %s", self._dc_name)
                self._rhvm.remove_datacenter(DC_NAME)
            except Exception as e:
                log.error(e)
                time.sleep(20)
                count = count + 1
            else:
                break


    def _check_openscap_config(self):
        cmd = "test -e {name} && grep 'configured = 1' {name}".format(name="/var/imgbased/openscap/config")
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if not ret[0]:
            log.error("Failed to get /var/imgbased/openscap/config.")
            return False
        if "configured = 1" in ret[1]:
            log.info("Get /var/imgbased/openscap/config successfully.")
            return True
        log.error("Failed to get /var/imgbased/openscap/config. The result of '%s' is '%s'", cmd, ret[1])
        return False


    def _check_host_status_on_rhvm(self):
        log.info("Check host status on rhvm.")
        
        count = 0
        while (count < 40):
            host = self._rhvm.list_host(key="name", value=HOST_NAME)
            if host and host.get('status') == 'up':
                break
            count = count + 1
            time.sleep(60)
        else:
            log.error("Host is not up on rhvm.")
            return False
        log.info("Host is up on rhvm.")
        return True


    def security_vdsm_check(self):
        log.info("In security mode, register rhvh via rhvm...")
        if self._check_openscap_config():
            return False
        if not self._add_host_to_rhvm():
            self._del_host_on_rhvm()
            return False
        if not self._check_host_status_on_rhvm():
            self._del_host_on_rhvm()
            return False
        self._del_host_on_rhvm()

        log.info("Register rhvh via rhvm with security profile selected finished.")
        return True
