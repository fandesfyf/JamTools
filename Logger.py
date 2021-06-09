#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/6/9 21:47
# @Author  : Fandes
# @FileName: Logger.py
# @Software: PyCharm

import io
import os
import sys, time


class Logger(object):
    def __init__(self, log_path="jamtools.log"):
        # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        self.terminal = sys.stdout
        if os.path.exists(log_path):
            ls = os.path.getsize(log_path)
            print("日志文件大小为:", ls," 保存于:", log_path)
            if ls > 2485760:
                print("日志文件过大")
                with open(log_path, "r+", encoding="utf-8")as f:
                    f.seek(ls - 1885760)
                    log = "已截断日志" + time.strftime("%Y-%m-%d %H:%M:%S:\n", time.localtime(time.time())) + f.read()
                    f.seek(0)
                    f.truncate()
                    f.write(log)
                print("新日志大小", os.path.getsize(log_path))
        self.log = open(log_path, "a", encoding='utf8')
        self.logtime = time.time()
        self.log.write("\n\nOPEN@" + time.strftime("%Y-%m-%d %H:%M:%S:\n", time.localtime(time.time())))

    def write(self, message):
        self.terminal.write(message)
        now = time.time()
        timestr = ""
        if now - self.logtime > 1:
            timestr = "\n@" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) + "-" * 40 + "\n"

        log = timestr + message
        self.log.write(log)
        if now - self.logtime > 1:
            self.logtime = now
            self.log.flush()
        self.terminal.flush()

    def flush(self):
        pass


if __name__ == '__main__':
    st = time.time()
    sys.stdout = Logger('hfks.log')
    print("fsdafwefs")
    print(time.time() - st)
    time.sleep(1.5)
    print(time.localtime())
    time.sleep(1.1)
    print("rtyuio" * 50)
