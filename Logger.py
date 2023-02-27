#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/6/9 21:47
# @Author  : Fandes
# @FileName: Logger.py
# @Software: PyCharm

import io
import os
import sys, time

from PyQt5.QtCore import QThread


class Logger(QThread):
    def __init__(self, log_path="jamtools.log"):
        super(Logger, self).__init__()
        # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        self.terminal = sys.stdout
        self.log_path = log_path
        self.logtime = time.time() - 2
        self.loglist = []
        self.start()

    def run(self) -> None:
        if os.path.exists(self.log_path):
            try:
                ls = os.path.getsize(self.log_path)
                print("日志文件大小为:", ls, " 保存于:", self.log_path)
                if ls > 2485760:
                    print("日志文件过大")
                    with open(self.log_path, "r+", encoding="utf8")as f:
                        f.seek(ls - 1885760)
                        log = "已截断日志" + time.strftime("%Y-%m-%d %H:%M:%S:\n", time.localtime(time.time())) + f.read()
                        f.seek(0)
                        f.truncate()
                        f.write(log)
                    print("新日志大小", os.path.getsize(self.log_path))
            except Exception as e:
                with open(self.log_path, "w", encoding="utf8")as f:
                    f.write("已清空日志, {}".format(e))
        self.log = open(self.log_path, "a", encoding='utf8')
        self.log.write("\n\nOPEN@" + time.strftime("%Y-%m-%d %H:%M:%S:\n", time.localtime(time.time())))
        try:
            while True:
                if len(self.loglist):
                    self.process(self.loglist.pop(0))
                else:
                    time.sleep(0.05)
        except:
            print(sys.exc_info(), "log47")

    def write(self, message):
        self.loglist.append(message)

    def process(self, message):
        self.terminal.write(message)
        now = time.time()
        timestr = ""
        if now - self.logtime > 1:
            timestr = "\n"+"-" * 20 + "@" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) + "-" * 20 + "\n"

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
