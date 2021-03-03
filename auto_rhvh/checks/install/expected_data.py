import os
import json


class ExpectedData(object):
    """
    """

    def __init__(self, expected_data_file):
        if os.path.exists(expected_data_file):
            with open(expected_data_file, 'rb') as fp:
                self._expected_data = json.load(fp)

    @property
    def expected_partition(self):
        """
        'bootdevice':
        'standard partition name': {
            'lvm': False
            'device_alias':
            'device_wwid':
            'fstype':
            'size':
            'grow':
            'maxsize'            
        },
        'logic volume name':{
            'lvm': True
            'name':
            'fstype':
            'size':
            'grow':
            'maxsize':
            'recommended': True/False
            'discard': True/False
        }
        """
        return self._expected_data.get('partition')

    def set_expected_vgname(self, vgname):
        self._expected_data['partition']['volgroup']['name'] = vgname

    @property
    def expected_network(self):
        """
        'hostname':
        'nic': {
            'DEVICE':
            'BOOTPROTO':
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

    @property
    def expected_rhsm(self):
        return None

    @property
    def expected_securityengine(self):
        return None
