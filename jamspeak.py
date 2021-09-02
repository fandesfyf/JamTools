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

    def speak(self, text="none", lan="en", replay=False):
        self.replay = self.replay + 1 if replay else 0
        try:
            n = 0
            for i in text:
                if self.is_alphabet(i):
                    n += 1
            if n / len(text) <= 0.4:
                lan = "zh"
            text = text.replace(" ", "_")
            url = self.url.format(lan, text)
            print(url)
            res = requests.get(url)
            randname = "{}.mp3".format(random.randint(1000, 9999))
            with open(randname, "wb")as f:
                f.write(res.content)
            # self.play_bytes(res.content)
            playsound(randname, 1)
            os.remove(randname)
        except:
            e = sys.exc_info()
            if "指定的设备未打开" in e[1].args[0] and self.replay < 3:
                time.sleep(0.1)
                self.speak(text, replay=True)
                print("重放")
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
