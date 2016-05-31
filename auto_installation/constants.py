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


SMOKE_TEST_LIST = ('FC_01')
P1_TEST_LIST = ('autopart', 'bond', 'FC', 'part')
ALL_TEST = ('*')
