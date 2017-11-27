from fabric.api import env, settings, run, get, put
from fabric.exceptions import NetworkError, CommandTimeout
from fabric.network import disconnect_all
import re
import logging

log = logging.getLogger('bender')


class RemoteCmd(object):
    """"""

    def __init__(self, host_string, host_user, host_pass):
        self._host_string = host_string
        self._host_user = host_user
        self._host_pass = host_pass
        self.set_env()

    @property
    def host_string(self):
        return self._host_string

    @property
    def host_user(self):
        return self._host_user

    @property
    def host_pass(self):
        return self._host_pass

    def set_env(self):
        env.host_string = self.host_string
        env.user = self.host_user
        env.password = self.host_pass
        env.disable_known_hosts = True
        env.connection_attempts = 120

    def get_remote_file(self, remote_path, local_path):
        ret = get(remote_path, local_path)
        if not ret.succeeded:
            raise ValueError("Can't get {} from remote server:{}.".format(
                remote_path, env.host_string))

    def put_remote_file(self, local_path, remote_path):
        ret = put(local_path, remote_path)
        if not ret.succeeded:
            raise ValueError("Can't put {} to remote server:{}.".format(
                local_path, env.host_string))

    def run_cmd(self, cmd, timeout=60):
        ret = None
        try:
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

    def disconnect(self):
        disconnect_all()


if __name__ == '__main__':
    remotecmd = RemoteCmd('10.73.75.35', 'root', 'redhat')
    remotecmd.run_cmd("hostname")
