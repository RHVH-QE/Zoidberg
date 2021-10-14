from common import DELL_PER7425_03, DELL_PER510_01, DELL_PER515_01

UPGRADE_TIER1_TESTCASE_MAP = {
    "RHEVM-23979": ('atu_yum_update.ks', DELL_PER7425_03, 'basic_upgrade_check'),
    "RHEVM-23981": ('atu_yum_update.ks', DELL_PER7425_03, 'packages_check'),
    "RHEVM-23982": ('atu_yum_update.ks', DELL_PER7425_03, 'settings_check'),
    "RHEVM-23983": ('atu_yum_update.ks', DELL_PER7425_03, 'roll_back_check'),
    "RHEVM-23992": ('atu_yum_update.ks', DELL_PER7425_03, 'basic_upgrade_check'),
    "RHEVM-24003": ('atu_yum_update.ks', DELL_PER7425_03, 'cmds_check'),
    "RHEVM-24014": ('atu_yum_update.ks', DELL_PER7425_03, 'signed_check'),
    # "RHEVM-24022": ('atu_yum_update.ks', DELL_PER7425_03, 'knl_space_rpm_check'),
    "RHEVM-24023": ('atu_yum_update.ks', DELL_PER7425_03, 'usr_space_rpm_check'),
    "RHEVM-24029": ('atu_yum_update.ks', DELL_PER7425_03, 'cmds_check'),
    "RHEVM-24012": ('atu_yum_update.ks', DELL_PER7425_03, 'separate_volumes_check'),
    "RHEVM-24013": ('atu_yum_update.ks', DELL_PER7425_03, 'etc_var_file_update_check'),
    "RHEVM-23980": ('atu_yum_install.ks', DELL_PER515_01, 'basic_upgrade_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-23991": ('atu_yum_install.ks', DELL_PER515_01, 'basic_upgrade_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-23999": ('atu_rhvm_upgrade.ks', DELL_PER515_01, 'basic_upgrade_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24030": ('atu_rhvm_upgrade.ks', DELL_PER515_01, 'basic_upgrade_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24995": ('atu_rhvm_upgrade.ks', DELL_PER515_01, 'basic_upgrade_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24000": ('atu_rhvm_vms_upgrade.ks', DELL_PER7425_03, 'vms_boot_check'),
}

UPGRADE_TIER2_TESTCASE_MAP = {
    "RHEVM-23987": ('atu_yum_update.ks', DELL_PER7425_03, 'cannot_update_check'),
    "RHEVM-24021": ('atu_yum_update.ks', DELL_PER7425_03, 'avc_denied_check'),
    # "RHEVM-24032": ('atu_yum_update.ks', DELL_PER7425_03, 'iptables_status_check'),
    "RHEVM-24033": ('atu_yum_update.ks', DELL_PER7425_03, 'ntpd_status_check'),
    "RHEVM-24034": ('atu_yum_update.ks', DELL_PER7425_03, 'sysstat_check'),
    "RHEVM-24038": ('atu_yum_update.ks', DELL_PER7425_03, 'ovirt_imageio_daemon_check'),
    "RHEVM-24035": ('atu_yum_update.ks', DELL_PER7425_03, 'kdump_check'),
    "RHEVM-24402": ('atu_yum_update.ks', DELL_PER7425_03, 'katello_check'),
    "RHEVM-24391": ('atu_yum_update.ks', DELL_PER7425_03, 'imgbased_log_check'),
    # "RHEVM-24039": ('atu_yum_update.ks', DELL_PER7425_03, 'port_16514_check'),
    "RHEVM-24040": ('atu_yum_update.ks', DELL_PER7425_03, 'systemd_tmpfiles_clean_check'),
    "RHEVM-26979": ('atu_yum_update.ks', DELL_PER7425_03, 'usr_space_service_status_check'),
    "RHEVM-24016": ('atu_lack_space.ks', DELL_PER7425_03, 'no_space_update_check'),
    "RHEVM-24004": ('atu_yum_install.ks', DELL_PER515_01, 'boot_dmesg_log_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24028": ('atu_yum_install.ks', DELL_PER515_01, 'reinstall_rpm_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24037": ('atu_yum_install.ks', DELL_PER515_01, 'packages_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-23988": ('atu_yum_install.ks', DELL_PER515_01, 'cannot_install_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-23989": ('atu_yum_vlan.ks', DELL_PER515_01, 'basic_upgrade_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24020": ('atu_yum_vlan.ks', DELL_PER515_01, 'delete_imgbase_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24041": ('atu_yum_vlan.ks', DELL_PER515_01, 'libguestfs_tool_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-24042": ('atu_yum_vlan.ks', DELL_PER515_01, 'diff_services_check'),#DELL_PER510_01 is broken, so move to DELL_PER515_01
    "RHEVM-23996": ('atu_rhvm_iscsi.ks', DELL_PER515_01, 'basic_upgrade_check'),
    "RHEVM-24036": ('atu_rhvm_iscsi.ks', DELL_PER515_01, 'update_again_unavailable_check'),
    # "RHEVM-24036": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'update_again_unavailable_check'),
    "RHEVM-27787": ('atu_rhvm_security_upgrade.ks', DELL_PER7425_03, 'scap_stig_check'),
}
