import attr


@attr.s
class UserCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_user = attr.ib()

    def user_check(self):
        username = self.expected_user.get('name')
        ck01 = self.remotecmd.check_strs_in_file(
            '/etc/passwd', [username], timeout=300)
        ck02 = self.remotecmd.check_strs_in_file(
            '/etc/shadow', [username], timeout=300)
        ck03 = self.remotecmd.check_strs_in_cmd_output(
            'ls /home', [username], timeout=300)
        return ck01 and ck02 and ck03
