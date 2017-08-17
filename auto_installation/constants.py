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

LOG_URL = "http://10.73.73.23:7788"

STATIC_URL = ("http://{0}:{1}/"
              "static/ngn-auto-installation-kickstarts/%s").format(
                  CURRENT_IP_PORT[0], CURRENT_IP_PORT[1])

DELL_PET105_01 = 'dell-pet105-01.qe.lab.eng.nay.redhat.com'
DELL_PER510_01 = 'dell-per510-01.lab.eng.pek2.redhat.com'
DELL_OP790_01 = 'dell-op790-01.qe.lab.eng.nay.redhat.com'
DELL_PER515_01 = 'dell-per515-01.lab.eng.pek2.redhat.com'

COVERAGE_TEST = True

# ANACONDA-TIER1, ANACONDA-TIER2, KS-TIER1, KS-TIER2,ALL
DEBUG_TIER = 0x01
ANACONDA_TIER1 = 0x02
ANACONDA_TIER2 = 0x04
KS_TIER1 = 0x08
KS_TIER2 = 0x10
UPGRADE_TIER1 = 0x20
UPGRADE_TIER2 = 0x40
VDSM_TIER = 0x80

TEST_LEVEL = CFGS['test_level']
# TEST_LEVEL = UPGRADE_TIER1

DEBUG_TIER_TESTCASE_MAP = {
    'RHEVM-17788': ('ati_local_01.ks', DELL_PET105_01, 'install_check'),
    'RHEVM-16972': ('ati_fc_01.ks', DELL_PER510_01, 'partition_check')
}

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
            "macaddress-em2": "08:9e:01:63:2c:b3"
        },
        "hostname": "",
        "static_ip": ""
    }
}

TR_TPL = '4_1_Node_Auto_ATIKS_{}'
TR_PROJECT_ID = 'RHEVM3'
TR_ID = '{}_{}'

# Kickstart related stuff

POST_SCRIPT_01 = """
EM1IP=$(ip -o -4 addr show {} | awk -F '[ /]+' '/global/ {{print $4}}')
curl -s http://%s:%s/done/$EM1IP/""" % (CURRENT_IP_PORT[0], CURRENT_IP_PORT[1])

# this ks speiclize for bond test
POST_SCRIPT_02 = """
EM1IP=$(ip -4 a show | awk -F " " '/inet/ { if (match($2, /^10.*/)) print $2 }' | awk -F "/" '{print $1}')
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

PRE_SCRIPT_02 = """
fetch /tmp/clean_disk http://{srv_ip}:{srv_port}/static/clean_disk.py
python /tmp/clean_disk
""".format(
    srv_ip=CURRENT_IP_PORT[0], srv_port=CURRENT_IP_PORT[1])

NOPXE_URL = "http://lab-01.rhts.eng.pek2.redhat.com:8000/nopxe/{0}"

CB_API = "http://10.73.60.74/cobbler_api"
CB_CREDENTIAL = ('cobbler', 'cobbler')
CB_PROFILE = CFGS['cb_profile']
ARGS_TPL = ('inst.ks=http://{srv_ip}:{srv_port}/static/auto/{ks_file} '
            '{addition_params}')
