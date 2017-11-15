import attr


@attr.s
class TimezoneCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_timezone = attr.ib()

    def ntp_check(self):
        ntp = self.expected_timezone.get('ntpservers')
        return self.remotecmd.check_strs_in_file('/etc/chrony.conf', [ntp], timeout=300)
