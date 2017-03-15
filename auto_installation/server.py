from __future__ import unicode_literals
# pylint: disable=W0403, C0103
import os
import base64
import json

from flask import Flask, request, redirect, abort
from flask_socketio import SocketIO, emit

from .utils import init_redis, ResultsAndLogs, setup_funcs, get_lastline_of_file
from .constants import CURRENT_IP_PORT, BUILDS_SERVER_URL, CB_PROFILE, HOSTS, TEST_LEVEL, PROJECT_ROOT
from .jobs import job_runner
from .cobbler import Cobbler
from .mongodata import MongoQuery
from .celerytask import RhvhTask

rd_conn = init_redis()
IP, PORT = CURRENT_IP_PORT
results_logs = ResultsAndLogs()
mongo = MongoQuery()
rt = RhvhTask()

app = Flask(__name__)
socketio = SocketIO(app)


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
            return redirect('/goaway')
    else:
        abort(406)


@app.route('/goaway', methods=['GET'])
def goaway():
    return "automation test already running, please goaway"


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


# =========== websocket api ===================================================


@socketio.on('status')
def get_curretn_status(msg):
    ret = {
        'cb_profile': CB_PROFILE,
        'running': rd_conn.get("running"),
        'test_level': TEST_LEVEL,
        'hosts': HOSTS
    }
    emit('currentStatus', ret)


@socketio.on('build')
def get_current_build(msg):
    build_path = results_logs.current_log_path
    log_file = results_logs.current_log_file
    ret = {'path': build_path, 'log': get_lastline_of_file(log_file)}
    emit('currentBuild', ret)


@socketio.on('pxe_profiles')
def get_pxe_profiles(msg):
    with Cobbler() as cb:
        emit('pxeProfiles', cb.profiles)


@socketio.on('rhvh_builds')
def get_rhvh_builds(msg):
    emit('rhvhBuilds', mongo.rhvh_build_names(msg))


@socketio.on('bkr_machines')
def get_bkr_machines(msg):
    emit('bkrMachines', mongo.machines(msg))


@socketio.on('pre_auto')
def pre_auto_job(msg):
    ts_level = sum([int(i) for i in msg['tslevel']])
    pxe = msg['pxe']
    build = msg['build']

    cfg = os.path.join(PROJECT_ROOT, 'auto_installation', 'constants.json')
    cfg_ = None

    with open(cfg) as fp:
        cfg_ = json.load(fp)
        cfg_['cb_profile'] = pxe
        cfg_['test_level'] = ts_level
    with open(cfg, 'w') as fp:
        json.dump(cfg_, fp)

    rt.lanuchAuto(build, pxe, ts_level)


if __name__ == '__main__':
    pass
