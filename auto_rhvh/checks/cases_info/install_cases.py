from common import DELL_PER510_01, DELL_PER515_01, DELL_PER515_02

# one kickstart file can only be run on a single machine
INSTALL_TIER1_TESTCASE_MAP = {
    'RHEVM-23911': ('ati_fc_01.ks', DELL_PER510_01, 'PartitionCheck.partitions_check'),
    'RHEVM-23945': ('ati_fc_01.ks', DELL_PER510_01, 'NetworkCheck.dhcp_network_check'),
    'RHEVM-23950': ('ati_fc_01.ks', DELL_PER510_01, 'NetworkCheck.bond_vlan_check'),
    'RHEVM-24162': ('ati_fc_01.ks', DELL_PER510_01, 'GeneralCheck.node_check'),
    'RHEVM-23919': ('ati_iscsi_01.ks', DELL_PER515_01, 'PartitionCheck.custom_boot_check'),
    'RHEVM-23930': ('ati_iscsi_01.ks', DELL_PER515_01, 'PartitionCheck.vgfree_check'),
    'RHEVM-23938': ('ati_iscsi_01.ks', DELL_PER515_01, 'PartitionCheck.custom_nists_check'),
    'RHEVM-23942': ('ati_iscsi_01.ks', DELL_PER515_01, 'PartitionCheck.custom_swap_check'),
    'RHEVM-24689': ('ati_iscsi_01.ks', DELL_PER515_01, 'PartitionCheck.custom_var_crash_check'),
    'RHEVM-24163': ('ati_iscsi_01.ks', DELL_PER515_01, 'GeneralCheck.node_check'),
    'RHEVM-23948': ('ati_iscsi_01.ks', DELL_PER515_01, 'NetworkCheck.bond_check'),
    'RHEVM-24161': ('ati_local_01.ks', DELL_PER515_02, 'GeneralCheck.node_check'),
}

INSTALL_TIER2_TESTCASE_MAP = {
    'RHEVM-23882': ('ati_fc_01.ks', DELL_PER510_01, 'LangCheck.lang_check'),
    'RHEVM-23884': ('ati_fc_01.ks', DELL_PER510_01, 'TimezoneCheck.ntp_check'),
    'RHEVM-23885': ('ati_fc_01.ks', DELL_PER510_01, 'TimezoneCheck.utc_check'),
    'RHEVM-23886': ('ati_fc_01.ks', DELL_PER510_01, 'TimezoneCheck.timezone_check'),
    'RHEVM-23889': ('ati_fc_01.ks', DELL_PER510_01, 'KeyboardCheck.keyboard_check'),
    'RHEVM-23892': ('ati_fc_01.ks', DELL_PER510_01, 'UserCheck.user_check'),
    'RHEVM-23896': ('ati_fc_01.ks', DELL_PER510_01, 'KdumpCheck.kdump_enable_check'),
    'RHEVM-23897': ('ati_fc_01.ks', DELL_PER510_01, 'SelinuxCheck.selinux_check'),
    'RHEVM-23899': ('ati_fc_01.ks', DELL_PER510_01, 'SecurityCheck.security_policy_check'),
    'RHEVM-23905': ('ati_fc_01.ks', DELL_PER510_01, 'FirewallCheck.firewall_enable_check'),
    'RHEVM-23909': ('ati_fc_01.ks', DELL_PER510_01, 'ServicesCheck.sshd_check'),
    'RHEVM-23954': ('ati_fc_01.ks', DELL_PER510_01, 'NetworkCheck.hostname_check'),
    'RHEVM-24195': ('ati_fc_01.ks', DELL_PER510_01, 'GeneralCheck.layout_init_check'),
    'RHEVM-24167': ('ati_fc_01.ks', DELL_PER510_01, 'GeneralCheck.node_check'),
    'RHEVM-24168': ('ati_fc_02.ks', DELL_PER510_01, 'GeneralCheck.node_check'),
    'RHEVM-24192': ('ati_fc_02.ks', DELL_PER510_01, 'GeneralCheck.iqn_check'),
    'RHEVM-23901': ('ati_iscsi_01.ks', DELL_PER515_01, 'SelinuxCheck.selinux_check'),
    'RHEVM-23904': ('ati_iscsi_01.ks', DELL_PER515_01, 'FirewallCheck.firewall_disable_check'),
    'RHEVM-23907': ('ati_iscsi_01.ks', DELL_PER515_01, 'GrubbyCheck.grubby_check'),
    'RHEVM-23895': ('ati_iscsi_02.ks', DELL_PER515_01, 'KdumpCheck.kdump_disable_check'),
    'RHEVM-23902': ('ati_iscsi_02.ks', DELL_PER515_01, 'SelinuxCheck.selinux_check'),
    'RHEVM-23912': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.bootloader_check'),
    'RHEVM-23924': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.custom_boot_check'),
    'RHEVM-23923': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.custom_std_data_check'),
    'RHEVM-23925': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.custom_swap_check'),
    'RHEVM-23939': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.custom_nists_check'),
    'RHEVM-23940': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.custom_thin_data_check'),
    'RHEVM-23943': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.custom_lv_data_check'),
    'RHEVM-24690': ('ati_iscsi_02.ks', DELL_PER515_01, 'PartitionCheck.custom_var_crash_check'),
    'RHEVM-23947': ('ati_iscsi_02.ks', DELL_PER515_01, 'NetworkCheck.vlan_check'),
    'RHEVM-23941': ('ati_local_01.ks', DELL_PER515_02, 'PartitionCheck.partitions_check'),
    'RHEVM-23944': ('ati_local_01.ks', DELL_PER515_02, 'NetworkCheck.static_network_check'),
    'RHEVM-23949': ('ati_local_01.ks', DELL_PER515_02, 'NetworkCheck.nic_stat_dur_install_check'),
    'RHEVM-23955': ('ati_local_01.ks', DELL_PER515_02, 'NetworkCheck.static_network_check'),
    'RHEVM-23888': ('ati_local_01.ks', DELL_PER515_02, 'KeyboardCheck.keyboard_check'),
    'RHEVM-24186': ('ati_local_02.ks', DELL_PET105_01, 'GeneralCheck.fips_check'),
}

KS_PRESSURE_MAP = {'ati_fc_02.ks': '3'}

KS_KERPARAMS_MAP = {'ati_local_02.ks': 'fips=1'}
