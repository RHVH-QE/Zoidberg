import os
import json


class ExpectedData(object):
    """
    """

    def __init__(self, expected_data_file):
        with open(expected_data_file, 'rb') as fp:
            self._expected_data = json.load(fp)

    @property
    def expected_partition(self):
        """
        'bootdevice':
        '/boot': {
            'lvm':
            'device_alias':
            'device_wwid':
            'fstype':
            'size':
        },
        'volgroup': {
            'lvm':
            'name':
        },
        'pool': {
            'lvm':
            'name':
            'size':
            'grow':
        },
        '/': {
            'lvm':
            'name':
            'fstype':
            'size':
        },
        '/var': {
            'lvm':
            'name':
            'fstype':
            'size':
        },
        '/var/log': {
            'lvm':
            'name':
            'fstype':
            'size':
        },
        '/var/log/audit': {
            'lvm':
            'name':
            'fstype':
            'size':
        },
        '/tmp': {
            'lvm':
            'name':
            'fstype':
            'size':
        }
        '/home': {
            'lvm':
            'name':
            'fstype':
            'size':
        },
        'swap': {
            'lvm':
            'name':
            'size':
        },
        """
        return self._expected_data.get('partition')

    @property
    def expected_network(self):
        """
        'hostname':
        'nic': {
            'DEVICE':
            'BOOTPROTO':
            'status':
            'ONBOOT':
        },        
        'static': {
            'DEVICE':
            'BOOTPROTO':
            'IPADDR':
            'NETMASK':
            'GATEWAY':
            'ONBOOT':
        },
        'dhcp': {
            'DEVICE':
            'BOOTPROTO':
            'ONBOOT':
        },        
        'bond': {
            'DEVICE':
            'TYPE':
            'BONDING_OPTS':
            'ONBOOT':
            'slaves':
        },
        'vlan': {
            'DEVICE':
            'TYPE':
            'BOOTPROTO':
            'VLAN_ID':
            'ONBOOT':
        }
        """
        return self._expected_data.get('network')

    @property
    def expected_lang(self):
        return self._expected_data.get('lang')

    @property
    def expected_timezone(self):
        """
        'timezone':
        'ntpservers':
        """
        return self._expected_data.get('timezone')

    @property
    def expected_keyboard(self):
        """
        'vckeymap': 
        'xlayouts':
        """
        return self._expected_data.get('keyboard')

    @property
    def expected_kdump(self):
        """
        'reserve-mb':
        """
        return self._expected_data.get('kdump')

    @property
    def expected_user(self):
        """
        'name':
        """
        return self._expected_data.get('user')

    @property
    def expected_selinux(self):
        return self._expected_data.get('selinux')

    @property
    def expected_grubby(self):
        return self._expected_data.get('grubby')

    @property
    def expected_security(self):
        return None

    @property
    def expected_firewall(self):
        return None

    @property
    def expected_services(self):
        return None

    @property
    def expected_general(self):
        return None
