import os
import json
from constants import PROJECT_ROOT
from utils import init_redis

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


def cache_logs_summary():
    conn = init_redis()
    logs = json.dumps(walk_the_logs())
    conn.set("logs_summary", logs)


if __name__ == "__main__":
    cache_logs_summary()
