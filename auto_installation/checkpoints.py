import logging
from fabric.api import settings, run
from fabric.exceptions import NetworkError, CommandTimeout

log = logging.getLogger('bender')


class CheckYoo(object):
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
            with settings(
                    host_string=self.host_string,
                    user=self.host_user,
                    password=self.host_pass,
                    disable_known_hosts=True,
                    connection_attempts=60):
                ret = run(cmd, quiet=True, timeout=timeout)
                if ret.succeeded:
                    return True, ret
                else:
                    return False, ret
        except NetworkError as e:
            return False, e

        return True, ret

    def check_strs_in_file(self, fp, strs, timeout):
        log.info("start to check if %s in %s", strs, fp)
        try:
            ret = self.run_cmd('cat {}'.format(fp), timeout=timeout)
        except CommandTimeout as e:
            log.error(e)
            return False

        log.info("Got result %s", ret)
        if ret[0]:
            for s in strs:
                if s not in ret[1]:
                    log.error("can not found %s in %s", s, fp)
                    return False
            log.info("ks test %s is pass", fp)
            return True
        else:
            log.error(ret[1])
            return False

    def check_strs_in_cmd_output(self, cmd, strs, timeout):
        log.info("start to check if %s in %s output", strs, cmd)
        try:
            ret = self.run_cmd(cmd, timeout=timeout)
            log.info(ret)
        except CommandTimeout as e:
            log.error(e)
            return False

        log.info("Got result %s", ret)
        if ret[0]:
            for s in strs:
                if s not in ret[1]:
                    log.error("can not found %s in %s", s, cmd)
                    return False
            log.info("ks test %s is pass", cmd)
            return True
        else:
            log.error(ret[1])
            return False


class CheckCheck(CheckYoo):
    """"""

    def go_check(self, name):
        func = getattr(self, name.lower(), None)
        if func:
            return func()
        else:
            return self.default()

    def bond_01(self):
        return self.check_strs_in_file(
            '/etc/sysconfig/network-scripts/ifcfg-bond00',
            ('DEVICE=bond00', 'miimon=100 mode=balance-rr'),
            timeout=300)

    def fc_01(self):
        ck01 = self.check_strs_in_cmd_output(
            'fdisk -l | grep "Linux LVM"', 'LVM', timeout=300)
        ck02 = self.check_strs_in_cmd_output('lvs', '4.00g', timeout=300)

        return ck01 and ck02

    def firewall_01(self):
        return self.check_strs_in_cmd_output(
            'firewall-cmd --state', 'running', timeout=300)

    def iscsi_01(self):
        ck01 = self.check_strs_in_cmd_output(
            'fdisk -l | grep "Linux LVM"', 'LVM', timeout=300)
        return ck01

    def network_01(self):
        ck01 = self.check_strs_in_file(
            '/etc/sysconfig/network-scripts/ifcfg-em1', ('BOOTPROTO=dhcp', ),
            timeout=300)

        return ck01

    def selinux_01(self):
        return self.check_strs_in_cmd_output(
            'cat /etc/selinux/config', 'SELINUX=enforcing', timeout=300)

    def services_01(self):
        ck01 = self.check_strs_in_cmd_output(
            'systemctl status sshd', 'active', timeout=300)
        return ck01

    def default(self):
        log.info(
            "perform basic check, installation is finished, reboot is success")
        ck01 = True
        return ck01


if __name__ == '__main__':
    # 10.73.75.219
    ck = CheckCheck()
    ck.host_string, ck._host_user, ck.host_pass = ('10.73.75.228', 'root',
                                                   'redhat')
    print(ck.go_check('bond_01'))
