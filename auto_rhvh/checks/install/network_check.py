import attr


@attr.s
class NetworkCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_network = attr.ib()

    def _check_device_ifcfg_value(self, device_data_map):
        patterns = []
        for key, value in device_data_map.items():
            if key.isupper():
                patterns.append(r'^{}="?{}"?$'.format(key, value))

        ifcfg_file = "/etc/sysconfig/network-scripts/ifcfg-{}".format(
            device_data_map.get('DEVICE'))
        cmd = 'cat {}'.format(ifcfg_file)

        return self.remotecmd.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_device_connected(self, nics, expected_result='yes'):
        patterns = []
        for nic in nics:
            if expected_result == 'yes':
                patterns.append(
                    r'^{}:(connected|connecting)'.format(nic))
            else:
                patterns.append(r'^{}:disconnected$'.format(nic))

        cmd = 'nmcli -t -f DEVICE,STATE dev'

        return self.remotecmd.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_device_ipv4_address(self, nic, ipv4):
        patterns = [r'^inet\s+{}'.format(ipv4)]
        cmd = 'ip -f inet addr show {}'.format(nic)

        return self.remotecmd.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_device_ipv6_address(self, nic, ipv6):
        patterns = [r'^inet6\s+{}'.format(ipv6)]
        cmd = 'ip -f inet6 addr show {}'.format(nic)

        return self.remotecmd.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def _check_bond_has_slave(self, bond, slaves, expected_result='yes'):
        patterns = []
        for slave in slaves:
            if expected_result == 'yes':
                patterns.append(r'^Slave.*{}$'.format(slave))
            else:
                patterns.append(
                    r'^((?!Slave.*{}).)*$'.format(slave))

        cmd = 'cat /proc/net/bonding/{}'.format(bond)

        return self.remotecmd.match_strs_in_cmd_output(cmd, patterns, timeout=300)

    def static_network_check(self):
        device_data_map = self.expected_network.get('static')
        nic_device = device_data_map.get('DEVICE')
        nic_ipv4 = device_data_map.get('IPADDR')
        nic_ipv6 = device_data_map.get('IPV6ADDR')

        ck01 = self._check_device_ifcfg_value(device_data_map)

        ck02 = True
        if nic_ipv4:
            ck02 = self._check_device_ipv4_address(nic_device, nic_ipv4)

        ck03 = True
        if nic_ipv6:
            ck03 = self._check_device_ipv6_address(nic_device, nic_ipv6)

        ck04 = self._check_device_connected([nic_device])

        return ck01 and ck02 and ck03 and ck04

    def bond_check(self):
        device_data_map = self.expected_network.get('bond')
        bond_device = device_data_map.get('DEVICE')
        bond_slaves = device_data_map.get('slaves')

        ck01 = self._check_device_ifcfg_value(device_data_map)
        ck02 = self._check_bond_has_slave(bond_device, bond_slaves)
        ck03 = self._check_device_connected([bond_device] + bond_slaves)

        return ck01 and ck02 and ck03

    def vlan_check(self):
        device_data_map = self.expected_network.get('vlan')
        vlan_device = device_data_map.get('DEVICE')

        ck01 = self._check_device_ifcfg_value(device_data_map)
        ck02 = self._check_device_connected([vlan_device])

        return ck01 and ck02

    def bond_vlan_check(self):
        ck01 = self.bond_check()
        ck02 = self.vlan_check()
        return ck01 and ck02

    def nic_stat_dur_install_check(self):
        device_data_map = self.expected_network.get('nic')
        nic_device = device_data_map.get('DEVICE')

        cmd = "test -e /boot/nicup"
        ck01 = self.remotecmd.run_cmd(cmd)
        ck02 = self._check_device_ifcfg_value(device_data_map)
        ck03 = self._check_device_connected(
            [nic_device], expected_result='false')

        return ck01 and ck02 and ck03

    def dhcp_network_check(self):
        device_data_map = self.expected_network.get('dhcp')
        nic_device = device_data_map.get('DEVICE')

        ck01 = self._check_device_ifcfg_value(device_data_map)
        ck02 = self._check_device_connected([nic_device])

        return ck01 and ck02

    def hostname_check(self):
        hostname = self.expected_network.get('hostname')
        return self.remotecmd.check_strs_in_cmd_output(
            'hostname', [hostname], timeout=300)
