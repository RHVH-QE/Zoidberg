class FirewallCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_firewall = attr.ib()

    def firewall_check(self):
        return self.remotecmd.check_strs_in_cmd_output(
            'firewall-cmd --state', ['running'], timeout=300)
