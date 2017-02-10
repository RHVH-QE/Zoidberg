"""Here put all project level costants"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

KS_FILES_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                            'rhvh-41')

KS_FILES_AUTO_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                                 'auto')

BUILDS_SERVER_URL = "http://10.66.10.22:8090"

CURRENT_IP_PORT = ('10.66.9.123', '5000')

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

TEST_LEVEL = ANACONDA_TIER1 | ANACONDA_TIER2

# one kickstart file can only be run on a single machine
ANACONDA_TIER1_TESTCASE_MAP = {
    'RHEVM-17788': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17800': ('ati_local_01.ks', DELL_PET105_01, 'static_network_check'),
    'RHEVM-17801': ('ati_local_01.ks', DELL_PET105_01, 'hostname_check'),
    'RHEVM-17807': ('ati_local_01.ks', DELL_PET105_01, 'manually_partition_check'),
    'RHEVM-17826': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17828': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-17790': ('ati_fc_01.ks', DELL_PER510_01, 'install_check'),
    'RHEVM-17806': ('ati_fc_01.ks', DELL_PER510_01, 'auto_partition_check'),
    'RHEVM-17816': ('ati_fc_01.ks', DELL_PER510_01, 'bond_vlan_check'),
    'RHEVM-16972': ('ati_fc_01.ks', DELL_PER510_01, 'auto_partition_check')
}

ANACONDA_TIER2_TESTCASE_MAP = {
    'RHEVM-17798': ('ati_local_01.ks', DELL_PET105_01, 'lang_check'),
    'RHEVM-17802': ('ati_local_01.ks', DELL_PET105_01, 'ntp_check'),
    'RHEVM-17803': ('ati_local_01.ks', DELL_PET105_01, 'keyboard_check'),
    'RHEVM-17805': ('ati_local_01.ks', DELL_PET105_01, 'security_policy_check'),
    'RHEVM-17808': ('ati_local_01.ks', DELL_PET105_01, 'kdump_check'),
    'RHEVM-17811': ('ati_local_01.ks', DELL_PET105_01, 'users_check'),
    'RHEVM-17804': ('ati_local_02.ks', DELL_PET105_01, 'keyboard_check')
}

KS_TIER1_TESTCASE_MAP = {}

KS_TIER2_TESTCASE_MAP = {}

SMOKE_TEST_LIST = ('FC_01',)
P1_TEST_LIST = (
    'autopart',
    'bond',
    'FC',
    'part',)
ALL_TEST = ('*',)
MUST_HAVE_TEST_LIST = (
    # 'autopart_01',
    # 'FC_01',
    # 'FC_04',
    # 'FC_05',
    # 'FC_06',
    # 'lvm_01',
    # 'iscsi_01',
    # 'raid_01',
    # 'network_01',
    # 'ntp',
    # 'bond_01',
    # 'vlan_01',
    # 'firewall_01',
    # 'selinux_01',
    'local_01',)

DEBUG_LIST = ('FC_06',)

HOST_POOL = {
    'FC': ('dell-per510-01.lab.eng.pek2.redhat.com',),
    'bond': (),
    'iscsi': (),
    'uefi': (),
    'vlan': (),
    'default': ('dell-pet105-01.qe.lab.eng.nay.redhat.com',),
}

HOSTS = {
    DELL_PET105_01: {
        "nic": {
            "macaddress-enp2s0": "00:22:19:27:54:c7"
        },
        "hostname": "",
        "static_ip": "",
        "ksfiles": ("ati_local_01.ks", "ati_local_02.ks")
    },
    DELL_PER510_01: {
        "nic": {
            "macaddress-em2": "78:2b:cb:47:93:5e"
        },
        "hostname": "",
        "static_ip": "",
        "ksfiles": "ati_fc_01.ks"
    }
}

TR_TPL = '4_0_Node_Auto_ATIKS_{}'
TR_PROJECT_ID = 'RHEVM3'
TR_ID = '4_0_Node_{}_AutoInstallWithKickstart_{}'
KS_TESTCASE_MAP = {
    'ati_FC_01.ks': 'RHEVM-15410',
    'ati_firewall_01.ks': 'RHEVM-15418',
    'ati_iscsi_01.ks': 'RHEVM-15414',
    'ati_network_01.ks': 'RHEVM-15058',
    'ati_selinux_01.ks': 'RHEVM-15060',
    'ati_services_01.ks': 'RHEVM-15062',
    'ati_autopart_01.ks': 'RHEVM-15056',
    'ati_lvm_01.ks': 'RHEVM-15057',
    'ati_ntp.ks': 'RHEVM-15064',
    'ati_local_01.ks': ('RHEVM-17788',
                        'RHEVH-17800',
                        'RHEVH-17801',
                        'RHEVH-17807',
                        'RHEVH-17826',
                        'RHEVH-17828',
                        'RHEVH-17798',
                        'RHEVH-17802',
                        'RHEVH-17803',
                        'RHEVH-17805',
                        'RHEVH-17808',
                        'RHEVH-17811'),
    'ati_local_02.ks': 'RHEVM-17804',
    'ati_fc_01.ks': ('RHEVM-17790',
                     'RHEVM-17806',
                     'RHEVM-17816',
                     'RHEVM-16972')
}

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
CB_PROFILE = 'RHVH-4.1-73-20170111.0'
CB_SYSTEM = 'dell-pet105-01.qe.lab.eng.nay.redhat.com'
ARGS_TPL = ('inst.ks=http://{srv_ip}:{srv_port}/static/auto/{ks_file} '
            'inst.stage2=http://10.66.10.22:8090/'
            'rhvh_ngn/pxedir/RHVH-4.1-20170111.0-RHVH-x86_64-dvd1.iso/stage2')
