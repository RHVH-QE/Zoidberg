"""Here put all project level costants"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

KS_FILES_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                            'ngn-auto-installation-kickstarts')

KS_FILES_AUTO_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                                 'auto')

BUILDS_SERVER_URL = "http://10.66.10.22:8090"

CURRENT_IP_PORT = ('10.66.9.123', '5000')

STATIC_URL = ("http://{0}:{1}/"
              "static/ngn-auto-installation-kickstarts/%s").format(
                  CURRENT_IP_PORT[0], CURRENT_IP_PORT[1])

SMOKE_TEST_LIST = ('FC_01', )
P1_TEST_LIST = (
    'autopart',
    'bond',
    'FC',
    'part', )
ALL_TEST = ('*', )
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
    'services_01', )

DEBUG_LIST = ('FC_06', )

HOST_POOL = {
    'FC': ('dell-per510-01.lab.eng.pek2.redhat.com', ),
    'bond': (),
    'iscsi': (),
    'uefi': (),
    'vlan': (),
    'default': ('dell-pet105-01.qe.lab.eng.nay.redhat.com', ),
}

HOSTS = {
    "dell-pet105-01.qe.lab.eng.nay.redhat.com": {
        "nic": {
            "macaddress-enp2s0": "00:22:19:27:54:c7"
        },
        "hostname": "",
        "static_ip": "",
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
}

# Kickstart related stuff

POST_SCRIPT_01 = """
EM1IP=$(ip -o -4 addr show em2 | awk -F '[ /]+' '/global/ {print $4}')
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
CB_PROFILE = 'RHVH-4.0-73-20170104.0'
CB_SYSTEM = 'dell-pet105-01.qe.lab.eng.nay.redhat.com'
ARGS_TPL = ('inst.ks=http://{srv_ip}:{srv_port}/static/auto/{ks_file} '
            'inst.stage2=http://10.66.10.22:8090/'
            'rhvh_ngn/pxedir/RHVH-4.0-20170104.0-RHVH-x86_64-dvd1.iso/stage2')
