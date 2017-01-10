import os
import time
import datetime
from pylarion.test_run import TestRun
from constants import TR_ID, TR_PROJECT_ID, TR_TPL, KS_TESTCASE_MAP

# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


def make_test_run():
    return TestRun(
        project_id=TR_PROJECT_ID,
        test_run_id='4_0_Node_0622_AutoInstallWithKickstart_Must')


class ResultsToPolarion(object):
    """
    /home/dracher/Projects/Zoidberg/app/logs/2016-06-21/rhev-hypervisor7-ng-4.0-20160616.0/ati_FC_01.ks/checkpoints
    """

    def __init__(self, path):
        self.path = path.rstrip('/')
        _path = self.path.split('/')
        self.build = _path[-2]
        self.root_path = os.path.join('/', *_path[:-1])
        self.ks_list = os.listdir(self.root_path)

    @staticmethod
    def get_current_date():
        return time.strftime("%m%d%H%M", time.localtime())

    def create_testrun(self, level='Must'):
        ret = TestRun.create(TR_PROJECT_ID,
                             TR_ID.format(self.get_current_date(), level),
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

        for a, b, c in os.walk(self.root_path):
            for ks in b:
                print ks
                with open(os.path.join(a, ks, 'checkpoints')) as fp:
                    if 'False' in fp.readlines()[-1]:
                        self.export_to_polarion(tr,
                                                KS_TESTCASE_MAP.get(ks),
                                                'failed')
                        # tr.add_attachment_to_test_record(test_case_id=KS_TESTCASE_MAP.get(ks),
                        #                                  path=fp.name,
                        #                                  title='failedLogs')
                    else:
                        self.export_to_polarion(tr,
                                                KS_TESTCASE_MAP.get(ks),
                                                'passed')

                print "be nice with server, sleep 1 sec"
                time.sleep(1)
            break


if __name__ == '__main__':
    r = ResultsToPolarion(
        '/home/dracher/Projects/Zoidberg/app/logs/2017-01-05/redhat-virtualization-host-4.0-20170104.0/ati_autopart_01.ks'
    )
    r.run()

    # tr = TestRun(project_id='RHEVM3', test_run_id='4_0_Node_06221451_AutoInstallWithKickstart_Must')
    # tr.add_attachment_to_test_record(test_case_id='RHEVM-15058', path='/home/dracher/Projects/Zoidberg/app/logs/2016-06-21/rhev-hypervisor7-ng-4.0-20160616.0/ati_network_01.ks/checkpoints', title='failedLogs')
# /logs/2016-09-08/redhat-virtualization-host-4.0-20160906.0/ati_autopart_01.ks/results
