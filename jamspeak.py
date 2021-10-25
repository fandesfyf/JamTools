#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/2 22:52
# @Author  : Fandes
# @FileName: jamspeak.py
# @Software: PyCharm
import os
import random
import sys
import time

import requests
from playsound import playsound


# https://fanyi.baidu.com/gettts?lan=en&text=web&spd=3&source=web
class Speaker():
    def __init__(self):
        self.url = "https://fanyi.baidu.com/gettts?lan={}&text={}&spd=3&source=web"
        self.replay = 0
        if not os.path.exists("./j_temp/speaker"):
            os.mkdir("./j_temp/speaker")

    def speak(self, text="none", lan="en", replay=False):
        self.replay = self.replay + 1 if replay else 0
        text = text.replace(" ", "_").replace("\n",".").replace(","," ").replace("，"," ")
        rfile = "./j_temp/speaker/{}.mp3".format(text)
        randname = "./j_temp/speaker/{}{}.mp3".format(text, random.randint(0, 99999))
        try:
            if not os.path.exists(rfile):
                print("重新获取")
                n = 0
                for i in text:
                    if self.is_alphabet(i):
                        n += 1
                if n / len(text) <= 0.4:
                    lan = "zh"

                url = self.url.format(lan, text)
                print(url)
                res = requests.get(url)
                with open(rfile, "wb")as f:
                    f.write(res.content)

            with open(rfile, "rb")as f:
                with open(randname, "wb")as wf:
                    wf.write(f.read())
            # time.sleep(1)
            playsound(randname, 1)
            os.remove(randname)
        except:
            e = sys.exc_info()
            if "指定的设备未打开" in e[1].args[0] and self.replay < 3:
                print("重放")
                time.sleep(0.1)
                try:
                    self.speak(text, replay=True)
                except:
                    print(sys.exc_info(),59,"重试失败")
            print(e, 39)

    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False


if __name__ == '__main__':
    s = Speaker()
    s.speak()
