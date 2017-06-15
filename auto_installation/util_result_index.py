import os
import json
from constants import PROJECT_ROOT

LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs') + '/'


def walk_the_logs():
    """=+_="""
    summary = dict()
    for dpath, dnames, files in os.walk(LOGS_DIR):
        if 'final_results.json' in files:
            tmp = dpath.replace(LOGS_DIR, '').split('/')
            date = tmp[0]
            time_build = tmp[1] + '__' + tmp[2]
            final_res = json.load(open(os.path.join(dpath, files[0])))['sum']

            if summary.get(date, None):
                summary[date][time_build] = [dnames, final_res]
            else:
                summary[date] = {time_build: [dnames, final_res]}

    return summary


if __name__ == "__main__":
    walk_the_logs()
