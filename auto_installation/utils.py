import os
import logging
import redis

log = logging.getLogger('bender')


class ReserveUserWrongException(Exception):
    def __init__(self, message):
        super(ReserveUserWrongException, self).__init__('''System <{bkr_name}> must be reserved by \
User::<{user_name_r}>, but currently reserved by User::<{user_name_w}>'''.format(**message))


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
    with open(fn+'.tpl', 'r') as fp:
        tpl = fp.read()
        tpl = tpl.format(**args)
        with open(fn+'.ks', 'w') as fp:
            fp.write(tpl)


def setup_funcs(redis_conn):
    log.info("flush all keys from current database")
    redis_conn.flushdb()
    log.info("set key 'running' value to '0'")
    redis_conn.set('running', 0, nx=True)
