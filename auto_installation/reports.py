import os
import time
import datetime
from pylarion.test_run import TestRun
from constants import TR_ID, TR_PROJECT_ID, TR_TPL
import sys
import json

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def make_test_run():
    return TestRun(
        project_id=TR_PROJECT_ID,
        test_run_id='4_0_Node_0622_AutoInstallWithKickstart_Must')


class ResultsToPolarion(object):
    """
    /home/dracher/Zoidberg/logs/2017-03-08/redhat-virtualization-host-4.1-20170208.0/final_results.json
    """

    def __init__(self, path):
        self.final_results = json.load(open(path))
        self.build = self.final_results.get('sum').get('build')
        self.ks_list = self.final_results.get(self.build).keys()

    @staticmethod
    def get_current_date():
        return time.strftime("%m%d%H%M", time.localtime())

    def create_testrun(self, level='Must'):
        ret = TestRun.create(TR_PROJECT_ID,
                             TR_ID.format(self.build, self.get_current_date()),
                             TR_TPL.format(level))
        return ret

    # def add_attachment_to_record(self, tr=None):
    #     tr.add_attachment_to_test_record(test_case_id='RHEVM-15058',
    #                                      path='/home/dracher/Projects/Zoidberg/app/logs/2016-06-21/rhev-hypervisor7-ng-4.0-20160616.0/ati_services_01.ks/checkpoints',
    #                                      title='results')

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

    def run(self):
        tr = self.create_testrun()
        tr.group_id = self.build
        tr.description = 'automatic installation use {} with {}'.format(
            self.build, self.ks_list)
        tr.status = 'finished'
        tr.update()

        print tr.uri
        print tr.test_run_id
        
        rets = self.final_results.get(self.build).values()
        for ret in rets:
            for k, v in ret.items():
                self.export_to_polarion(tr, k, v)
                    
                print "be nice with server, sleep 1 sec"
                time.sleep(1) 


if __name__ == '__main__':
    res_path = os.path.realpath(sys.argv[1])

    r = ResultsToPolarion(res_path)
    r.run()

    # tr = TestRun(project_id='RHEVM3', test_run_id='4_0_Node_06221451_AutoInstallWithKickstart_Must')
    # tr.add_attachment_to_test_record(test_case_id='RHEVM-15058', path='/home/dracher/Projects/Zoidberg/app/logs/2016-06-21/rhev-hypervisor7-ng-4.0-20160616.0/ati_network_01.ks/checkpoints', title='failedLogs')
# /logs/2016-09-08/redhat-virtualization-host-4.0-20160906.0/ati_autopart_01.ks/results
