import common as COMM
import install_cases as INSTALL
import upgrade_cases as UPGRADE
import vdsm_cases as VDSM
from operator import itemgetter


class CasesMap(object):
    """
    """

    def __init__(self, test_level):
        self._test_level = test_level
        self._testcase_map = self._get_testcase_map(test_level)

    @property
    def test_level(self):
        return self._test_level

    @property
    def testcase_map(self):
        return self._testcase_map

    def _get_testcase_map(self, test_level):
        testcase_map = {}

        if test_level & COMM.DEBUG_TIER:
            testcase_map.update(COMM.DEBUG_TIER_TESTCASE_MAP)
        if test_level & COMM.INSTALL_TIER1:
            testcase_map.update(INSTALL.INSTALL_TIER1_TESTCASE_MAP)
        if test_level & COMM.INSTALL_TIER2:
            testcase_map.update(INSTALL.INSTALL_TIER2_TESTCASE_MAP)
        if test_level & COMM.UPGRADE_TIER1:
            testcase_map.update(UPGRADE.UPGRADE_TIER1_TESTCASE_MAP)
        if test_level & COMM.UPGRADE_TIER2:
            testcase_map.update(UPGRADE.UPGRADE_TIER2_TESTCASE_MAP)
        if test_level & COMM.VDSM_TIER:
            testcase_map.update(VDSM.VDSM_TIER_TESTCASE_MAP)

        if not testcase_map:
            raise ValueError('Invaild TEST_LEVEL')

        return testcase_map

    def gether_other_params(self):
        def gether(param_name):
            param = {param_name: {}}
            for m in ["INSTALL", "UPGRADE", "VDSM"]:
                temp = getattr(globals()[m], param_name, None)
                if temp:
                    param[param_name].update(temp)
            return param

        other_params = {}
        for m in ["KS_PRESSURE_MAP", "KS_KERPARAMS_MAP"]:
            param = gether(m)
            other_params.update(param)

        return other_params

    def get_machine_ksl_map(self):
        machine_ksl_map = {}
        other_params = self.gether_other_params()

        for value in self.testcase_map.itervalues():
            ks = value[0]
            machine = value[1]
            flag = False
            if machine in machine_ksl_map:
                if ks not in machine_ksl_map.get(machine):
                    flag = True
            else:
                machine_ksl_map[machine] = []
                flag = True

            if flag:
                kst = (ks,)
                ks_kerparam_map = other_params["KS_KERPARAMS_MAP"]
                ks_pressure_map = other_params["KS_PRESSURE_MAP"]
                if ks in ks_kerparam_map:
                    kst = (ks, ks_kerparam_map.get(ks))
                if ks in ks_pressure_map:
                    ks_repeat_ls = [kst] * int(ks_pressure_map.get(ks))
                    machine_ksl_map[machine].extend(ks_repeat_ls)
                else:
                    machine_ksl_map[machine].append(kst)

        for k in machine_ksl_map:
            machine_ksl_map[k] = sorted(machine_ksl_map[k], key=itemgetter(0))

        return machine_ksl_map

    def get_ks_machine_map(self):
        ks_mashine_map = {}
        for value in self.testcase_map.itervalues():
            ks = value[0]
            machine = value[1]
            if ks in ks_mashine_map:
                if machine != ks_mashine_map.get(ks):
                    raise ValueError(
                        'One kickstart file %s cannot be run on two machines.' % ks)
            else:
                ks_mashine_map[ks] = machine

        return ks_mashine_map

    def get_checkpoint_cases_map(self, ks, mc):
        checkpoint_cases_map = {}
        for key, value in self.testcase_map.items():
            if set((ks, mc)) < set(value):
                checkpoint = value[2]
                if checkpoint in checkpoint_cases_map:
                    checkpoint_cases_map[checkpoint].append(key)
                else:
                    checkpoint_cases_map[checkpoint] = []
                    checkpoint_cases_map[checkpoint].append(key)

        return checkpoint_cases_map


if __name__ == '__main__':
    test_level = COMM.DEBUG_TIER
    casesmap = CasesMap(test_level)
    print casesmap.testcase_map
    print casesmap.get_checkpoint_cases_map('ati_fc_01.ks',
                                            'dell-per510-01.lab.eng.pek2.redhat.com')
