import attr


@attr.s
class SecurityCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_security = attr.ib()

    def security_policy_check(self):
        return self.remotecmd.check_strs_in_cmd_output(
            'ls /root', ['openscap_data'], timeout=300)


    def _enable_fips_mode(self):
        cmd = "fips-mode-setup --enable"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to enable fips mode.")
            return False
        if "FIPS mode will be enabled" in ret[1] and "Please reboot the system for the setting to take effect" in ret[1]:
            log.info("Enable fips mode successfully.")
            return True
        log.error("Failed to enable fips mode. The result of '%s' is '%s'", cmd, ret[1])
        return False

    def _enter_system(self, flag="manual"):
        log.info("Reboot and log into system...")

        if flag == "manual":
            self.remotecmd.disconnect()
            cmd = "systemctl reboot"
            self.remotecmd.run_cmd(cmd, timeout=10)

        self.remotecmd.disconnect()
        count = 0
        while (count < CONST.ENTER_SYSTEM_MAXCOUNT):
            time.sleep(CONST.ENTER_SYSTEM_INTERVAL)
            ret = self.remotecmd.run_cmd(
                "imgbase w", timeout=CONST.ENTER_SYSTEM_TIMEOUT)
            if not ret[0]:
                count = count + 1
            else:
                break

        log.info("Reboot and log into system finished.")
        return ret

    def _check_fips_mode(self):
        cmd = "fips-mode-setup --check"
        ret = self._remotecmd.run_cmd(cmd, timeout=CONST.FABRIC_TIMEOUT)
        if not ret[0]:
            log.error("Failed to get fips mode.")
            return False
        if ret[1] == "FIPS mode is enabled.":
            log.info("Fips mode is enabled.")
            return True
        log.error("Fips mode is not enabled. The result of '%s' is '%s'", cmd, ret[1])
        return False
