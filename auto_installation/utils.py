import os
import logging
import logging.config
import yaml
import redis
import time
from constants import PROJECT_ROOT

log = logging.getLogger('bender')


class ReserveUserWrongException(Exception):
    def __init__(self, message):
        super(ReserveUserWrongException,
              self).__init__('''System <{bkr_name}> must be reserved by \
User::<{user_name_r}>, but currently reserved by User::<{user_name_w}>'''
                             .format(**message))


class ResultsAndLogs(object):
    """This class will prepare logs directory structure
    """

    def __init__(self):

        self._logs_root_dir = os.path.join(PROJECT_ROOT, 'logs')
        self.img_url = None
        self.logger_conf = os.path.join(PROJECT_ROOT, 'logger.yml')
        self.logger_name = "results"
        self.logger_dict = self.conf_to_dict()
        self._current_log_path = "/tmp/logs"

    @property
    def current_log_path(self):
        return self._current_log_path

    def get_current_date(self):
        return time.strftime("%Y-%m-%d", time.localtime())

    def conf_to_dict(self):
        return yaml.load(open(self.logger_conf))

    def parse_img_url(self, img_url):
        return img_url.split('/')[-2]

    def get_actual_logger(self, img_url, ks_name=''):
        log_file = os.path.join(PROJECT_ROOT, 'logs', self.get_current_date(),
                                self.parse_img_url(img_url), ks_name,
                                self.logger_name)
        if not os.path.exists(log_file):
            os.system("mkdir -p {0}".format(os.path.dirname(log_file)))

        self._current_log_path = os.path.dirname(log_file)

        self.logger_dict['logging']['handlers']['logfile'][
            'filename'] = log_file

        logging.config.dictConfig(self.logger_dict['logging'])


def init_redis():
    pool = redis.ConnectionPool(host='localhost', port=6379,
                                db=0, password='redhat')
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
    print("flush all keys from current database")
    redis_conn.flushdb()
    print("set key 'running' value to '0'")
    redis_conn.set('running', 0, nx=True)


if __name__ == '__main__':
    pass
