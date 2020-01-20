import attr


@attr.s
class ServicesCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_services = attr.ib()

    def sshd_check(self):
        return self.remotecmd.run_cmd(
            'systemctl status sshd | egrep "Active:.*running"', timeout=300)
