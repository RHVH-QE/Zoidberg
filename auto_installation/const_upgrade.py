from constants import DELL_PET105_01, DELL_PER510_01

UPGRADE_TIER1_TESTCASE_MAP = {
    "RHEVM-18068": ('atu_yum_update.ks', DELL_PET105_01, 'basic_upgrade_check'),
    "RHEVM-18071": ('atu_yum_update.ks', DELL_PET105_01, 'packages_check'),
    "RHEVM-18072": ('atu_yum_update.ks', DELL_PET105_01, 'settings_check'),
    "RHEVM-18073": ('atu_yum_update.ks', DELL_PET105_01, 'roll_back_check'),
    "RHEVM-18077": ('atu_yum_update.ks', DELL_PET105_01, 'cannot_update_check'),
    "RHEVM-18082": ('atu_yum_update.ks', DELL_PET105_01, 'basic_upgrade_check'),
    "RHEVM-18093": ('atu_yum_update.ks', DELL_PET105_01, 'cmds_check'),
    "RHEVM-18104": ('atu_yum_update.ks', DELL_PET105_01, 'signed_check'),
    "RHEVM-18211": ('atu_yum_update.ks', DELL_PET105_01, 'knl_space_rpm_check'),
    "RHEVM-18212": ('atu_yum_update.ks', DELL_PET105_01, 'usr_space_rpm_check'),
    "RHEVM-21647": ('atu_yum_update.ks', DELL_PET105_01, 'cmds_check'),
    "RHEVM-18069": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-18078": ('atu_yum_install.ks', DELL_PER510_01, 'cannot_install_check'),
    "RHEVM-18081": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-18089": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
}

RHVM_DATA_MAP = {
    "4.0_rhvm_fqdn": "rhvm40-vlan50-1.lab.eng.pek2.redhat.com",
    "4.1_rhvm_fqdn": "rhvm41-vdsm-auto.lab.eng.pek2.redhat.com",
}

RHVH_UPDATE_RPM_NAME = "redhat-virtualization-host-image-update-{}.el7_3.noarch.rpm"
RHVH_UPDATE_RPM_URL = "http://10.66.10.22:8090/rhvhupgrade/updates/{}"

KERNEL_SPACE_RPM_URL = ("http://download.eng.pek2.redhat.com/pub/rhel/rel-eng/RHEL-7.3-20161019.0/"
                        "compose/Server/x86_64/os/Packages/"
                        "kmod-oracleasm-2.0.8-17.el7.x86_64.rpm")

FABRIC_TIMEOUT = 300
YUM_UPDATE_TIMEOUT = 1200
YUM_INSTALL_TIMEOUT = 1200
CHK_HOST_ON_RHVM_STAT_MAXCOUNT = 20
CHK_HOST_ON_RHVM_STAT_INTERVAL = 60
ENTER_SYSTEM_MAXCOUNT = 10
ENTER_SYSTEM_INTERVAL = 60
ENTER_SYSTEM_TIMEOUT = 600
