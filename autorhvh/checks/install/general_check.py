class GeneralCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_general = attr.ib()

    def node_check(self):
        patterns = [r'^Status: OK']
        return self.remotecmd.match_strs_in_cmd_output(
            'nodectl check', patterns, timeout=300)

    def fips_check(self):
        return self.remotecmd.check_strs_in_file(
            '/proc/sys/crypto/fips_enabled', ['1'], timeout=300)

    def iqn_check(self):
        return self.remotecmd.check_strs_in_file(
            '/etc/iscsi/initiatorname.iscsi', ['iqn'], timeout=300)

    def layout_init_check(self):
        resstr = (
            "imgbased.imgbase.ExistingImgbaseWithTags: "
            "Looks like the system already has imgbase working properly.\r\n"
            "However, imgbase was called with --init. If this was intentional, "
            "please untag the existing volumes and try again.")
        ret = self.remotecmd.run_cmd('imgbase layout --init', timeout=300)
        if not ret[0]:
            if resstr in ret[1]:
                return True
        return False
