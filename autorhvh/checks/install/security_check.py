import attr


@attr.s
class SecurityCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_security = attr.ib()

    def security_policy_check(self):
        return self.remotecmd.check_strs_in_cmd_output(
            'ls /root', ['openscap_data'], timeout=300)
