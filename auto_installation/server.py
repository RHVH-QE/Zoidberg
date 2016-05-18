"""
"""
# pylint: disable=W0403, C0103

import logging.config

import yaml
from flask import Flask, request, redirect
from flask.ext import resteasy

from beaker import BeakerProvision, MonitorPubSub
from utils import init_redis, setup_funcs, generate_loger
from constants import CURRENT_IP_PORT, BUILDS_SERVER_URL
from jobs import JobRunner

LOG_CONF = yaml.load(open('./logger.yml'))
logging.config.dictConfig(LOG_CONF['logging'])
LOG = logging.getLogger('bender')
RD_CONN = init_redis()

IP, PORT = CURRENT_IP_PORT
BEAKER = BeakerProvision(srv_ip=IP, srv_port=PORT)

app = Flask(__name__)
api = resteasy.Api(app)


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
    """todo"""
    if request.method == 'POST':
        if RD_CONN.get("running") == "0":
            RD_CONN.set("running", 1)
            data = request.get_json()
            img_url = data.get('img', None)
            if img_url:
                _img_url = img_url.replace('/var/www/builds',
                                           BUILDS_SERVER_URL)
                generate_loger(_img_url, './logger.yml')
                LOG.info("start testing rhevh build :: %s", _img_url)
                # JobRunner(_img_url, RD_CONN).start()
                return redirect('/post_result')
        else:
            return redirect('/post_result')
    else:
        return redirect('/post_result')


@app.route('/add/<bkr_name>')
def add_job(bkr_name):
    """todo"""
    LOG.info("start provisioning on host %s", bkr_name)
    ret = BeakerProvision(srv_ip=IP, srv_port=PORT).provision(bkr_name)

    if ret == 0:
        LOG.info("provisioning on host %s finished with return code 0",
                 bkr_name)
        p = RD_CONN.pubsub(ignore_subscribe_messages=True)
        LOG.info("subscribe channel %s", bkr_name)
        p.subscribe(bkr_name)
        LOG.info("start daemon thread to listen on channel %s", bkr_name)
        MonitorPubSub(bkr_name, p).start()
        return "add job success"
    else:
        LOG.error("provisioning on host %s failed with return code %s",
                  bkr_name, ret)
        return "add job fail"


@app.route('/done/<bkr_name>')
def done_job(bkr_name):
    """todo"""
    LOG.info("publish message 'done to channel %s'", bkr_name)
    RD_CONN.publish(bkr_name, 'done')
    return "done job"
