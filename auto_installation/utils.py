import os
import re
import logging.config
import yaml
import redis
import time
import subprocess as sp
from constants import PROJECT_ROOT, \
    ANACONDA_TIER1, ANACONDA_TIER2, KS_TIER1, KS_TIER2, \
    TEST_LEVEL, \
    ANACONDA_TIER1_TESTCASE_MAP, ANACONDA_TIER2_TESTCASE_MAP, \
    KS_TIER1_TESTCASE_MAP, KS_TIER2_TESTCASE_MAP, \
    KS_PRESSURE_MAP
import json

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
        self._img_url = None
        self.logger_conf = os.path.join(PROJECT_ROOT, 'logger.yml')
        self._logger_name = "results"
        self.logger_dict = self.conf_to_dict()
        self._current_log_path = "/tmp/logs"
        self._current_log_file = "/tmp/logs"

    @property
    def img_url(self):
        return self._img_url
    
    @img_url.setter
    def img_url(self, val):
        self._img_url = val

    @property
    def logger_name(self):
        return self._logger_name

    @logger_name.setter
    def logger_name(self, val):
        self._logger_name = val

    @property
    def current_log_path(self):
        return self._current_log_path

    @property
    def current_log_file(self):
        return self._current_log_file

    def get_current_date(self):
        return time.strftime("%Y-%m-%d", time.localtime())

    def conf_to_dict(self):
        return yaml.load(open(self.logger_conf))

    def parse_img_url(self):
        return self.img_url.split('/')[-2]

    def get_actual_logger(self, ks_name=''):
        log_file = os.path.join(PROJECT_ROOT, 'logs',
                                self.get_current_date(),
                                self.parse_img_url(), ks_name,
                                self.logger_name)
        if not os.path.exists(log_file):
            os.system("mkdir -p {0}".format(os.path.dirname(log_file)))

        self._current_log_path = os.path.dirname(log_file)
        self._current_log_file = log_file

        self.logger_dict['logging']['handlers']['logfile'][
            'filename'] = log_file

        logging.config.dictConfig(self.logger_dict['logging'])

    def del_existing_logs(self, ks_name=''):
        log_file = os.path.join(PROJECT_ROOT, 'logs',
                                self.get_current_date(),
                                self.parse_img_url(), ks_name)
        if os.path.exists(log_file):
            os.system('rm -rf {}/*'.format(log_file))
    
    def _parse_results(self, res):
        ks = res.split('/')[-2]
        if ks in KS_PRESSURE_MAP:
            num = int(KS_PRESSURE_MAP[ks])
        else:
            num = 1

        p1 = re.compile(r"{'RHEVM-\d")
        p2 = re.compile(r'InitiatorName=iqn')
        rets = []
        iqns = []
        for line in open(res):
            if p1.search(line):
                rets.append(eval(line.split("::")[-1]))
            if p2.search(line):
                iqns.append(line.split(":")[-1].rstrip("')\n"))

        retNum = len(rets)
        if retNum != num:
            newret = {}
        else:
            newret = rets[0]
            if num > 1:
                for ret in rets[1:]:
                    for k in newret:
                        newret[k] = newret[k] and ret[k]

                if len(iqns) == num and len(set(iqns)) != num:
                    testcase_map = get_testcase_map()
                    for k, v in testcase_map.items():
                        if 'iqn_check' in v and k in newret:
                            newret[k] = False
                            break
        return newret

    def gen_final_results(self):
        build = self.parse_img_url()
        log_root_path = os.path.join(PROJECT_ROOT, 'logs',
                                     self.get_current_date(),
                                     build)
        if not os.path.exists(log_root_path):
            return
        
        final_results = {build: {}}
        actual_run_cases = []
        pass_num = 0
        failed_num = 0
        for a, b, c in os.walk(log_root_path):
            for ks in b:
                ret = self._parse_results(os.path.join(a, ks, 'checkpoints'))
                final_results[build][ks] = ret
                actual_run_cases.extend(list(ret.keys()))
                values = list(ret.values())
                pass_num = pass_num + values.count('passed')
                failed_num = failed_num + values.count('failed')
            break
        
        need_run_cases = list(get_testcase_map().keys())
        final_results['sum']['build'] = build
        final_results['sum']['total'] = len(need_run_cases)
        final_results['sum']['pass'] = pass_num
        final_results['sum']['failed'] = failed_num
        final_results['sum']['error'] = len(need_run_cases) - len(actual_run_cases)
        final_results['sum']['errorlist'] = list(set(need_run_cases) - set(actual_run_cases))
        
        final_results_jfile = os.path.join(log_root_path, 'final_results.json')
        with open(final_results_jfile, 'w') as json_file:
            json_file.write(json.dumps(final_results, sort_keys=True, indent =4))


def init_redis():
    pool = redis.ConnectionPool(
        host='localhost', port=6379, db=0, password='redhat')
    conn = redis.StrictRedis(connection_pool=pool)
    return conn


def get_current_ip_port():
    # TODO
    return '10.66.11.155', '5000'


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


def get_testcase_map():
    # get testcase map
    testcase_map = {}
    if TEST_LEVEL & ANACONDA_TIER1:
        testcase_map.update(ANACONDA_TIER1_TESTCASE_MAP)
    if TEST_LEVEL & ANACONDA_TIER2:
        testcase_map.update(ANACONDA_TIER2_TESTCASE_MAP)
    if TEST_LEVEL & KS_TIER1:
        testcase_map.update(KS_TIER1_TESTCASE_MAP)
    if TEST_LEVEL & KS_TIER2:
        testcase_map.update(KS_TIER2_TESTCASE_MAP)

    if not testcase_map:
        raise ValueError('Invaild TEST_LEVEL')

    return testcase_map


def get_machine_ksl_map():
    machine_ksl_map = {}
    testcase_map = get_testcase_map()
    for value in testcase_map.itervalues():
        ks = value[0]
        machine = value[1]
        flag = False
        if machine in machine_ksl_map:
            if ks not in machine_ksl_map.get(machine):
                flag = True
        else:
            machine_ksl_map[machine] = []
            flag = True

        if flag:
            if ks in KS_PRESSURE_MAP:
                ks_repeat_ls = [ks] * int(KS_PRESSURE_MAP.get(ks))
                machine_ksl_map[machine].extend(ks_repeat_ls)
            else:
                machine_ksl_map[machine].append(ks)
    for k in machine_ksl_map:
        machine_ksl_map[k].sort()

    return machine_ksl_map


def get_ks_machine_map():
    ks_mashine_map = {}
    testcase_map = get_testcase_map()
    for value in testcase_map.itervalues():
        ks = value[0]
        machine = value[1]
        if ks in ks_mashine_map:
            if machine != ks_mashine_map.get(ks):
                raise ValueError(
                    'One kickstart file cannot be run on two machines.')
        else:
            ks_mashine_map[ks] = machine

    return ks_mashine_map


def get_checkpoint_cases_map(ks, mc):
    # get testcase map
    testcase_map = get_testcase_map()

    checkpoint_cases_map = {}
    for key, value in testcase_map.items():
        if set((ks, mc)) < set(value):
            checkpoint = value[2]
            if checkpoint in checkpoint_cases_map:
                checkpoint_cases_map[checkpoint].append(key)
            else:
                checkpoint_cases_map[checkpoint] = []
                checkpoint_cases_map[checkpoint].append(key)

    return checkpoint_cases_map


def get_lastline_of_file(file_path):
    return sp.check_output(['tail', '-1', file_path])


if __name__ == '__main__':
    pass
