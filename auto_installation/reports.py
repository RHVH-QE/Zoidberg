import os
import time
import argparse
import datetime
try:
    from pylarion.test_run import TestRun
except ImportError:
    print("pylarion must be installed")
from constants import TR_ID, TR_PROJECT_ID, TR_TPL, \
    KS_PRESSURE_MAP
import re
import json
from utils import get_testcase_map

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def make_test_run():
    return TestRun(
        project_id=TR_PROJECT_ID,
        test_run_id='4_0_Node_0622_AutoInstallWithKickstart_Must')


class ResultsToPolarion(object):
    """
    /home/dracher/Zoidberg/logs/2017-03-08/redhat-virtualization-host-4.1-20170208.0
    """

    def __init__(self, path, action):
        self.action = action
        self.path = path.rstrip('/')
        self.jfilename = "final_results.json"

    @staticmethod
    def get_current_date():
        return time.strftime("%m%d%H%M", time.localtime())

    def create_testrun(self, build, level='Must'):
        ret = TestRun.create(TR_PROJECT_ID,
                             TR_ID.format(
                                 build.replace(".", "_"),
                                 self.get_current_date()),
                             TR_TPL.format(level))
        return ret

    def export_to_polarion(
            self,
            tr,
            test_case_id,
            test_result,  # passed or failed
            test_comment="pass without error",
            executed_by='yaniwang',  # krb_id
            executed=datetime.datetime.now(),
            duration=66.6):

        if test_result == 'passed':
            tr.add_test_record_by_fields(
                test_case_id=test_case_id,
                test_result=test_result,
                test_comment=test_comment,
                executed_by=executed_by,
                executed=executed,
                duration=duration)
        elif test_result == 'failed':
            tr.add_test_record_by_fields(
                test_case_id=test_case_id,
                test_result=test_result,
                test_comment="failed, detail in attatched log",
                executed_by=executed_by,
                executed=executed,
                duration=duration)
        else:
            # TODO deal with blocked
            pass

    def _parse_checkpoints(self, res):
        ks = res.split('/')[-2]
        if ks in KS_PRESSURE_MAP:
            num = int(KS_PRESSURE_MAP[ks])
        else:
            num = 1

        p1 = re.compile(r"{'RHEVM-\d")
        p2 = re.compile(r'InitiatorName=iqn')
        rets = []
        iqns = []
        if os.path.exists(res):
            for line in open(res):
                if p1.search(line):
                    rets.append(eval(line.split("::")[-1]))
                if p2.search(line):
                    iqns.append(line.split(":")[-1].rstrip("')\n"))

        retNum = len(rets)
        if retNum != num:
            newret = {}
        else:
            newret = rets[0]
            if num > 1:
                for ret in rets[1:]:
                    for k in newret:
                        newret[k] = newret[k] and ret[k]

                if len(iqns) == num and len(set(iqns)) != num:
                    testcase_map = get_testcase_map()
                    for k, v in testcase_map.items():
                        if 'iqn_check' in v and k in newret:
                            newret[k] = False
                            break
        return newret

    def _gen_results_jfile(self):
        build = self.path.split('/')[-1]
        root_path = self.path

        final_results = {build: {}}
        actual_run_cases = []
        pass_num = 0
        failed_num = 0
        for a, b, c in os.walk(root_path):
            for ks in b:
                ret = self._parse_checkpoints(os.path.join(a, ks, 'checkpoints'))
                final_results[build][ks] = ret
                actual_run_cases.extend(list(ret.keys()))
                values = list(ret.values())
                pass_num = pass_num + values.count('passed')
                failed_num = failed_num + values.count('failed')
            break

        need_run_cases = list(get_testcase_map().keys())
        final_results['sum'] = {}
        final_results['sum']['build'] = build
        final_results['sum']['total'] = len(need_run_cases)
        final_results['sum']['passed'] = pass_num
        final_results['sum']['failed'] = failed_num
        final_results['sum']['error'] = len(need_run_cases) - len(
            actual_run_cases)
        final_results['sum']['errorlist'] = list(
            set(need_run_cases) - set(actual_run_cases))

        final_results_jfile = os.path.join(root_path,
                                           self.jfilename)
        try:
            with open(final_results_jfile, 'w') as json_file:
                json_file.write(
                    json.dumps(
                        final_results, sort_keys=True, indent=4))

            return final_results_jfile
        except Exception as e:
            print e
            return None

    def _report_to_polarion_by_jfile(self, jfile):
        if jfile.split('/')[-1] != self.jfilename:
            print "Input wrong results json file."
            return

        print "Begin to transport results to polarion..."

        final_results = json.load(open(jfile))
        build = final_results.get('sum').get('build')
        ks_list = []
        for k in final_results.get(build):
            ks_list.append(k.encode())
        ks_list.sort()

        tr = self.create_testrun(build)
        tr.group_id = build
        tr.description = 'automatic installation use {} with {}'.format(
            build, ks_list)
        tr.status = 'finished'
        tr.update()

        print tr.uri
        print tr.test_run_id

        rets = final_results.get(build).values()
        for ret in rets:
            for k, v in ret.items():
                self.export_to_polarion(tr, k, v)
                print "be nice with server, sleep 1 sec"
                time.sleep(1)

        print "Transport results to polarion finished."

    def run(self):
        if self.action in ['-l', '-b']:
            final_results_jfile = self._gen_results_jfile()
            if not final_results_jfile:
                print "Generate final results json file failed."
                return
            else:
                print "Generated {}".format(final_results_jfile)
        else:
            final_results_jfile = self.path

        if self.action in ['-p', '-b']:
            self._report_to_polarion_by_jfile(final_results_jfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=(
        'Script used to generate test-run '
        'summary or upload results to polarion'))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-l',
        action='store_true',
        help='generate final summary in json format')
    group.add_argument(
        '-p',
        action='store_true',
        help='upload test results to polarion only using json file')
    group.add_argument(
        '-b',
        action='store_true',
        help='generate final summary in json format and upload results to polarion')
    parser.add_argument('results_path', help="path to results log directory")
    args = parser.parse_args()

    res_path = args.results_path
    if args.p:
        action = '-p'
    if args.l:
        action = '-l'
    if args.b:
        action = '-b'

    r = ResultsToPolarion(res_path, action)
    r.run()
