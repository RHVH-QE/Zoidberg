import attr


@attr.s
class FirewallCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_firewall = attr.ib()

    def firewall_enable_check(self):
        pattern = r'^running'
        cmd = 'firewall-cmd --state'
        return self.remotecmd.match_strs_in_cmd_output(cmd, [pattern], timeout=300)

    def firewall_disable_check(self):
        cmd = 'firewall-cmd --state'
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if not ret[0] and "not running" in ret[1]:
            return True
        else:
            return False
