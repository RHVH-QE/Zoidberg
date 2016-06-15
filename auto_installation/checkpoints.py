import logging
from fabric.api import settings, run
from fabric.exceptions import NetworkError, CommandTimeout


log = logging.getLogger('bender')


class CheckYoo():
    """"""
    def __init__(self):
        self._host_string = None
        self._host_user = None
        self._host_pass = None

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

    def run_cmd(self, cmd, timeout=60):
        ret = None
        try:
            with settings(host_string=self.host_string,
                          user=self.host_user,
                          password=self.host_pass,
                          disable_known_hosts=True,):
                ret = run(cmd, quiet=True, timeout=timeout)
        except NetworkError as e:
            return False, e

        return True, ret


class CheckCheck(CheckYoo):
    """"""
    def go_check(self, name):
        return getattr(self, name)()

    def bond_01(self):
        log.info("")
        ret = self.run_cmd('cat /etc/sysconfig/network-scripts/ifcfg-bond00',
                           timeout=300)
        if ret[0]:
            if 'DEVICE=bond00' in ret[1] and \
               'miimon=100 mode=balance-rr' in ret[1]:
                return True
            else:
                return False
        else:
            # TODO
            return


if __name__ == '__main__':
    ck = CheckCheck()
    ck.host_string, ck._host_user, ck.host_pass = ('10.73.75.219',
                                                   'root',
                                                   'redhat')
    print ck.go_check('bond_01')
