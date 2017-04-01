"""Here put all project level costants"""
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

cfgjson = os.path.join(PROJECT_ROOT, 'auto_installation', 'constants.json')
CFGS = json.load(open(cfgjson))

KS_FILES_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                            'rhvh-41')

KS_FILES_AUTO_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                                 'auto')

BUILDS_SERVER_URL = "http://10.66.10.22:8090"

CURRENT_IP_PORT = ('10.73.73.23', '5000')

STATIC_URL = ("http://{0}:{1}/"
              "static/ngn-auto-installation-kickstarts/%s").format(
                  CURRENT_IP_PORT[0], CURRENT_IP_PORT[1])

DELL_PET105_01 = 'dell-pet105-01.qe.lab.eng.nay.redhat.com'
DELL_PER510_01 = 'dell-per510-01.lab.eng.pek2.redhat.com'

# ANACONDA-TIER1, ANACONDA-TIER2, KS-TIER1, KS-TIER2,ALL
ANACONDA_TIER1 = 0x01
ANACONDA_TIER2 = 0x02
KS_TIER1 = 0x04
KS_TIER2 = 0x08
DEBUG_TIER = 0x10

TEST_LEVEL = CFGS['test_level']
# TEST_LEVEL = ANACONDA_TIER2

# one kickstart file can only be run on a single machine
ANACONDA_TIER1_TESTCASE_MAP = {
    'RHEVM-17788': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17800': ('ati_local_01.ks', DELL_PET105_01, 'static_network_check'),
    'RHEVM-17801': ('ati_local_01.ks', DELL_PET105_01, 'hostname_check'),
    'RHEVM-17807': ('ati_local_01.ks', DELL_PET105_01, 'partition_check'),
    'RHEVM-17826': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17828': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17799':
    ('ati_local_01.ks', DELL_PET105_01, 'nic_stat_dur_install_check'),
    'RHEVM-17790': ('ati_fc_01.ks', DELL_PER510_01, 'install_check'),
    'RHEVM-17806': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17816': ('ati_fc_01.ks', DELL_PER510_01, 'bond_vlan_check'),
    'RHEVM-16972': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check')
}

ANACONDA_TIER2_TESTCASE_MAP = {
    'RHEVM-17798': ('ati_local_01.ks', DELL_PET105_01, 'lang_check'),
    'RHEVM-17802': ('ati_local_01.ks', DELL_PET105_01, 'ntp_check'),
    'RHEVM-17803': ('ati_local_01.ks', DELL_PET105_01, 'keyboard_check'),
    'RHEVM-17805':
    ('ati_local_01.ks', DELL_PET105_01, 'security_policy_check'),
    'RHEVM-17808': ('ati_local_01.ks', DELL_PET105_01, 'kdump_check'),
    'RHEVM-17811': ('ati_local_01.ks', DELL_PET105_01, 'users_check'),
    'RHEVM-18210': ('ati_local_01.ks', DELL_PET105_01, 'layout_init_check'),
    'RHEVM-17804': ('ati_local_02.ks', DELL_PET105_01, 'keyboard_check'),
    'RHEVM-17823': ('ati_local_02.ks', DELL_PET105_01, 'fips_check'),
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
    'RHEVM-17860': ('ati_fc_02.ks', DELL_PER510_01, 'bond_check'),
    'RHEVM-17862': ('ati_fc_02.ks', DELL_PER510_01, 'vlan_check'),
    'RHEVM-17863': ('ati_fc_02.ks', DELL_PER510_01, 'bond_vlan_check'),
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
    'RHEVM-17859': ('ati_fc_02.ks', DELL_PER510_01, 'static_network_check'),
    'RHEVM-17872': ('ati_fc_02.ks', DELL_PER510_01, 'ntp_check'),
    'RHEVM-17873': ('ati_fc_02.ks', DELL_PER510_01, 'users_check'),
    'RHEVM-17867': ('ati_local_02.ks', DELL_PET105_01, 'selinux_check'),
    'RHEVM-17847': ('ati_local_02.ks', DELL_PET105_01, 'partition_check'),
    'RHEVM-17861': ('ati_local_02.ks', DELL_PET105_01, 'static_network_check'),
    'RHEVM-17834': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17835': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17836': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17839': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-17848': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
}

DEBUG_TIER_TESTCASE_MAP = {
    'RHEVM-17834': ('ati_fc_03.ks', DELL_PER510_01, 'partition_check'),
    'RHEVM-18210': ('ati_local_01.ks', DELL_PET105_01, 'layout_init_check'),
}

KS_PRESSURE_MAP = {'ati_fc_04.ks': '3'}

KS_KERPARAMS_MAP = {'ati_local_02.ks': 'fips=1'}

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
            "macaddress-em2": "78:2b:cb:47:93:5e"
        },
        "hostname": "",
        "static_ip": ""
    }
}

TR_TPL = '4_1_Node_Auto_ATIKS_{}'
TR_PROJECT_ID = 'RHEVM3'
TR_ID = '4_1_Node_Install_AutoTest_{}_{}'

# Kickstart related stuff

POST_SCRIPT_01 = """
EM1IP=$(ip -o -4 addr show {} | awk -F '[ /]+' '/global/ {{print $4}}')
curl -s http://%s:%s/done/$EM1IP/""" % (CURRENT_IP_PORT[0], CURRENT_IP_PORT[1])

PRE_SCRIPT_01 = """set -x
# Some distros have curl in their minimal install set, others have wget.
# We define a wrapper function around the best available implementation
# so that the rest of the script can use that for making HTTP requests.
if command -v curl >/dev/null ; then
    # Older curl versions lack --retry
    if curl --help 2>&1 | grep -q .*--retry ; then
        function fetch() {{
            curl --retry 20 --remote-time -o "$1" "$2"
        }}
    else
        function fetch() {{
            curl --remote-time -o "$1" "$2"
        }}
    fi
elif command -v wget >/dev/null ; then
    # In Anaconda images wget is actually busybox
    if wget --help 2>&1 | grep -q BusyBox ; then
        function fetch() {{
            wget -O "$1" "$2"
        }}
    else
        function fetch() {{
            wget --tries 20 -O "$1" "$2"
        }}
    fi
else
    echo "No HTTP client command available!"
    function fetch() {{
        false
    }}
fi

fetch /tmp/anamon http://{srv_ip}:{srv_port}/static/anamon.py
python /tmp/anamon --server {srv_ip} --port {srv_port} --stage pre

""".format(
    srv_ip=CURRENT_IP_PORT[0], srv_port=CURRENT_IP_PORT[1])

NOPXE_URL = "http://lab-01.rhts.eng.pek2.redhat.com:8000/nopxe/{0}"

CB_API = "http://10.73.60.74/cobbler_api"
CB_CREDENTIAL = ('cobbler', 'cobbler')
CB_PROFILE = CFGS['cb_profile']
ARGS_TPL = ('inst.ks=http://{srv_ip}:{srv_port}/static/auto/{ks_file} '
            'inst.stage2=http://10.66.10.22:8090/'
            'rhvh_ngn/pxedir/RHVH-4.1-20170309.0-RHVH-x86_64-dvd1.iso/stage2 '
            '{addition_params}')
