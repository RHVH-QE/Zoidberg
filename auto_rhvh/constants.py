"""Here put all project level costants"""
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

cfgjson = os.path.join(PROJECT_ROOT, 'auto_rhvh', 'constants.json')

if os.path.exists(cfgjson):
    CFGS = json.load(open(cfgjson))
else:
    CFGS = {"test_level": 1,
            "target_build": '',
            "cb_profile": ''}

TEST_LEVEL = CFGS['test_level']

KS_FILES_DIR = os.path.join(PROJECT_ROOT, 'auto_rhvh', 'static', 'ksfiles')

KS_FILES_AUTO_DIR = os.path.join(PROJECT_ROOT, 'auto_rhvh', 'static', 'auto')

BUILDS_SERVER_URL = "http://10.66.10.22:8090"

CURRENT_IP_PORT = ('10.73.73.23', '5000')

LOG_URL = "http://10.73.73.23:7788"

COVERAGE_TEST = False

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

#fetch /tmp/anamon http://{srv_ip}:{srv_port}/static/anamon.py
#python /tmp/anamon --server {srv_ip} --port {srv_port} --stage pre

fetch /tmp/clean_disk http://{srv_ip}:{srv_port}/static/ksfiles/clean_disk.py
python /tmp/clean_disk
""".format(
    srv_ip=CURRENT_IP_PORT[0], srv_port=CURRENT_IP_PORT[1])

COVERAGE_SNIPPET = """coverage_check(){{\\
easy_install coverage\\
export COVERAGE_FILE=/boot/.coverage.install\\
coverage run -p -m --branch --source=/usr/lib/python2.7/site-packages/imgbased imgbased layout --init\\
filename=`find /boot -name .coverage.install*`\\
curl -s -X POST http://10.73.73.23:7789/upload/{} \\\
-F "file=@${{filename}}" \\\
-H "Content-Type: multipart/form-data" > /dev/null\\
}}\\
coverage_check\\"""

SED_COVERGE = """sed -i '/^imgbase/c\\
{}
' {}
"""

NOPXE_URL = "http://lab-01.rhts.eng.pek2.redhat.com:8000/nopxe/{0}"

CB_API = "http://10.73.60.74/cobbler_api"
CB_CREDENTIAL = ('cobbler', 'cobbler')
CB_PROFILE = CFGS['cb_profile']
ARGS_TPL = ('inst.ks=http://{srv_ip}:{srv_port}/static/auto/{ks_file} '
            '{addition_params}')
