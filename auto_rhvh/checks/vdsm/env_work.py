import logging
import time


log = logging.getLogger('bender')


class EnvWork(object):
    """"""
    def __init__(self, vdsminfo):
        self.vdsminfo = vdsminfo

    def setup(self):
        log.info("Setup before check...")

        dc_name = self.vdsminfo.rhvm_info["dc_name"]
        is_local = self.vdsminfo.rhvm_info["is_local"]
        cluster_name = self.vdsminfo.rhvm_info["cluster_name"]
        cpu_type = self.vdsminfo.rhvm_info["cpu_type"]
        rhvm = self.vdsminfo.rhvm

        try:
            self._create_datacenter(rhvm, dc_name, is_local)  # Creating datacenter

            self._create_cluster(rhvm, dc_name, cluster_name, cpu_type)  # Creating cluster

        except Exception as e:
            log.exception(e)
            return False
        return True

    def teardown(self):
        log.info("Teardown after check...")

        dc_name = self.vdsminfo.rhvm_info.get("dc_name", None)
        cluster_name = self.vdsminfo.rhvm_info.get("cluster_name", None)
        host_name = self.vdsminfo.host_info.get("host_name", None)
        sd_name = self.vdsminfo.storage_info.get("sd_name", None)
        isd_name = self.vdsminfo.storage_info.get("isd_name", None)
        vm_name = self.vdsminfo.vm_info.get("vm_name", None)
        rhvm = self.vdsminfo.rhvm

        try:
            self._remove_vm(rhvm, vm_name)  # Remove VM
            
            self._maintenance_host(rhvm, host_name)  # Maintenance Host

            self._remove_sd(rhvm, isd_name, host_name)  # Destroy iso domain

            self._remove_sd(rhvm, sd_name, host_name)  # Destroy data domain

            self._remove_host(rhvm, host_name)  # Remove host

            self._remove_cluster(rhvm, cluster_name)  # Remove cluster

            self._remove_dc(rhvm, dc_name)  # Remove Datacenter

        except Exception as e:
            log.exception(e)

    def _create_datacenter(self, rhvm, dc_name, is_local):
        log.info("Creating datacenter %s" % dc_name)
        rhvm.create_datacenter(dc_name, is_local)
        time.sleep(5)

    def _create_cluster(self, rhvm, dc_name, cluster_name, cpu_type):
        log.info("Creating cluster %s" % cluster_name)
        rhvm.create_cluster(dc_name, cluster_name, cpu_type)
        time.sleep(5)

    def _remove_vm(self, rhvm, vm_name):
        if vm_name and rhvm.list_vm(vm_name):
            log.info("Removing vm %s..." % vm_name)
            rhvm.remove_vm(vm_name)

    def _maintenance_host(self, rhvm, host_name):
        if host_name and rhvm.list_host(host_name):
            log.info("Maintenance host...")
            rhvm.deactive_host(host_name)
            time.sleep(60)

    def _remove_sd(self, rhvm, sd_name, host_name):
        if sd_name and rhvm.list_storage_domain(sd_name):
            log.info("Removing storage domain...")
            rhvm.remove_storage_domain(sd_name, host_name)
            time.sleep(5)

    def _remove_dc(self, rhvm, dc_name):
        if dc_name and rhvm.list_datacenter(dc_name):
            log.info("Force removing datacenter...")
            rhvm.remove_datacenter(dc_name, force=True)

    def _remove_host(self, rhvm, host_name):
        if host_name and rhvm.list_host(host_name):
            log.info("Removing host...")
            rhvm.remove_host(host_name)

    def _remove_cluster(self, rhvm, cluster_name):
        if cluster_name and rhvm.list_cluster(cluster_name):
            log.info("Removing cluster...")
            rhvm.remove_cluster(cluster_name)
