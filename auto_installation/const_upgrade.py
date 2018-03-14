from constants import DELL_PET105_01, DELL_PER510_01, DELL_PER515_01

UPGRADE_TIER1_TESTCASE_MAP = {
    ##Tier1
    "RHEVM-18068": ('atu_yum_update.ks', DELL_PET105_01, 'basic_upgrade_check'),
    "RHEVM-18071": ('atu_yum_update.ks', DELL_PET105_01, 'packages_check'),
    "RHEVM-18072": ('atu_yum_update.ks', DELL_PET105_01, 'settings_check'),
    "RHEVM-18073": ('atu_yum_update.ks', DELL_PET105_01, 'roll_back_check'),
    "RHEVM-18077": ('atu_yum_update.ks', DELL_PET105_01, 'cannot_update_check'),
    "RHEVM-18082": ('atu_yum_update.ks', DELL_PET105_01, 'basic_upgrade_check'),
    "RHEVM-18093": ('atu_yum_update.ks', DELL_PET105_01, 'cmds_check'),
    "RHEVM-18104": ('atu_yum_update.ks', DELL_PET105_01, 'signed_check'),
    #"RHEVM-18211": ('atu_yum_update.ks', DELL_PET105_01, 'knl_space_rpm_check'),
    "RHEVM-18212": ('atu_yum_update.ks', DELL_PET105_01, 'usr_space_rpm_check'),
    "RHEVM-21647": ('atu_yum_update.ks', DELL_PET105_01, 'cmds_check'),
    "RHEVM-18069": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-18078": ('atu_yum_install.ks', DELL_PER510_01, 'cannot_install_check'),
    "RHEVM-18081": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-18089": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-21717": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
    #Tier2
    "RHEVM-18111": ('atu_yum_update.ks', DELL_PET105_01, 'avc_denied_check'),
    "RHEVM-22200": ('atu_yum_update.ks', DELL_PET105_01, 'iptables_status_check'),
    "RHEVM-22201": ('atu_yum_update.ks', DELL_PET105_01, 'ntpd_status_check'),
    "RHEVM-22202": ('atu_yum_update.ks', DELL_PET105_01, 'sysstat_check'),
    "RHEVM-22231": ('atu_yum_update.ks', DELL_PET105_01, 'ovirt_imageio_daemon_check'),
    "RHEVM-18094": ('atu_yum_update.ks', DELL_PET105_01, 'boot_dmesg_log_check'),
    "RHEVM-18102": ('atu_yum_update.ks', DELL_PET105_01, 'separate_volumes_check'),
    "RHEVM-18103": ('atu_yum_update.ks', DELL_PET105_01, 'etc_var_file_update_check'),
    "RHEVM-21347": ('atu_yum_install.ks', DELL_PER510_01, 'reinstall_rpm_check'),
    "RHEVM-22205": ('atu_yum_install.ks', DELL_PER510_01, 'packages_check'),
    "RHEVM-22204": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'update_again_unavailable_check'),
    "RHEVM-18106": ('atu_lack_space.ks', DELL_PET105_01, 'no_space_update_check'),
    "RHEVM-18079": ('atu_yum_update_vlan.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-22203": ('atu_yum_update.ks', DELL_PET105_01, 'kdump_check'),
}

UPGRADE_TIER2_TESTCASE_MAP = {
    "RHEVM-18080": ('atu_rhvm_iscsi.ks', DELL_PER515_01, 'basic_upgrade_check'),
    "RHEVM-18110": ('atu_yum_update.ks', DELL_PET105_01, 'delete_imgbase_check'),
    # #"RHEVM-18107": ('atu_yum_update.ks', DELL_PET105_01, 'fips_check'),
    # "RHEVM-18076": ('atu_yum_update_bond.ks', DELL_PER510_01, 'bond_check'),
}

RHVM_DATA_MAP = {
    "4.0_rhvm_fqdn": "rhvm40-vlan50-2.lab.eng.pek2.redhat.com",
    "4.1_rhvm_fqdn": "vm-74-201.lab.eng.pek2.redhat.com",
}

CHECK_NEW_LVS = True

#RHVH_UPDATE_RPM_NAME = "redhat-virtualization-host-image-update-{}.el7_3.noarch.rpm"
RHVH_UPDATE_RPM_URL = "http://10.66.10.22:8090/rhvhupgrade/updates/"

KERNEL_SPACE_RPM_URL = ("http://download.eng.pek2.redhat.com/pub/rhel/rel-eng/RHEL-7.3-20161019.0/"
                        "compose/Server/x86_64/os/Packages/"
                        "kmod-oracleasm-2.0.8-17.el7.x86_64.rpm")

FABRIC_TIMEOUT = 300
YUM_UPDATE_TIMEOUT = 1200
YUM_INSTALL_TIMEOUT = 1200
CHK_HOST_ON_RHVM_STAT_MAXCOUNT = 20
CHK_HOST_ON_RHVM_STAT_INTERVAL = 60
ENTER_SYSTEM_MAXCOUNT = 20
ENTER_SYSTEM_INTERVAL = 60
ENTER_SYSTEM_TIMEOUT = 600
