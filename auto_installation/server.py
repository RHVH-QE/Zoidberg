"""
"""
# pylint: disable=W0403, C0103
import os
import base64

from flask import Flask, request, redirect

from .utils import init_redis, ResultsAndLogs, setup_funcs
from .constants import CURRENT_IP_PORT, BUILDS_SERVER_URL
from .jobs import job_runner

rd_conn = init_redis()
IP, PORT = CURRENT_IP_PORT
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
        if rd_conn.get("running") == "0":
            rd_conn.set("running", 1)
            data = request.get_json()
            img_url = data.get('img', None)
            if img_url:
                _img_url = img_url.replace('/var/www/builds',
                                           BUILDS_SERVER_URL)

                t = job_runner(_img_url, rd_conn, results_logs)
                t.setDaemon(True)
                t.start()
                return redirect('/post_result')
        else:
            return redirect('/post_result')
    else:
        return redirect('/post_result')


@app.route('/done/<em1ip>/<bkr_name>')
def done_job(em1ip, bkr_name):
    """todo"""
    print("Remote node ip is {}".format(em1ip))

    rd_conn.publish(bkr_name, 'done,{}'.format(em1ip))
    rd_conn.publish("{0}-cockpit".format(bkr_name),
                    "{0},{1},{2}".format(em1ip, 'root', 'redhat'))
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
