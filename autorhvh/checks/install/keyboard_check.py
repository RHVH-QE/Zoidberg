import attr


@attr.s
class KeyboardCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_keyboard = attr.ib()

    def keyboard_check(self):
        vckey = self.expected_keyboard.get('vckeymap')
        xlayouts = self.expected_keyboard.get('xlayouts')
        return self.remotecmd.check_strs_in_cmd_output(
            'localectl status',
            ['VC Keymap: {}'.format(vckey), 'X11 Layout: {}'.format(xlayouts)],
            timeout=300)
