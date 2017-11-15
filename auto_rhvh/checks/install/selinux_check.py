import attr


@attr.s
class SelinuxCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_selinux = attr.ib()

    def selinux_check(self):
        selinux_status = self.expected_selinux
        strs = 'SELINUX={}'.format(selinux_status)
        return self.remotecmd.check_strs_in_file(
            '/etc/selinux/config', [strs], timeout=300)
