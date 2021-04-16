from common import DELL_PER7425_03, DELL_PER510_01, DELL_PER515_01

UPGRADE_TIER1_TESTCASE_MAP = {
    "RHEVM-23979": ('atu_yum_update.ks', DELL_PER7425_03, 'basic_upgrade_check'),
    "RHEVM-23981": ('atu_yum_update.ks', DELL_PER7425_03, 'packages_check'),
    "RHEVM-23982": ('atu_yum_update.ks', DELL_PER7425_03, 'settings_check'),
    "RHEVM-23983": ('atu_yum_update.ks', DELL_PER7425_03, 'roll_back_check'),
    "RHEVM-23992": ('atu_yum_update.ks', DELL_PER7425_03, 'basic_upgrade_check'),
    "RHEVM-24003": ('atu_yum_update.ks', DELL_PER7425_03, 'cmds_check'),
    "RHEVM-24014": ('atu_yum_update.ks', DELL_PER7425_03, 'signed_check'),
    ## "RHEVM-24022": ('atu_yum_update.ks', DELL_PER7425_03, 'knl_space_rpm_check'),
    "RHEVM-24023": ('atu_yum_update.ks', DELL_PER7425_03, 'usr_space_rpm_check'),
    "RHEVM-24029": ('atu_yum_update.ks', DELL_PER7425_03, 'cmds_check'),
    "RHEVM-24012": ('atu_yum_update.ks', DELL_PER7425_03, 'separate_volumes_check'),
    "RHEVM-24013": ('atu_yum_update.ks', DELL_PER7425_03, 'etc_var_file_update_check'),
    "RHEVM-27458": ('atu_yum_update.ks', DELL_PER7425_03, 'etc_var_file_update_check'),
    "RHEVM-26037": ('atu_yum_update.ks', DELL_PER7425_03, 'sssd_permission_check'),
    "RHEVM-27295": ('atu_yum_ls_update.ks', DELL_PER7425_03, 'ls_update_failed_check'),
    "RHEVM-24005": ('atu_yum_normal_ls_update.ks', DELL_PER7425_03, 'basic_upgrade_check'),
    "RHEVM-23980": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-23991": ('atu_yum_install.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-23999": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-24030": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-24995": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-27051": ('atu_rhvm_bond_vlan_upgrade.ks', DELL_PER515_01, 'grubenv_check'),
    "RHEVM-27552": ('atu_rhvm_bond_vlan_upgrade.ks', DELL_PER515_01, 'openvswitch_permission_check'),
    "RHEVM-24000": ('atu_rhvm_vms_upgrade.ks', DELL_PER7425_03, 'vms_boot_check'),
    "RHEVM-23996": ('atu_rhvm_iscsi.ks', DELL_PER515_01, 'basic_upgrade_check'),#2021-03-29 added iscsi SD and VM
}

UPGRADE_TIER2_TESTCASE_MAP = {
    "RHEVM-23987": ('atu_yum_update.ks', DELL_PER7425_03, 'cannot_update_check'),
    "RHEVM-24021": ('atu_yum_update.ks', DELL_PER7425_03, 'avc_denied_check'),
    ## "RHEVM-24032": ('atu_yum_update.ks', DELL_PER7425_03, 'iptables_status_check'),
    "RHEVM-24033": ('atu_yum_update.ks', DELL_PER7425_03, 'ntpd_status_check'),
    "RHEVM-24034": ('atu_yum_update.ks', DELL_PER7425_03, 'sysstat_check'),
    "RHEVM-24038": ('atu_yum_update.ks', DELL_PER7425_03, 'ovirt_imageio_daemon_check'),
    "RHEVM-24035": ('atu_yum_update.ks', DELL_PER7425_03, 'kdump_check'),
    ## "RHEVM-24402": ('atu_yum_update.ks', DELL_PER7425_03, 'katello_check'),#This case does not apply to RHVH4.4 according to Bug 1425032
    "RHEVM-24391": ('atu_yum_update.ks', DELL_PER7425_03, 'imgbased_log_check'),
    ## "RHEVM-24039": ('atu_yum_update.ks', DELL_PER7425_03, 'port_16514_check'),
    "RHEVM-24040": ('atu_yum_update.ks', DELL_PER7425_03, 'systemd_tmpfiles_clean_check'),
    "RHEVM-26979": ('atu_yum_update.ks', DELL_PER7425_03, 'usr_space_service_status_check'),
    "RHEVM-23994": ('atu_yum_update.ks', DELL_PER7425_03, 'cannot_upgrade_check_in_latest_build'),
    "RHEVM-24018": ('atu_upgrade_and_rollback_01.ks', DELL_PER7425_03, 'rollback_and_basic_check'),
    "RHEVM-24019": ('atu_upgrade_and_rollback_02.ks', DELL_PER7425_03, 'rollback_and_basic_check'),
    "RHEVM-27028": ('atu_rhvm_config_upgrade.ks', DELL_PER7425_03, 'lvm_configuration_check'),
    "RHEVM-26033": ('atu_rhvm_config_upgrade.ks', DELL_PER7425_03, 'insights_check'),#RHSM
    "RHEVM-24016": ('atu_lack_space.ks', DELL_PER7425_03, 'no_space_update_check'),
    "RHEVM-24004": ('atu_yum_install.ks', DELL_PER510_01, 'boot_dmesg_log_check'),
    "RHEVM-24028": ('atu_yum_install.ks', DELL_PER510_01, 'reinstall_rpm_check'),
    "RHEVM-24037": ('atu_yum_install.ks', DELL_PER510_01, 'packages_check'),
    "RHEVM-23988": ('atu_yum_install.ks', DELL_PER510_01, 'cannot_install_check'),
    "RHEVM-23989": ('atu_yum_vlan.ks', DELL_PER510_01, 'basic_upgrade_check'),
    "RHEVM-24020": ('atu_yum_vlan.ks', DELL_PER510_01, 'delete_imgbase_check'),
    "RHEVM-24041": ('atu_yum_vlan.ks', DELL_PER510_01, 'libguestfs_tool_check'),
    "RHEVM-24042": ('atu_yum_vlan.ks', DELL_PER510_01, 'diff_services_check'),
    "RHEVM-23996": ('atu_rhvm_iscsi.ks', DELL_PER515_01, 'basic_upgrade_check'),#2021-03-29 added iscsi SD and VM
    "RHEVM-24036": ('atu_rhvm_iscsi.ks', DELL_PER515_01, 'update_again_unavailable_check'),
    ## "RHEVM-24036": ('atu_rhvm_upgrade.ks', DELL_PER510_01, 'update_again_unavailable_check'),
    "RHEVM-23986": ('atu_rhvm_bond_iscsi.ks', DELL_PER515_01, 'basic_upgrade_check'),
    "RHEVM-27050": ('atu_rhvm_failed_upgrade.ks', DELL_PER7425_03, 'upgrade_failed_check'),
    "RHEVM-27534": ('atu_rhvm_failed_upgrade.ks', DELL_PER7425_03, 'placeholder_check'),
    "RHEVM-24009": ('atu_rhvm_normal_upgrade.ks', DELL_PER7425_03, 'enable_repos_check'),#RHSM
    "RHEVM-24011": ('atu_rhvm_normal_upgrade.ks', DELL_PER7425_03, 'gpgcheck_check'),#RHSM
    "RHEVM-24010": ('atu_rhvm_normal_upgrade.ks', DELL_PER7425_03, 'repos_info_check'),#RHSM
    "RHEVM-26253": ('atu_rhvm_rhsm_upgrade.ks', DELL_PER7425_03, 'basic_upgrade_check'),#RHSM,just run after GA
    "RHEVM-24017": ('atu_rhvm_fips_upgrade.ks', DELL_PER7425_03, 'fips_mode_check'),
    "RHEVM-26255": ('atu_rhvm_security_upgrade.ks', DELL_PER7425_03, 'scap_stig_check'),
    "RHEVM-24034": ('atu_duplicate_service_update.ks', DELL_PER7425_03, 'installed_rpms_check'),
}
