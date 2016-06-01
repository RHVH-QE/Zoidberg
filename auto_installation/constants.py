"""Here put all project level costants"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

KS_FILES_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                            'ngn-auto-installation-kickstarts')

KS_FILES_AUTO_DIR = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                                 'auto')

BUILDS_SERVER_URL = "http://10.66.10.22:8090"

CURRENT_IP_PORT = ('10.66.9.216', '5000')

STATIC_URL = "http://{0}:{1}/static/ngn-auto-installation-kickstarts/%s".format(
    CURRENT_IP_PORT[0], CURRENT_IP_PORT[1])

SMOKE_TEST_LIST = ('FC_01', )
P1_TEST_LIST = ('autopart',
                'bond',
                'FC',
                'part', )
ALL_TEST = ('*', )

HOST_POOL = {
    'FC': ('dell-per510-01.lab.eng.pek2.redhat.com', ),
    'bond': (),
    'iscsi': (),
    'uefi': (),
    'vlan': (),
    'default': ('dell-per510-01.lab.eng.pek2.redhat.com', ),
}

# Kickstart related stuff

POST_SCRIPT_01 = "curl -s http://{}:{}/done/%s".format(CURRENT_IP_PORT[0],
                                                       CURRENT_IP_PORT[1])

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
python /tmp/anamon --server {srv_ip} --port {srv_port}

""".format(srv_ip=CURRENT_IP_PORT[0], srv_port=CURRENT_IP_PORT[1])
