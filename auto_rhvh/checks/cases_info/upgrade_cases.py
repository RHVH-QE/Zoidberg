from common import DELL_PET105_01, DELL_PER510_01

UPGRADE_TIER1_TESTCASE_MAP = {
    "RHEVM-23979": ('atu_yum_update.ks', DELL_PET105_01, 'basic_upgrade_check'),
    "RHEVM-23981": ('atu_yum_update.ks', DELL_PET105_01, 'packages_check'),
    "RHEVM-23982": ('atu_yum_update.ks', DELL_PET105_01, 'settings_check'),
    "RHEVM-23983": ('atu_yum_update.ks', DELL_PET105_01, 'roll_back_check'),
    "RHEVM-23987": ('atu_yum_update.ks', DELL_PET105_01, 'cannot_update_check'),
    "RHEVM-23992": ('atu_yum_update.ks', DELL_PET105_01, 'basic_upgrade_check'),
    "RHEVM-24003": ('atu_yum_update.ks', DELL_PET105_01, 'cmds_check'),
    "RHEVM-24014": ('atu_yum_update.ks', DELL_PET105_01, 'signed_check'),
    #"RHEVM-24022": ('atu_yum_update.ks', DELL_PET105_01, 'knl_space_rpm_check'),
    "RHEVM-24023": ('atu_yum_update.ks', DELL_PET105_01, 'usr_space_rpm_check'),
    "RHEVM-24029": ('atu_yum_update.ks', DELL_PET105_01, 'cmds_check'),
    "RHEVM-23980": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-23988": ('atu_yum_install.ks', DELL_PER510_01, 'cannot_install_check'),
    "RHEVM-23991": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-23999": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-24030": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
}

UPGRADE_TIER2_TESTCASE_MAP = {
    "RHEVM-24021": ('atu_yum_update.ks', DELL_PET105_01, 'avc_denied_check'),
    "RHEVM-24032": ('atu_yum_update.ks', DELL_PET105_01, 'iptables_status_check'),
    "RHEVM-24033": ('atu_yum_update.ks', DELL_PET105_01, 'ntpd_status_check'),
    "RHEVM-24034": ('atu_yum_update.ks', DELL_PET105_01, 'sysstat_check'),
    "RHEVM-24038": ('atu_yum_update.ks', DELL_PET105_01, 'ovirt_imageio_daemon_check'),
    "RHEVM-24004": ('atu_yum_update.ks', DELL_PET105_01, 'boot_dmesg_log_check'),
    "RHEVM-24012": ('atu_yum_update.ks', DELL_PET105_01, 'separate_volumes_check'),
    "RHEVM-24013": ('atu_yum_update.ks', DELL_PET105_01, 'etc_var_file_update_check'),
    "RHEVM-24028": ('atu_yum_install.ks', DELL_PER510_01, 'reinstall_rpm_check'),
    "RHEVM-24037": ('atu_yum_install.ks', DELL_PER510_01, 'packages_check'),
    "RHEVM-24036": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'update_again_unavailable_check'),
    "RHEVM-24016": ('atu_lack_space.ks', DELL_PET105_01, 'no_space_update_check'),
}
