import os
import logging
import yaml
import redis
import time

log = logging.getLogger('bender')


class ReserveUserWrongException(Exception):
    def __init__(self, message):
        super(ReserveUserWrongException,
              self).__init__('''System <{bkr_name}> must be reserved by \
User::<{user_name_r}>, but currently reserved by User::<{user_name_w}>'''
                             .format(**message))


def init_redis():
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    conn = redis.StrictRedis(connection_pool=pool)
    return conn


def get_current_ip_port():
    # TODO
    return '10.66.9.216', '5000'


def get_current_path():
    return os.path.dirname(__file__)


def init_kickstart_file(fn, args):
    with open(fn + '.tpl', 'r') as fp:
        tpl = fp.read()
        tpl = tpl.format(**args)
        with open(fn + '.ks', 'w') as fp:
            fp.write(tpl)


def setup_funcs(redis_conn):
    if not os.path.exists('./logs'):
        log.info("making dir 'logs' to store all test results")
        os.mkdir('logs')
    else:
        log.info("found dir 'logs' existed")

    log.info("flush all keys from current database")
    redis_conn.flushdb()
    log.info("set key 'running' value to '0'")
    redis_conn.set('running', 0, nx=True)


def generate_loger(img_url, conf_fp):
    dir_name = time.strftime("%Y-%m-%d", time.localtime())
    if not os.path.exists("logs/%s" % dir_name):
        os.mkdir("logs/%s" % dir_name)

    log_name = img_url.split('/')[-1]

    conf = yaml.load(open(conf_fp))
    
    conf['logging']['handlers']['logfile']['filename'] = "logs/%s/%s.log" % (
        dir_name, log_name)
        
    from pprint import pprint as pp
    pp(conf)
    logging.config.dictConfig(conf['logging'])
