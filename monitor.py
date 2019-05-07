#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dogxxgod@yeah.net

import os
import sys
import re
import time
import json
import threading
import psutil
import logging

interval = 20
datadir = '/tmp/pidstat/'
single_fields = ['status', 'pid', 'create_time', 'cwd', 'username',
                 'name', 'ppid', 'exe', 'num_threads', 'num_fds', 'cmdline']

obj_fields = {
    'io_counters': ['read_count', 'write_count', 'read_bytes', 'write_bytes', 'read_chars', 'write_chars'],
    'memory_full_info': ['rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss', 'swap']}


sys_single_fields = ['cpu_percent', ]

sys_obj_fields = {
    'cpu_times_percent': ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice'],
    'net_io_counters': ['bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv', 'errin', 'errout', 'dropin', 'dropout'],
    'virtual_memory': ['total', 'available', 'percent', 'used', 'free', 'active', 'inactive', 'buffers', 'cached', 'shared', 'slab'],
    'disk_io_counters': ['read_count', 'write_count', 'read_bytes', 'write_bytes', 'read_time', 'write_time', 'read_merged_count', 'write_merged_count', 'busy_time']
}


def obj2dict(obj, fields):
    rt = {}
    try:
        is_dict = isinstance(obj, dict)
        for f in fields:
            if is_dict:
                v = obj[f]
            else:
                v = getattr(obj, f)
            if hasattr(v, '__call__'):
                v = v()
            rt[f] = v
    except:
        print obj
        logging.exception('getattr error')
    return rt


def get_pid_info(pid, ts):
    try:
        p = psutil.Process(pid).as_dict()
        info = obj2dict(p, single_fields)
        #print 'info..',info
        info['ts'] = ts
        for k, v in obj_fields.items():
            info[k] = obj2dict(p[k], v)

        save_info(info)
    except:
        logging.exception('get_pid_info error')


def get_sys_info(ts):
    try:
        info = obj2dict(psutil, sys_single_fields)
        #print 'info..',info
        info['ts'] = ts
        info['pid'] = 0
        for k, v in sys_obj_fields.items():
            info[k] = obj2dict(getattr(psutil, k)(), v)
        save_info(info)
    except:
        logging.exception('get_sys_info error')


def save_info(info):
    filepath = os.path.join(datadir, 'pid_'+str(info['pid'])+'.stat')
    with open(filepath, 'a') as fw:
        fw.write(json.dumps(info))
        fw.write(',')
        fw.close()


def get_pid_by_pattern(pattern_str):
    me = sys.argv[0]
    mepattern = ".*%s.*" % me
    pattern = ".*%s.*" % pattern_str
    for p in psutil.process_iter():
        cmdline = " ".join(p.cmdline())
        # if re.match(pattern, cmdline):
        if re.match(pattern, cmdline) and not re.match(mepattern, cmdline):
            yield p.pid
#    raise OSError


def main():
    process_patterns = ['postgres', 'python', 'redis', 'uwsgi']
    while True:
        process_lst = []
        for pat in process_patterns:
            process_lst.extend([pid for pid in get_pid_by_pattern(pat)])
        process_lst = set(process_lst)
        threads = []
        ts = time.time()
        for p in process_lst:
            threads.append(threading.Thread(target=get_pid_info, args=(p, ts)))
        threads.append(threading.Thread(target=get_sys_info, args=(ts,)))
        for t in threads:
            t.setDaemon(True)

        for t in threads:
            t.start()

        time.sleep(interval)
        # sys.exit()


if __name__ == "__main__":

    main()
