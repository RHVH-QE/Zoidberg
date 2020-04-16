import attr


@attr.s
class RhsmCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_rhsm = attr.ib()

    def subscription_check(self):
        ck01 = self.remotecmd.run_cmd('subscription-manager status | grep "Overall Status: Current"', timeout=300)
        ck02 = self.remotecmd.run_cmd('insights-client --status | grep "System is registered"', timeout=300)
        # need to unregister because entitlements are limited
        self.remotecmd.run_cmd('subscription unregister', timeout=300)

        return ck01[0] and ck02[0]
