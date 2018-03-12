#
# RHVM FQDN
#
RHVM_INFO = {
    "rhvm40_vlan20_fqdn": "rhvm40-vlan20-2.lab.eng.pek2.redhat.com",
    "rhvm40_vlan50_fqdn": "rhvm40-vlan50-2.lab.eng.pek2.redhat.com",
    "rhvm41_vlan20_fqdn": "rhvm41-vlan20-2.lab.eng.pek2.redhat.com",
    "rhvm41_vlan50_fqdn": "rhvm41-vlan50-2.lab.eng.pek2.redhat.com",
    "rhvm42_vlan20_fqdn": "vm-74-225.lab.eng.pek2.redhat.com",
    "rhvm42_vlan50_fqdn": "vm-73-209.lab.eng.pek2.redhat.com"
}

#
# Info for NFS to be used in test_nfs
#
NFS_INFO = {
    "ip": "10.66.148.11",
    "password": "redhat",
    "data_path": ["/home/dguo/atv/data"],
    "iso_path": ["/home/dguo/atv/iso"]
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
