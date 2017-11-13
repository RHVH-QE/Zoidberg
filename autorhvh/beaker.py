import attr
import json
import subprocess
import time
import logging
from threading import Thread
from .cobbler import Cobbler
from .utils import ReserveUserWrongException, init_redis

log = logging.getLogger("Beaker")


@attr.s
class WatchInstallation(object):
    ch_name = attr.ib()
    p = attr.ib()
    redis_conn = attr.ib(default=init_redis())

    def watch(self):
        now = time.time()
        while True:
            msg = self.p.get_message(ignore_subscribe_messages=True)
            log.info("waiting for installation message")
            if msg:
                log.info("get message from channel %s: %s", self.ch_name, msg)
                with Cobbler() as cb:
                    log.info("remove system %s from cobbler", self.ch_name)
                    cb.remove_system(self.ch_name)
                self.redis_conn.publish(self.ch_name, msg['data'])
                break
            elif (time.time() - now > 1200):
                log.error("provision job is time-out after 20min")
                self.redis_conn.publish(self.ch_name, 'fail')
                break
            time.sleep(10)


def inst_watcher(ch_name, p):
    ins = WatchInstallation(ch_name, p)
    return Thread(target=ins.watch)


@attr.s
class Beaker(object):

    CMDs = dict(
        # this cmd will provision the given host with rhevh ngn build
        provision=("bkr system-provision "
                   "--kernel-options "
                   "inst.stage2=http://10.66.10.22:8090/"
                   "rhevh/ngn-dvd-iso/RHVH-7.2-20160718.1/stage2 "
                   "inst.ks=http://{srv_ip}:{srv_port}/ksfiles/auto/{ks_file} "
                   "ks= "
                   "--distro-tree {distro_tree_id} {bkr_name}"),

        # this cmd will make sure the given host boot from local disk
        clear_netboot=("bkr system-power "
                       "--action none "
                       "--clear-netboot {bkr_name}"),
        power_on=("bkr system-power "
                  "--action on {bkr_name}"),
        power_off=("bkr system-power "
                   "--action off {bkr_name}"),
        reboot=("bkr system-power "
                "--action reboot {bkr_name}"),
        reserve="bkr system-reserve {bkr_name}",
        release="bkr system-release {bkr_name}",
        status="bkr system-status {bkr_name} --format json")

    srv_ip = attr.ib(default="0.0.0.0")
    srv_port = attr.ib(default=5000)
    ks_file = attr.ib(default="")

    def _exec_cmd(self, cmd, bkr_name, args, output=False):
        _cmd = self.CMDs[cmd].format(**args)
        if not output:
            ret = subprocess.call(_cmd, shell=True)
            return ret
        else:
            ret = subprocess.check_output(_cmd, shell=True)
            return ret

    def power_on(self, bkr_name):
        """pass"""
        return self._exec_cmd('power_on', bkr_name, dict(bkr_name=bkr_name))

    def power_off(self, bkr_name):
        """pass"""
        return self._exec_cmd('power_off', bkr_name, dict(bkr_name=bkr_name))

    def reboot(self, bkr_name):
        """pass"""
        return self._exec_cmd('reboot', bkr_name, dict(bkr_name=bkr_name))

    def provision(self, bkr_name, distro_tree_id='71758'):
        """pass"""
        return self._exec_cmd(
            'provision',
            bkr_name,
            dict(
                bkr_name=bkr_name,
                distro_tree_id=distro_tree_id,
                ks_file=self.ks_file,
                srv_ip=self.srv_ip,
                srv_port=self.srv_port))

    def reserve(self, bkr_name):
        """pass"""
        return self._exec_cmd('reserve', bkr_name, dict(bkr_name=bkr_name))

    def release(self, bkr_name):
        """pass"""
        return self._exec_cmd('release', bkr_name, dict(bkr_name=bkr_name))

    def status(self, bkr_name):
        """pass"""
        ret = self._exec_cmd(
            'status', bkr_name, dict(bkr_name=bkr_name), output=True)
        data = json.loads(ret)
        if data['current_reservation']:
            if data['current_reservation']['user_name'] == 'yaniwang':
                return True
            else:
                raise ReserveUserWrongException(
                    dict(
                        bkr_name=bkr_name,
                        user_name_r='yaniwang',
                        # pylint: disable=C0301
                        user_name_w=data['current_reservation']['user_name']))
        else:
            return False


if __name__ == '__main__':
    bk = Beaker()

    bk.reboot("dell-pet105-01.qe.lab.eng.nay.redhat.com")
