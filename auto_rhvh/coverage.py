import logging
import os
import time
import commands
from constants import PROJECT_ROOT

log = logging.getLogger('bender')


COV_RAW_RES_TAR_NAME = "coverage.tar.gz"
COV_ALL_RAW_RES_TAR_NAME = "coverages.tar.gz"
COV_HTML_RES_NAME = "htmlcov"
COV_HTML_RES_TAR_NAME = "{}.tar.gz".format(COV_HTML_RES_NAME)

COV_HOST_RAW_RES_PATH = "/boot/coverage/"
COV_HOST_DEAL_PATH = "/root"
COV_HOST_RAW_RES_TAR_PATH = os.path.join(
    COV_HOST_DEAL_PATH, COV_RAW_RES_TAR_NAME)

COV_LOCAL_DEAL_PATH = os.path.join(PROJECT_ROOT, 'logs', 'coverage', 'tmp')
COV_LOCAL_RAW_RES_TAR_PATH = os.path.join(
    COV_LOCAL_DEAL_PATH, COV_RAW_RES_TAR_NAME)
COV_LOCAL_ALL_RAW_RES_TAR_PATH = os.path.join(
    COV_LOCAL_DEAL_PATH, COV_ALL_RAW_RES_TAR_NAME)
COV_LOCAL_FINAL_RES_PATH = os.path.join(
    PROJECT_ROOT, 'logs', 'coverage')


def upload_coverage_raw_res_from_host(remotecmd):
    # To makeup local deal path:
    if not os.path.exists(COV_LOCAL_DEAL_PATH):
        os.makedirs(COV_LOCAL_DEAL_PATH)

    # To compress .coverage* files under /boot/coverage on host
    cmd = "tar -zcf {} -C {} .".format(COV_HOST_RAW_RES_TAR_PATH,
                                       COV_HOST_RAW_RES_PATH)
    ret = remotecmd.run_cmd(cmd, timeout=300)
    if not ret[0]:
        log.error("Failed to compress {}".format(COV_HOST_RAW_RES_PATH))
        return False

    # To upload coverage tar file to local server
    try:
        remotecmd.get_remote_file(
            COV_HOST_RAW_RES_TAR_PATH, COV_LOCAL_DEAL_PATH)
    except Exception as e:
        log.error(e)
        return False

    # To decompress coverage tar file on local server
    cmd = "tar -zxf {} -C {}".format(COV_LOCAL_RAW_RES_TAR_PATH,
                                     COV_LOCAL_DEAL_PATH)
    os.system(cmd)

    # To delete the coverage tar file on local server
    cmd = "rm -f {}".format(COV_LOCAL_RAW_RES_TAR_PATH)
    os.system(cmd)

    return True


def download_all_coverage_raw_res_to_host(remotecmd):
    # To compress all coverage file on local server
    cmd = "tar -zcf {} -C {} .".format(
        COV_LOCAL_ALL_RAW_RES_TAR_PATH, COV_LOCAL_DEAL_PATH)
    os.system(cmd)

    # To download the coverage files to host
    try:
        remotecmd.put_remote_file(
            COV_LOCAL_ALL_RAW_RES_TAR_PATH, COV_HOST_DEAL_PATH)
    except Exception as e:
        log.error(e)
        return False

    return True


def combine_all_coverage_raw_res_on_host(remotecmd):
    # To decompress coverage files on host
    cmd = "tar -zxf {}/{} -C {}".format(COV_HOST_DEAL_PATH,
                                        COV_ALL_RAW_RES_TAR_NAME, COV_HOST_DEAL_PATH)
    ret = remotecmd.run_cmd(cmd, timeout=300)
    if not ret[0]:
        log.error("Failed to decompress all coverage tar on host")
        return False

    # To combine all coverages
    cmd = "coverage combine {}".format(COV_HOST_DEAL_PATH)
    ret = remotecmd.run_cmd(cmd, timeout=300)
    if not ret[0]:
        log.error("Failed to combine coverage on host")
        return False

    return True


def generate_coverage_html_res_on_host(remotecmd):
    cmd = "coverage html -d {}/{}".format(COV_HOST_DEAL_PATH,
                                          COV_HTML_RES_NAME)
    ret = remotecmd.run_cmd(cmd, timeout=300)
    if not ret[0]:
        log.error("Failed to gen coverage html on host")
        return False

    # To compress the html result
    cmd = "tar -zcf {0}/{1}.tar.gz -C {0} {1}".format(
        COV_HOST_DEAL_PATH, COV_HTML_RES_NAME)
    ret = remotecmd.run_cmd(cmd, timeout=300)
    if not ret[0]:
        log.error("Failed to compress html result on host")
        return False

    return True


def upload_coverage_html_res_to_server(remotecmd, src_build):
    final_result_path = os.path.join(
        COV_LOCAL_FINAL_RES_PATH, src_build)
    if not os.path.exists(final_result_path):
        os.mkdir(final_result_path)
    else:
        os.system("rm -rf {}/*".format(final_result_path))

    # To get html result from host
    remote_file = "{}/{}".format(COV_HOST_DEAL_PATH,
                                 COV_HTML_RES_TAR_NAME)
    try:
        remotecmd.get_remote_file(remote_file, final_result_path)
    except Exception as e:
        log.error(e)
        return False

    # To decompress html result
    cmd = "tar -zxf {}/{} -C {}".format(
        final_result_path, COV_HTML_RES_TAR_NAME, final_result_path)
    os.system(cmd)

    cmd = "rm -f {}/{}".format(final_result_path, COV_HTML_RES_TAR_NAME)
    os.system(cmd)

    cmd = "mv {} {}".format(COV_LOCAL_ALL_RAW_RES_TAR_PATH, final_result_path)
    os.system(cmd)

    cmd = "rm -rf {}".format(COV_LOCAL_DEAL_PATH)
    os.system(cmd)

    return True


def generate_final_coverage_result(remotecmd, src_build):
    if not download_all_coverage_raw_res_to_host(remotecmd):
        return False
    if not combine_all_coverage_raw_res_on_host(remotecmd):
        return False
    if not generate_coverage_html_res_on_host(remotecmd):
        return False
    if not upload_coverage_html_res_to_server(remotecmd, src_build):
        return False
    return True
