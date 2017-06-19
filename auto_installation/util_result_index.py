import os
import json
from constants import PROJECT_ROOT

LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs') + '/'


def walk_the_logs():
    """=+_="""
    summary = dict()
    for dpath, dnames, files in os.walk(LOGS_DIR):
        if 'final_results.json' in files:
            index = files.index('final_results.json')
            tmp = dpath.replace(LOGS_DIR, '').split('/')
            date = tmp[0]
            time_build = tmp[1] + '__' + tmp[2]
            try:
                final_res = json.load(
                    open(os.path.join(dpath, files[index])))['sum']
            except ValueError:
                print("erros exists in file:: " + os.path.join(
                    dpath, files[index]))
                continue

            if summary.get(date, None):
                summary[date][time_build] = [dnames, final_res]
            else:
                summary[date] = {time_build: [dnames, final_res]}

    return summary


if __name__ == "__main__":
    pass
