import attr


@attr.s
class KdumpCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_kdump = attr.ib()

    def kdump_enable_check(self):
        reserve_mb = self.expected_kdump.get('reserve-mb')
        return self.remotecmd.check_strs_in_file(
            '/etc/grub2.cfg', ['crashkernel={}M'.format(reserve_mb)],
            timeout=300)

    def kdump_disable_check(self):
        cmd = "grep 'crashkernel' /etc/grub2.cfg"
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if ret[0]:
            return False

        return True
