from constants import DELL_PET105_01, DELL_PER510_01

# one kickstart file can only be run on a single machine
ANACONDA_TIER1_TESTCASE_MAP = {
    'RHEVM-17788': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17800': ('ati_local_01.ks', DELL_PET105_01, 'static_network_check'),
    'RHEVM-17801': ('ati_local_01.ks', DELL_PET105_01, 'hostname_check'),
    'RHEVM-17807': ('ati_local_01.ks', DELL_PET105_01, 'partition_check'),
    'RHEVM-17826': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17828': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17799': ('ati_local_01.ks', DELL_PET105_01,
                    'nic_stat_dur_install_check'),
    'RHEVM-21643': ('ati_local_01.ks', DELL_PET105_01, 'partition_check'),
    'RHEVM-17790': ('ati_fc_01.ks', DELL_PER510_01, 'install_check'),
    'RHEVM-17806': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17816': ('ati_fc_01.ks', DELL_PER510_01, 'bond_vlan_check'),
    'RHEVM-16972': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-21642': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check')
}

ANACONDA_TIER2_TESTCASE_MAP = {
    'RHEVM-17798': ('ati_local_01.ks', DELL_PET105_01, 'lang_check'),
    'RHEVM-17802': ('ati_local_01.ks', DELL_PET105_01, 'ntp_check'),
    'RHEVM-17803': ('ati_local_01.ks', DELL_PET105_01, 'keyboard_check'),
    'RHEVM-17805': ('ati_local_01.ks', DELL_PET105_01,
                    'security_policy_check'),
    'RHEVM-17808': ('ati_local_01.ks', DELL_PET105_01, 'kdump_check'),
    'RHEVM-17811': ('ati_local_01.ks', DELL_PET105_01, 'users_check'),
    'RHEVM-18210': ('ati_local_01.ks', DELL_PET105_01, 'layout_init_check'),
    'RHEVM-17823': ('ati_local_01.ks', DELL_PET105_01, 'fips_check'),
    'RHEVM-17804': ('ati_local_02.ks', DELL_PET105_01, 'keyboard_check'),
    #'RHEVM-17823': ('ati_local_02.ks', DELL_PET105_01, 'fips_check'),
    'RHEVM-17818': ('ati_fc_04.ks', DELL_PER510_01, 'install_check'),
    'RHEVM-17819': ('ati_fc_04.ks', DELL_PER510_01, 'install_check'),
    'RHEVM-17824': ('ati_fc_04.ks', DELL_PER510_01, 'iqn_check'),
    'RHEVM-17815': ('ati_fc_03.ks', DELL_PER510_01, 'vlan_check'),
}

KS_TIER1_TESTCASE_MAP = {
    'RHEVM-17831': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17851': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17833': ('ati_fc_02.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17858': ('ati_fc_02.ks', DELL_PER510_01, 'dhcp_network_check'),
    #'RHEVM-17860': ('ati_fc_02.ks', DELL_PER510_01, 'bond_check'),
    #'RHEVM-17862': ('ati_fc_02.ks', DELL_PER510_01, 'vlan_check'),
    #'RHEVM-17863': ('ati_fc_02.ks', DELL_PER510_01, 'bond_vlan_check'),
    'RHEVM-17864': ('ati_fc_02.ks', DELL_PER510_01, 'firewall_check'),
    'RHEVM-17869': ('ati_fc_02.ks', DELL_PER510_01, 'sshd_check'),
    'RHEVM-17874': ('ati_fc_02.ks', DELL_PER510_01, 'grubby_check'),
    'RHEVM-17865': ('ati_fc_03.ks', DELL_PER510_01, 'selinux_check'),
    'RHEVM-17854': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
}

KS_TIER2_TESTCASE_MAP = {
    'RHEVM-17830': ('ati_fc_02.ks', DELL_PER510_01, 'bootloader_check'),
    'RHEVM-17843': ('ati_fc_02.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17844': ('ati_fc_02.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17845': ('ati_fc_02.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17846': ('ati_fc_02.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17853': ('ati_fc_02.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17857': ('ati_fc_02.ks', DELL_PER510_01, 'install_check'),
    'RHEVM-17868': ('ati_fc_02.ks', DELL_PER510_01, 'install_check'),
    'RHEVM-17866': ('ati_fc_02.ks', DELL_PER510_01, 'selinux_check'),
    #'RHEVM-17859': ('ati_fc_02.ks', DELL_PER510_01, 'static_network_check'),
    'RHEVM-17872': ('ati_fc_02.ks', DELL_PER510_01, 'ntp_check'),
    'RHEVM-17873': ('ati_fc_02.ks', DELL_PER510_01, 'users_check'),
    'RHEVM-17867': ('ati_local_02.ks', DELL_PET105_01, 'selinux_check'),
    'RHEVM-17847': ('ati_local_02.ks', DELL_PET105_01, 'partition_check'),
    'RHEVM-17859': ('ati_local_02.ks', DELL_PET105_01, 'static_network_check'),
    'RHEVM-17861': ('ati_local_02.ks', DELL_PET105_01, 'static_network_check'),
    'RHEVM-17834': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17835': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17836': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17839': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17848': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
}

KS_PRESSURE_MAP = {'ati_fc_04.ks': '3'}

KS_KERPARAMS_MAP = {'ati_local_01.ks': 'fips=1'}
