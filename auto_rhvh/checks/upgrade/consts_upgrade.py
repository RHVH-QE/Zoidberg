import os

LOCAL_DIR = os.path.dirname(__file__)

CHECK_NEW_LVS = True

#RHVH_UPDATE_RPM_NAME = "redhat-virtualization-host-image-update-{}.el7_3.noarch.rpm"
RHVH_UPDATE_RPM_URL = "http://10.66.10.22:8090/rhvhupgrade/updates/"

KERNEL_SPACE_RPM_URL = ("http://download.eng.pek2.redhat.com/pub/rhel/rel-eng/RHEL-7.3-20161019.0/"
                        "compose/Server/x86_64/os/Packages/"
                        "kmod-oracleasm-2.0.8-17.el7.x86_64.rpm")

FABRIC_TIMEOUT = 300
YUM_UPDATE_TIMEOUT = 1200
YUM_INSTALL_TIMEOUT = 2400
CHK_HOST_ON_RHVM_STAT_MAXCOUNT = 40
CHK_HOST_ON_RHVM_STAT_INTERVAL = 60
ENTER_SYSTEM_MAXCOUNT = 10
ENTER_SYSTEM_INTERVAL = 60
ENTER_SYSTEM_TIMEOUT = 60

RHVM_DATA_MAP = {
    "4.0_rhvm_fqdn": "rhvm40-vlan50-2.lab.eng.pek2.redhat.com",
    "4.1_rhvm_fqdn": "vm-198-141.lab.eng.pek2.redhat.com",
    "4.2_rhvm_fqdn": "bootp-73-199-145.lab.eng.pek2.redhat.com",
    "4.3_rhvm_fqdn": "bootp-73-199-39.lab.eng.pek2.redhat.com",
    "4.4_rhvm_fqdn": "vm-198-19.lab.eng.pek2.redhat.com",
}

# Info for LVM to be used in RHEVM-27050(tier2)
# Modify this value according to the destination build, before running tier2 test case.
LVM_INFO = {
    "lv_name_of_destination_build": "rhvh-4.4.5.3-0.20210215.0+1",
}

#Info for NFS to be used in Storage
NFS_INFO = {
    "ip": "10.73.131.220",
    "password": "redhat",
    "data_path": "/home/nfs-rhel-data",
    "iso_path": "/home/nfs-rhel-iso",
}

# Info for local storage
LOCAL_STORAGE_INFO = {
    "local_data_path": "/local-storage-test",
}

#Info for disk to be used in VMs
DISK_INFO = {
    "size": "21474836480",
}

RHSM_INFO = {
    "username": "rhevh-qe",
    "password": "1234qwerP",
}

USER_RPMS = {
    "download_url_35": "http://download.eng.bos.redhat.com/brewroot/vol/rhel-8/packages/vdsm/4.40.35.1/1.el8ev/noarch/vdsm-hook-nestedvt-4.40.35.1-1.el8ev.noarch.rpm",
    "download_url_39": "http://download.eng.bos.redhat.com/brewroot/vol/rhel-8/packages/vdsm/4.40.39/1.el8ev/noarch/vdsm-hook-nestedvt-4.40.39-1.el8ev.noarch.rpm",
    "rpm_name_35": "vdsm-hook-nestedvt-4.40.35.1-1.el8ev.noarch.rpm",
    "rpm_name_39": "vdsm-hook-nestedvt-4.40.39-1.el8ev.noarch.rpm",
}
