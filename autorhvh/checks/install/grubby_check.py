class GrubbyCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_grubby = attr.ib()

    def grubby_check(self):
        checkstr = self.expected_grubby

        return self.remotecmd.check_strs_in_cmd_output(
            'grubby --info=0', [checkstr], timeout=300)
