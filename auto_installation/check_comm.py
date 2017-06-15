import logging
from fabric.api import settings, run, get, put
from fabric.exceptions import NetworkError, CommandTimeout
import re
from utils import get_checkpoint_cases_map

log = logging.getLogger('bender')


class CheckYoo(object):
    """"""

    def __init__(self):
        self._host_string = None
        self._host_user = None
        self._host_pass = None
        self._ksfile = None
        self._beaker_name = None

    @property
    def host_string(self):
        return self._host_string

    @host_string.setter
    def host_string(self, val):
        # TODO check val
        self._host_string = val

    @property
    def host_user(self):
        return self._host_user

    @host_user.setter
    def host_user(self, val):
        self._host_user = val

    @property
    def host_pass(self):
        return self._host_pass

    @host_pass.setter
    def host_pass(self, val):
        self._host_pass = val

    @property
    def beaker_name(self):
        return self._beaker_name

    @beaker_name.setter
    def beaker_name(self, val):
        self._beaker_name = val

    @property
    def ksfile(self):
        return self._ksfile

    @ksfile.setter
    def ksfile(self, val):
        self._ksfile = val

    def get_remote_file(self, remote_path, local_path):
        with settings(
                host_string=self.host_string,
                user=self.host_user,
                password=self.host_pass,
                disable_known_hosts=True,
                connection_attempts=120):
            ret = get(remote_path, local_path)
            if not ret.succeeded:
                raise ValueError("Can't get {} from remote server:{}.".format(
                    remote_path, self.host_string))

    def put_remote_file(self, local_path, remote_path):
        with settings(
                host_string=self.host_string,
                user=self.host_user,
                password=self.host_pass,
                disable_known_hosts=True,
                connection_attempts=120):
            ret = put(local_path, remote_path)
            if not ret.succeeded:
                raise ValueError("Can't put {} to remote server:{}.".format(
                    local_path, self.host_string))

    def run_cmd(self, cmd, timeout=60):
        ret = None
        try:
            with settings(
                    host_string=self.host_string,
                    user=self.host_user,
                    password=self.host_pass,
                    disable_known_hosts=True,
                    connection_attempts=60):
                ret = run(cmd, quiet=True, timeout=timeout)
                if ret.succeeded:
                    log.info('Run cmd "%s" succeeded', cmd)
                    return True, ret
                else:
                    log.error('Run cmd "%s" failed', cmd)
                    return False, ret
        except Exception as e:
            log.error('Run cmd "%s" failed with exception "%s"', cmd, e)
            return False, e

    def check_strs_in_file(self, fp, strs, timeout):
        log.info("start to check if %s in %s", strs, fp)
        try:
            ret = self.run_cmd('cat {}'.format(fp), timeout=timeout)
            log.info("Got result %s", ret)
        except CommandTimeout as e:
            log.error(e)
            return False

        if ret[0]:
            for s in strs:
                if s not in ret[1]:
                    log.error("can not found %s in %s", s, fp)
                    return False
            log.info("ks test %s is pass", fp)
            return True
        else:
            # log.error(ret[1])
            return False

    def check_strs_in_cmd_output(self, cmd, strs, timeout):
        log.info("start to check if %s in %s output", strs, cmd)
        try:
            ret = self.run_cmd(cmd, timeout=timeout)
            log.info("Got result %s", ret)
        except CommandTimeout as e:
            log.error(e)
            return False

        if ret[0]:
            for s in strs:
                if s not in ret[1]:
                    log.error("can not found %s in %s", s, cmd)
                    return False
            log.info("ks test %s is pass", cmd)
            return True
        else:
            # log.error(ret[1])
            return False

    def match_strs_in_cmd_output(self, cmd, patterns, timeout):
        log.info("start to match if %s in %s output", patterns, cmd)
        try:
            ret = self.run_cmd(cmd, timeout=timeout)
            color = re.compile(r'\x1B\[([0-9]{1,2}((;[0-9]{1,2})*)?)?[m|K]')
            newret = color.sub('', ret[1])
            log.info("Got result %s", (ret[0], newret))
        except CommandTimeout as e:
            log.error(e)
            return False

        if ret[0]:
            lines = newret.split('\r\n')
            for p in patterns:
                for line in lines:
                    if re.search(p, line.strip()):
                        break
                else:
                    log.error("can not match pattern %s in %s", p, cmd)
                    return False
            return True
        else:
            # log.error("run cmd %s failed", cmd)
            return False

    def call_func_by_name(self, name=''):
        func = getattr(self, name.lower(), None)
        if func:
            return func()
        else:
            raise NameError(
                'The checkpoint function {} is not defined'.format(name))

    def run_checkpoint(self, checkpoint, cases, cks):
        try:
            log.info("Start to run checkpoint:%s for cases:%s", checkpoint, cases)
            ck = self.call_func_by_name(checkpoint)
            if ck:
                newck = 'passed'
            else:
                newck = 'failed'
            for case in cases:
                cks[case] = newck
        except Exception as e:
            log.error(e)
        finally:
            log.info("Run checkpoint:%s for cases:%s finished.", checkpoint, cases)

    def run_cases(self):
        cks = {}
        try:
            # get checkpoint cases map
            checkpoint_cases_map = get_checkpoint_cases_map(self.ksfile,
                                                            self.beaker_name)

            # run check
            log.info("Start to run check points, please wait...")

            roll_back_cases = None
            for checkpoint, cases in checkpoint_cases_map.items():
                if checkpoint == "roll_back_check":
                    roll_back_cases = cases
                    continue
                self.run_checkpoint(checkpoint, cases, cks)
            if roll_back_cases:
                self.run_checkpoint("roll_back_check", roll_back_cases, cks)
        except Exception as e:
            log.error(e)

        return cks

    def go_check(self):
        pass



if __name__ == '__main__':
    pass
