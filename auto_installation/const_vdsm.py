from constants import DELL_PER510_01, DELL_PER515_01

#
# Cases remained to be automated or could not be automated
#
VDSM_NOT_AUTOMATED_MAP = {
    "RHEVM-18121": (
        "Create VMs on rhvh from rhvm side successfully after add rhvh to rhvm",
        "Half automation",
        "Reason: Half automated since the OS can not be installed automatically"
    ),
    "RHEVM-18124": (
        "rhvh info check in rhvm",
        "Needs to do"
        "Not easy to compare the rhevh info"
    ),
    "RHEVM-18125": (
        "Verify engine-iso-uploader works good",
        "Needs to do"
        "Needs to answer the password of engine"
    ),
    "RHEVM-18126": (
        "Verify VM migration successful",
        "Can not"
        "Needs two server"
    ),
    "RHEVM-18129": (
        "VM boot from PXE",
        "Can not",
        "Can not chose PXE boot for vm installation"
    ),
    "RHEVM-18133": (
        "Add one FC direct lun disk to VM",
        "Still needs to debug",
        "Still has bug"
    ),
    "RHEVM-18134": (
        "Add one iscsi direct lun disk to VM",
        "Still needs to debug",
        "Still has bug"
    ),
    "RHEVM-18138": (
        "The rhvh's firewall ports were enabled by default after adding to rhvm",
        "Needs to do",
        "Not easy to compare"
    ),
    "RHEVM-19736": (
        "Imgbase layout check on rhvh with a large number of LUNs attached",
        "Needs to do",
        "Needs to create 1000+ lvms"
    )
}

VDSM_TIER_TESTCASE_MAP = {  # sequential cases for each scenario
    "RHEVM-18113": ('atv_local-vlani_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18114": ('atv_local-vlani_01.ks', DELL_PER515_01, 'cl1_create_local_sd_check'),
    "RHEVM-18197": ('atv_local-vlani_01.ks', DELL_PER515_01, 'cl2_include_rhgs_pkg_check'),
    "RHEVM-18136": ('atv_local-vlani_01.ks', DELL_PER515_01, 'cl3_fcoe_service_check'),
    "RHEVM-18118": ('atv_local-vlani_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18135": ('atv_local-vlani_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18117": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18137": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18120": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cn1_create_nfs_sd_check'),
    "RHEVM-18128": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cn2_create_iso_sd_check'),
    "RHEVM-18121": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cv1_create_vm_with_disk_check'),
    "RHEVM-18122": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cv3_vm_life_cycle_check'),
    "RHEVM-18130": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cv9_delete_vm_check'),
    "RHEVM-18123": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cz1_maintenance_host_check'),
    "RHEVM-18127": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cz2_remove_host_check'),
    "RHEVM-invalid1": ('atv_scsi_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),  # must install host before check
    "RHEVM-18115": ('atv_scsi_01.ks', DELL_PER515_01, 'cs1_create_scsi_sd_check'),
    "RHEVM-18132": ('atv_scsi_01.ks', DELL_PER515_01, 'cv1_create_vm_with_disk_check'),
    "RHEVM-18119": ('atv_bvi_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18156": ('atv_bonda_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18160": ('atv_vlana_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18157": ('atv_bva_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-invalid2": ('atv_fc_01.ks', DELL_PER510_01, 'ca0_create_new_host_check'),  # must install host before check
    "RHEVM-18116": ('atv_fc_01.ks', DELL_PER510_01, 'cf1_create_fc_sd_check'),
    "RHEVM-18131": ('atv_fc_01.ks', DELL_PER510_01, 'cv1_create_vm_with_disk_check'),
}

#
# RHVM FQDN
#
RHVM_INFO = {
    "rhvm40_vlan50_fqdn": "rhvm40-vlan50-1.lab.eng.pek2.redhat.com",
    "rhvm41_vlan50_fqdn": "rhvm41-vdsm-auto.lab.eng.pek2.redhat.com",
    "rhvm40_vlan20_fqdn": "rhvm40-vlan20-1.lab.eng.pek2.redhat.com",
    "rhvm41_vlan20_fqdn": "rhvm41-vlan20-1.lab.eng.pek2.redhat.com"
}

#
# Info for NFS to be used in test_nfs
#
NFS_INFO = {
    "ip": "10.66.8.173",
    "password": "l1admin",
    "data_path": ["/home/dguo/Public/vdsm/data"],
    "iso_path": ["/home/dguo/Public/vdsm/iso"]
}

#
# Machines for test
#
MACHINE_INFO = {
    "dell-per515-01.lab.eng.pek2.redhat.com": {
        "ip": "10.73.73.17",
        "password": "redhat",
        "primary_nic": "em2",

        # For test_local
        "local": {"data_path": "/home/data"},

        # For test_scsi
        "scsi": {
            "boot_lun": ["360a9800050334c33424b41762d726954"],
            "avl_luns": [
                "360a9800050334c33424b41762d736d45",
                "360a9800050334c33424b41762d745551",
                "360a9800050334c33424b4a4b306a2d66"
            ],
            "lun_address": "10.73.194.25",
            "lun_port": "3260",
            "lun_target": "iqn.1992-08.com.netapp:sn.135053389"},

        # For test_bond/test_vlan/test_bv
        "bond": {"name": "bond0",
                 "slaves": ["em1", "em2"],
                 "em1": "08:9e:01:63:2c:b2",
                 "em2": "08:9e:01:63:2c:b3"},

        "vlan": {"id": "50",
                 "nics": ["p2p1", "p2p2"],
                 "static_ip": "192.168.50.48",
                 "p2p1": "00:1b:21:a6:64:6c",
                 "p2p2": "00:1b:21:a6:64:6d"},

        "bv": {"bond_name": "bond1",
               "vlan_id": "50",
               "slaves": ["p2p1", "p2p2"],
               "static_ip": "192.168.50.48",
               "p2p1": "00:1b:21:a6:64:6c",
               "p2p2": "00:1b:21:a6:64:6d"}
    },

    "dell-per510-01.lab.eng.pek2.redhat.com": {
        "ip": "10.73.73.35",
        "password": "redhat",
        "primary_nic": "eno1",

        # For test_local
        "local": {"data_path": "/home/data"},

        # For test_fc
        "fc": {
            "boot_lun": ["36005076300810b3e0000000000000022"],
            "avl_luns": [
                "36005076300810b3e0000000000000023",
                "36005076300810b3e0000000000000024",
                "36005076300810b3e0000000000000270"]
        }
    }
}
