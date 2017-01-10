import xmlrpclib
import logging
import requests
import json
import copy
import subprocess
from constants import CB_API, CB_CREDENTIAL, CB_PROFILE, NOPXE_URL, \
                      CB_SYSTEM, CURRENT_IP_PORT

log = logging.getLogger("bender")


class Host(object):
    """Abstract class prsent testable Host
    """

    def power_on(self):
        raise NotImplementedError

    def power_off(self):
        raise NotImplementedError

    def reboot(self):
        raise NotImplementedError

    def provision(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError

    def pxe_netboot(self, name, enabled):
        raise NotImplementedError


class CobblerHost(Host):
    """
    """

    def __init__(self,
                 cb_api_url=None,
                 cb_credential=None,
                 cb_profile=None,
                 cb_system=None):
        self.cb_api_url = cb_api_url or CB_API
        self.profile = cb_profile or CB_PROFILE
        self.system = cb_system or CB_SYSTEM
        self.server = xmlrpclib.Server(self.cb_api_url)
        self.cb_credential = cb_credential or CB_CREDENTIAL
        self.token = self.server.login(*(self.cb_credential))
        self.args = {
            "profile": self.profile,
            "comment": "updated-by-zoidberg",
            "status": "testing",
            "kernel_options": "",
            "kernel_options_post": ""
        }

        self.beaker = CobblerHost(system=self.system)

    def _get_system_handle(self):
        return self.server.get_system_handle(self.system, self.token)

    def modify_system(self, system_handle, args):
        for k, v in args.items():
            log.debug("Modifying system: %s=%s" % (k, v))
            self.server.modify_system(system_handle, k, v, self.token)
        self.server.save_system(system_handle, self.token)

    def power_on(self):
        self.beaker.power_on()

    def power_off(self):
        self.beaker.power_off()

    def reboot(self):
        self.beaker.reboot()

    def provision(self, args):
        self.reboot()

        tpl = copy.deepcopy(self.args)
        tpl.update(args)
        sh = self._get_system_handle()
        self.modify_system(sh, tpl)

        self.pxe_netboot(True)

    def status(self):
        pass

    def pxe_netboot(self, enabled):
        args = {"netboot-enabled": 1 if enabled else 0}
        tpl = copy.deepcopy(self.args)
        tpl.update(args)
        sh = self._get_system_handle()
        self.modify_system(sh, tpl)


class BeakerHost(Host):
    """pass
    """
    CMDs = dict(
        # this cmd will provision the given host with rhevh ngn build
        provision='''bkr system-provision \
        --kernel-options \
        "inst.stage2=http://10.66.10.22:8090/rhevh/ngn-dvd-iso/RHVH-7.2-20160718.1/stage2 \
        inst.ks=http://{srv_ip}:{srv_port}/static/auto/{ks_file} \
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
        power_reboot='''bkr system-power \
        --action reboot {bkr_name}
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

    def __init__(self, srv_ip='', srv_port='', ks_file='', system=''):
        self.srv_ip = srv_ip or CURRENT_IP_PORT[0]
        self.srv_port = srv_port or CURRENT_IP_PORT[1]
        self.ks_file = ks_file
        self.system = system

    def _exec_cmd(self, cmd, bkr_name, args, output=False):
        _cmd = self.CMDs[cmd].format(**args)
        if not output:
            ret = subprocess.call(_cmd, shell=True)
            return ret
        else:
            ret = subprocess.check_output(_cmd, shell=True)
            return ret

    def power_on(self):
        """pass"""
        return self._exec_cmd(
            'power_on', self.system, dict(bkr_name=self.system))

    def power_off(self):
        """pass"""
        return self._exec_cmd(
            'power_off', self.system, dict(bkr_name=self.system))

    def reboot(self):
        """pass"""
        return self._exec_cmd(
            'power_reboot', self.system, dict(bkr_name=self.system))

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

    def pxe_netboot(self, enabled):
        return requests.get(NOPXE_URL.format(self.system))

    def clear_netboot(self, bkr_name):
        """pass"""
        # TODO fix this

        return requests.get(NOPXE_URL.format(bkr_name))
        # self._exec_cmd('clear_netboot',
        #                       bkr_name,
        #                       dict(bkr_name=bkr_name))

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
                raise RuntimeError(
                    dict(
                        bkr_name=bkr_name,
                        user_name_r='yaniwang',
                        # pylint: disable=C0301
                        user_name_w=data['current_reservation']['user_name']))
        else:
            return False


if __name__ == '__main__':
    cb = BeakerHost(system='dell-per510-01.lab.eng.pek2.redhat.com')
    cb.reboot()
