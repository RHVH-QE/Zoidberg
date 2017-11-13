class KdumpCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_kdump = attr.ib()

    def kdump_check(self):
        reserve_mb = self.expected_kdump.get('reserve-mb')
        return self.remotecmd.check_strs_in_file(
            '/etc/grub2.cfg', ['crashkernel={}M'.format(reserve_mb)],
            timeout=300)
