import attr


@attr.s
class ServicesCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_services = attr.ib()

    def sshd_check(self):
        return self.remotecmd.check_strs_in_cmd_output(
            'systemctl status sshd', ['running'], timeout=300)
