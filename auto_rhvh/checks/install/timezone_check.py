import logging
import attr

log = logging.getLogger('bender')


@attr.s
class TimezoneCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_timezone = attr.ib()

    def ntp_check(self):
        ntp = self.expected_timezone.get('ntpservers')
        return self.remotecmd.check_strs_in_file('/etc/chrony.conf', [ntp], timeout=300)

    def timezone_check(self):
        timezone = self.expected_timezone.get('timezone')
        cmd = "timedatectl | grep 'Time zone'"
        return self.remotecmd.check_strs_in_cmd_output(cdm, [timezone], timeout=300)

    def utc_check(self):
        cmd = 'timedatectl'
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if not ret[0]:
            return False

        timedate = ret[1].split('\r\n')
        for line in timedate:
            if 'Universal time' in line:
                univer_time = line.split('time:')[-1].split('UTC')[0].strip()
            elif 'RTC time' in line:
                rtc_time = line.split('time:')[-1].strip()
            elif 'RTC in local TZ' in line:
                rtc_local_flag = line.split(':')[-1].strip()

        if univer_time != rtc_time:
            log.error("RTC time: '%s',  not equal to Universal time: '%s'",
                      rtc_time, univer_time)
            return False
        if rtc_local_flag != 'no':
            log.error("RTC in local TZ flag is %s, not 'no'", rtc_local_flag)
            return False

        return True
