DELL_PET105_01 = 'dell-pet105-01.qe.lab.eng.nay.redhat.com'
DELL_PER510_01 = 'dell-per510-01.lab.eng.pek2.redhat.com'
DELL_OP790_01 = 'dell-op790-01.qe.lab.eng.nay.redhat.com'
DELL_PER515_01 = 'dell-per515-01.lab.eng.pek2.redhat.com'
DELL_PER515_02 = 'dell-per515-02.lab.eng.pek2.redhat.com'
DELL_PER740_28 = 'dell-per740-28.lab.eng.pek2.redhat.com'

HOSTS = {
    DELL_PET105_01: {
        "nic": {
            "macaddress-enp2s0": "00:22:19:27:54:c7"
        },
        "hostname": "",
        "static_ip": ""
    },
    DELL_PER510_01: {
        "nic": {
            "macaddress-eno2": "78:2b:cb:47:93:5e"
        },
        "hostname": "",
        "static_ip": ""
    },
    DELL_OP790_01: {
        "nic": {
            "macaddress-em1": "d4:be:d9:95:61:ca"
        },
        "hostname": "",
        "static_ip": ""
    },
    DELL_PER515_01: {
        "nic": {
            "macaddress-eno2": "08:9e:01:63:2c:b3"
        },
        "hostname": "",
        "static_ip": ""
    },
    DELL_PER515_02: {
        "nic": {
            "macaddress-em2": "08:9e:01:63:2c:6e"
        },
        "hostname": "",
        "static_ip": ""
    },
    DELL_PER740_28: {
        "nic": {
            "macaddress-eno1": "dc:f4:01:e4:f1:7c"
        },
        "hostname": "",
        "static_ip": ""
    }
}

'''
RHVM_DATA_MAP = {
    "4.0_rhvm_fqdn": "rhvm40-vlan50-1.lab.eng.pek2.redhat.com",
    "4.1_rhvm_fqdn": "rhvm41-vdsm-auto.lab.eng.pek2.redhat.com",
}
'''

DEBUG_TIER = 0x01
INSTALL_TIER1 = 0x02
INSTALL_TIER2 = 0x04
#KS_TIER1 = 0x08
#KS_TIER2 = 0x10
UPGRADE_TIER1 = 0x20
UPGRADE_TIER2 = 0x40
VDSM_TIER = 0x80

DEBUG_TIER_TESTCASE_MAP = {
    'RHEVM-23911': ('ati_fc_01.ks', DELL_PER510_01, 'PartitionCheck.partitions_check'),
}
