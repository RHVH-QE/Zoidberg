"""to write
"""
import time
import json
import subprocess
import logging
from utils import init_redis, ReserveUserWrongException
from threading import Thread

redis_conn = init_redis()
log = logging.getLogger('bender')


class MonitorPubSub(Thread):
    """pass
    """

    def __init__(self, ch_name, p):
        super(MonitorPubSub, self).__init__()
        self.ch_name = ch_name
        self.daemon = True
        self.p = p

    def run(self):
        count = 0
        while True:
            count += 1
            if count % 10 == 0:
                log.debug(count)
            msg = self.p.get_message(ignore_subscribe_messages=True)
            if msg:
                log.info("get message from channel %s: %s", self.ch_name, msg)
                BeakerProvision().clear_netboot(self.ch_name)
                # self.p.unsubscribe(self.ch_name)
                # self.p.close()
                # log.info("wait here for 5 min")
                # time.sleep(300)
                redis_conn.publish(self.ch_name, 'success')
                break
            elif count > 260:  # wait for 20 minutes
                log.error("provision job is time-out")
                redis_conn.publish(self.ch_name, 'fail')
                break
            time.sleep(5)


class BeakerProvision(object):
    """pass
    """
    CMDs = dict(

        # this cmd will provision the given host with rhevh ngn build
        provision='''bkr system-provision \
        --kernel-options \
        "inst.stage2=http://download.eng.pek2.redhat.com/released/RHEL-7/7.2/Server/x86_64/os \
        inst.ks=http://{srv_ip}:{srv_port}/static/ngn-auto-installation-kickstarts/{ks_file} \
        ks=" \
        --distro-tree {distro_tree_id} {bkr_name}''',

        # this cmd will make sure the given host boot from local disk
        clear_netboot='''bkr system-power \
        --action none \
        --clear-netboot {bkr_name}''',
        power_on='''bkr system-power \
        --action on {bkr_name}
        ''',
        power_off='''bkr system-power \
        --action off {bkr_name}
        ''',
        reserve='''bkr system-reserve \
        {bkr_name}
        ''',
        release='''bkr system-release \
        {bkr_name}
        ''',
        status='''bkr system-status \
        {bkr_name} --format json
        ''')

    def __init__(self, srv_ip='', srv_port='', ks_file=''):
        self.srv_ip = srv_ip
        self.srv_port = srv_port
        self.ks_file = ks_file

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

    def provision(self, bkr_name, distro_tree_id='71758'):
        """pass"""
        return self._exec_cmd('provision',
                              bkr_name,
                              dict(bkr_name=bkr_name,
                                   distro_tree_id=distro_tree_id,
                                   ks_file=self.ks_file,
                                   srv_ip=self.srv_ip,
                                   srv_port=self.srv_port))

    def clear_netboot(self, bkr_name):
        """pass"""
        return self._exec_cmd('clear_netboot',
                              bkr_name,
                              dict(bkr_name=bkr_name))

    def reserve(self, bkr_name):
        """pass"""
        return self._exec_cmd('reserve', bkr_name, dict(bkr_name=bkr_name))

    def release(self, bkr_name):
        """pass"""
        return self._exec_cmd('release', bkr_name, dict(bkr_name=bkr_name))

    def status(self, bkr_name):
        """pass"""
        ret = self._exec_cmd('status',
                             bkr_name,
                             dict(bkr_name=bkr_name),
                             output=True)
        data = json.loads(ret)
        if data['current_reservation']:
            if data['current_reservation']['user_name'] == 'yaniwang':
                return True
            else:
                raise ReserveUserWrongException(
                    dict(bkr_name=bkr_name,
                         user_name_r='yaniwang',
                         # pylint: disable=C0301
                         user_name_w=data['current_reservation']['user_name']))
        else:
            return False
