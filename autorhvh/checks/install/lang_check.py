class LangCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_lang = attr.ib()

    def lang_check(self):
        lang = self.expected_lang
        return self.remotecmd.check_strs_in_cmd_output(
            'localectl status', [lang], timeout=300)
