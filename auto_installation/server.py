from __future__ import unicode_literals
# pylint: disable=W0403, C0103
import os
import base64
import json
import utils

from flask import Flask, request, redirect, abort, jsonify
from flask_cors import CORS

from .utils import init_redis, setup_funcs, get_lastline_of_file
from .constants import CURRENT_IP_PORT, BUILDS_SERVER_URL, CB_PROFILE, HOSTS, TEST_LEVEL, PROJECT_ROOT
from .jobs import job_runner
from .cobbler import Cobbler
from .mongodata import MongoQuery
from .celerytask import RhvhTask
from .reports import ResultsToPolarion

rd_conn = init_redis()
IP, PORT = CURRENT_IP_PORT
# ensure singleton instance
results_logs = utils.results_logs
mongo = MongoQuery()
rt = RhvhTask()

app = Flask(__name__)
CORS(app, resources=r'/api/*')


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

                results_logs.img_url = _img_url

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
@app.route('/done/<em1ip>/<bkr_name>/<cockpit>')
def done_job(em1ip, bkr_name, cockpit=None):
    """todo"""
    if cockpit is None:
        print("Remote node ip is {}".format(em1ip))

        rd_conn.publish(bkr_name, 'done,{}'.format(em1ip))
        rd_conn.publish("{0}-cockpit".format(bkr_name), "{0},{1},{2}".format(
            em1ip, 'root', 'redhat'))
        return "done job"
    else:
        print("Remote node ip is {}".format(em1ip))

        rd_conn.publish(bkr_name, 'done,{}'.format(em1ip))
        rd_conn.publish("{0}-cockpit".format(bkr_name), "{0},{1},{2}".format(
            em1ip, 'root', 'redhat'))
        print("prepare cockpit testing")

        cockpit_cfg = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                                   'cockpit.json')
        cockpit_cfg_ = None
        with open(cockpit_cfg) as fp:
            cockpit_cfg_ = json.load(fp)
            cockpit_cfg_['host_ip'] = em1ip
        with open(cockpit_cfg, 'w') as fp:
            json.dump(cockpit_cfg_, fp)
        rt.lanuchCockpitAuto()
        return "cockpit done job"


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


# =========== api section =====================================================


@app.route('/api/v1/current/status')
def get_current_status():
    ret = {
        'cb_profile': CB_PROFILE,
        'running': rd_conn.get("running"),
        'test_level': TEST_LEVEL,
        'hosts': HOSTS
    }
    return jsonify(ret)


@app.route('/api/v1/current/build')
def get_current_build():
    build_path = results_logs.current_log_path
    log_file = results_logs.current_log_file
    ret = {'path': build_path, 'log': get_lastline_of_file(log_file)}
    return jsonify(ret)


@app.route('/api/v1/pxe/profiles')
def get_pxe_profiles():
    with Cobbler() as cb:
        return jsonify(cb.profiles)


@app.route('/api/v1/rhvh_builds/<qname>')
def get_rhvh_builds(qname):
    return jsonify(mongo.rhvh_build_names(qname))


@app.route('/api/v1/bkr_machines')
def get_bkr_machines():
    return jsonify(mongo.machines())


@app.route('/api/v1/autojob/lanuch', methods=['POST'])
def auto_job_lanuch():
    if request.method == 'POST':
        msg = request.get_json()
        ts_level = sum([int(i) for i in msg['tslevel']])
        pxe = msg['pxe']
        build = msg['build']
        target_build = msg['target_build']

        cfg = os.path.join(PROJECT_ROOT, 'auto_installation', 'constants.json')
        cfg_ = None

        with open(cfg) as fp:
            cfg_ = json.load(fp)
            cfg_['cb_profile'] = pxe
            cfg_['test_level'] = ts_level
            cfg_['target_build'] = target_build
        with open(cfg, 'w') as fp:
            json.dump(cfg_, fp)
        # abort(401)
        rt.lanuchAuto(build, pxe, ts_level, target_build)
        return jsonify("job is launched")


@app.route('/api/v1/autojob/last_result')
def get_last_result():
    ret_none = {
        "sum": {
            "build": "",
            "error": -1,
            "errorlist": [],
            "failed": -1,
            "passed": -1,
            "total": -1
        }
    }
    log_path = os.path.dirname(results_logs.current_log_path)
    try:
        ResultsToPolarion(log_path, '-l').run()
    except IOError as e:
        print(e)
        return jsonify(ret_none)

    result_file = os.path.join(log_path, 'final_results.json')

    if not os.path.exists(result_file):
        return jsonify(ret_none)
    else:
        res = json.load(open(result_file))
        res.update({'logpath': log_path})
        return jsonify(res)


@app.route('/api/v1/cockpit/tslevel')
def get_cockpit_tslevel():
    cockpit_tslevle_fp = os.path.join(PROJECT_ROOT, 'auto_installation',
                                      'test_scen.json')
    return jsonify(json.load(open(cockpit_tslevle_fp)))


@app.route('/api/v1/cockpit/lanuch', methods=['POST'])
def cockpit_job_lanuch():
    if request.method == 'POST':
        msg = request.get_json()
        ts_level = sum([int(i) for i in msg['tslevel']])
        pxe = msg['pxe']
        build = msg['build']
        target_build = msg['target_build']
        test_profile = msg['cases']

        cfg = os.path.join(PROJECT_ROOT, 'auto_installation', 'constants.json')
        cfg_ = None

        cockpit_cfg = os.path.join(PROJECT_ROOT, 'auto_installation', 'static',
                                   'cockpit.json')
        cockpit_cfg_ = None

        with open(cfg) as fp:
            cfg_ = json.load(fp)
            cfg_['cb_profile'] = pxe
            cfg_['test_level'] = ts_level
            cfg_['target_build'] = target_build
        with open(cfg, 'w') as fp:
            json.dump(cfg_, fp)

        with open(cockpit_cfg) as fp:
            cockpit_cfg_ = json.load(fp)
            cockpit_cfg_['test_profile'] = test_profile
            cockpit_cfg_['host_ip'] = ""
            cockpit_cfg_['test_build'] = build
        with open(cockpit_cfg, 'w') as fp:
            json.dump(cockpit_cfg_, fp)
        # rt.lanuchAuto(build, pxe, ts_level, target_build)
        return jsonify("cockpit job is launched")


if __name__ == '__main__':
    pass
