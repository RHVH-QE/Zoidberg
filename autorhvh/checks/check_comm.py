import logging

log = logging.getLogger('bender')


class CheckComm(object):
    """"""

    def __init__(self):
        self._casesmap = None
        self._remotecmd = None
        self._beaker_name = None
        self._ksfile = None
        self._source_build = None
        self._target_build = None

    @property
    def casesmap(self):
        return self._casesmap

    @casesmap.setter
    def casesmap(self, val):
        self._casesmap = val

    @property
    def remotecmd(self):
        return self._remotecmd

    @remotecmd.setter
    def remotecmd(self, val):
        self._remotecmd = val

    @property
    def beaker_name(self):
        return self._beaker_name

    @beaker_name.setter
    def beaker_name(self, val):
        self._beaker_name = val

    @property
    def ksfile(self):
        return self._ksfile

    @ksfile.setter
    def ksfile(self, val):
        self._ksfile = val

    @property
    def source_build(self):
        return self._source_build

    @source_build.setter
    def source_build(self, val):
        self._source_build = val

    @property
    def target_build(self):
        return self._target_build

    @target_build.setter
    def target_build(self, val):
        self._target_build = val

    def call_func_by_name(self, name=''):
        func = getattr(self, name.lower(), None)
        if func:
            return func()
        else:
            raise NameError(
                'The checkpoint function {} is not defined'.format(name))

    def run_checkpoint(self, checkpoint, cases, cks):
        try:
            log.info("Start to run checkpoint:%s for cases:%s",
                     checkpoint, cases)
            ck = self.call_func_by_name(checkpoint)
            if ck:
                newck = 'passed'
            else:
                newck = 'failed'
            for case in cases:
                cks[case] = newck
        except Exception as e:
            log.error(e)
        finally:
            log.info("Run checkpoint:%s for cases:%s finished.",
                     checkpoint, cases)

    def run_cases(self):
        cks = {}
        try:
            # get checkpoint cases map
            checkpoint_cases_map = self.casesmap.get_checkpoint_cases_map(self.ksfile,
                                                                          self.beaker_name)

            # run check
            log.info("Start to run check points, please wait...")

            roll_back_cases = None
            for checkpoint, cases in checkpoint_cases_map.items():
                if checkpoint == "roll_back_check":
                    roll_back_cases = cases
                    continue
                self.run_checkpoint(checkpoint, cases, cks)
            if roll_back_cases:
                self.run_checkpoint("roll_back_check", roll_back_cases, cks)
        except Exception as e:
            log.error(e)

        return cks

    def go_check(self):
        pass


if __name__ == '__main__':
    pass
