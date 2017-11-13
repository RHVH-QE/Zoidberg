import os
import time
import argparse
import datetime
try:
    from pylarion.test_run import TestRun
except ImportError:
    print("pylarion must be installed")
from constants import TR_ID, TR_PROJECT_ID, TR_TPL, LOG_URL
import re
import json
from collections import OrderedDict

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

    def __init__(self, path, action, casesmap, test_flag="install", target_build=None):
        self.action = action
        self.path = path.rstrip('/')
        self.source_build = self.path.split('/')[-1]
        self.target_build = target_build
        self.test_flag = test_flag
        self.jfilename = "final_results.json"
        self.casesmap = casesmap

    @staticmethod
    def get_current_date():
        return time.strftime("%m%d%H%M", time.localtime())

    def create_testrun(self, title, level='Must'):
        ret = TestRun.create(TR_PROJECT_ID,
                             TR_ID.format(
                                 title.replace(".", "_"),
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
        ks_pressure_map = self.casesmap.get_other_params.get("KS_PRESSURE_MAP")
        if ks in ks_pressure_map:
            num = int(ks_pressure_map[ks])
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
                    for k, v in self.casesmap.testcase_map.items():
                        if 'iqn_check' in v and k in newret:
                            newret[k] = False
                            break
        return newret

    def _gen_title(self):
        src_ver = self.source_build.split('-')[-2].replace('.', '_')
        src_build_name = self.source_build.replace(
            'redhat-virtualization-host', 'rhvh')

        title = None
        if self.test_flag == "install":
            title = src_ver + "_Node_Install_AutoTest_" + src_build_name
        elif self.test_flag == "upgrade":
            if not self.target_build:
                print "The test_flag is upgrade, but there is no target build info."
            else:
                tar_ver = self.target_build.split('-')[-2].replace('.', '_')
                tar_build_name = self.target_build.replace(
                    'redhat-virtualization-host', 'rhvh')
                title = tar_ver + "_Node_Upgrade_AutoTest_from_" + \
                    src_build_name + "_to_" + tar_build_name
        elif self.test_flag == "vdsm":
            title = src_ver + "_Node_Vdsm_AutoTest_" + src_build_name

        return title

    def _gen_log_url(self):
        log_url = LOG_URL + self.path.split('logs')[-1]
        return log_url

    def _gen_results_jfile(self):
        root_path = self.path

        final_results = OrderedDict()
        final_results[self.source_build] = OrderedDict()
        actual_run_cases = []
        pass_num = 0
        failed_num = 0
        for a, b, c in os.walk(root_path):
            for ks in sorted(b):
                ret = self._parse_checkpoints(
                    os.path.join(a, ks, 'checkpoints'))
                final_results[self.source_build][ks] = ret
                actual_run_cases.extend(list(ret.keys()))
                values = list(ret.values())
                pass_num = pass_num + values.count('passed')
                failed_num = failed_num + values.count('failed')
            break

        need_run_cases = list(self.casesmap.testcase_map.keys())
        final_results['sum'] = OrderedDict()
        final_results['sum']['title'] = self._gen_title()
        final_results['sum']['log_url'] = self._gen_log_url()
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
                        final_results, indent=4))

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
        ks_list = []
        for ks in final_results.get(self.source_build):
            ks_list.append(ks.encode())
        ks_list.sort()

        title = final_results.get("sum").get("title")

        tr = self.create_testrun(title)
        tr.group_id = self.source_build
        tr.description = '{} with {}'.format(title, ks_list)
        tr.status = 'finished'
        tr.update()

        print tr.uri
        print tr.test_run_id

        rets = final_results.get(self.source_build).values()
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
    parser.add_argument('--t', dest="target_build",
                        help="target build name when upgrading")
    parser.add_argument('--f', dest="test_flag",
                        help="the value should be install, upgrade, or vdsm")
    args = parser.parse_args()

    res_path = args.results_path
    tar_build = args.target_build
    test_flag = args.test_flag
    if args.p:
        action = '-p'
    if args.l:
        action = '-l'
    if args.b:
        action = '-b'

    r = ResultsToPolarion(res_path, action, test_flag, tar_build)
    r.run()
