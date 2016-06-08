"""
"""
# pylint: disable=W0403, C0103
import os
import logging.config
import base64
import yaml
from flask import Flask, request, redirect

from beaker import BeakerProvision, MonitorPubSub
from utils import init_redis, setup_funcs, ResultsAndLogs
from constants import CURRENT_IP_PORT, BUILDS_SERVER_URL
from jobs import JobRunner

# LOG_CONF = yaml.load(open(os.path.join(PROJECT_ROOT, 'logger.yml')))
# logging.config.dictConfig(LOG_CONF['logging'])
# LOG = logging.getLogger('bender')

RD_CONN = init_redis()

IP, PORT = CURRENT_IP_PORT
BEAKER = BeakerProvision(srv_ip=IP, srv_port=PORT)

results_logs = ResultsAndLogs()

app = Flask(__name__)


@app.route('/post_result/<code>')
def post_result(code):
    """todo"""
    if code == 'ok':
        pass
    elif code == 'no':
        pass
    else:
        pass
    return "r u happy"


@app.route('/start', methods=['POST'])
def start_job():
    """This method is the trigger function to start a automation test

    Args:
        img_url (str): /var/www/builds/rhevh/
        rhevh7-ng-36/rhev-hypervisor7-ng-3.6-20160518.0/
        rhev-hypervisor7-ng-3.6-20160518.0.x86_64.liveimg.squashfs

    """
    if request.method == 'POST':
        if RD_CONN.get("running") == "0":
            RD_CONN.set("running", 1)
            data = request.get_json()
            img_url = data.get('img', None)
            if img_url:
                _img_url = img_url.replace('/var/www/builds',
                                           BUILDS_SERVER_URL)

                JobRunner(_img_url, RD_CONN, results_logs).start()
                return redirect('/post_result')
        else:
            return redirect('/post_result')
    else:
        return redirect('/post_result')


@app.route('/done/<bkr_name>')
def done_job(bkr_name):
    """todo"""
    # LOG.info("publish message 'done to channel %s'", bkr_name)
    RD_CONN.publish(bkr_name, 'done')
    RD_CONN.publish("{0}-cockpit".format(bkr_name), "{0},{1},{2}".format(
        request.remote_addr, 'root', 'redhat'))
    return "done job"


@app.route('/upload/<stage>/<log_name>/<offset>')
def upload_anaconda_log(stage, log_name, offset):
    _data = request.get_json()
    data = base64.decodestring(_data['data'])
    log_file = os.path.join(results_logs.current_log_path, stage, log_name)
    log_path = os.path.dirname(log_file)
    if not os.path.exists(log_path):
        os.system("mkdir -p {}".format(log_path))

    if offset != '-1':
        with open(log_file, 'w') as fp:
            fp.seek(int(offset))
            fp.write(data)
            fp.flush()
    return "upload done"
