import logging.config

import yaml
from flask import Flask, request, redirect
from flask.ext import resteasy

from auto_installation.beaker import BeakerProvision, MonitorPubSub
from utils import init_redis, get_current_ip_port

log_conf = yaml.load(open('./logger.yml'))
logging.config.dictConfig(log_conf['logging'])
log = logging.getLogger('bender')
redis_conn = init_redis()

IP, PORT = get_current_ip_port()

app = Flask(__name__)
api = resteasy.Api(app)


@app.route('/happy')
def happy():
    return "r u happy"


@app.route('/start', methods=['POST'])
def start_job():
    if request.method == 'POST':
        data = request.get_json()
        print data
        return redirect('/happy')
    else:
        return redirect('/happy')


@app.route('/add/<bkr_name>')
def add_job(bkr_name):
    log.info('start provisioning on host %s' % bkr_name)
    ret = BeakerProvision(srv_ip=IP, srv_port=PORT).provision(bkr_name)

    if ret == 0:
        log.info("provisioning on host %s finished with return code 0" % bkr_name)
        p = redis_conn.pubsub(ignore_subscribe_messages=True)
        log.info("subscribe channel %s" % bkr_name)
        p.subscribe(bkr_name)
        log.info("start daemon thread to listen on channel %s" % bkr_name)
        MonitorPubSub(bkr_name, p).start()
        return "add job success"
    else:
        log.error("provisioning on host %s failed with return code %s" % (bkr_name, ret))
        return "add job fail"


@app.route('/done/<bkr_name>')
def done_job(bkr_name):
    log.info("publish message 'done to channel %s'" % bkr_name)
    redis_conn.publish(bkr_name, 'done')
    return "done job"


if __name__ == '__main__':
    app.run('0.0.0.0', debug=False)
