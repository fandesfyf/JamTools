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
import pyttsx3
import pyttsx3.drivers
import pyttsx3.drivers.sapi5

try:
    speaker_engine = pyttsx3.init()
except:
    e = sys.exc_info()
    if "libespeak.so" in e[1].args[0]:
        try:
            os.system("sudo apt-get install espeak -y")
        except Exception as ex:
            print("linux下驱动未安装,请尝试使用`sudo apt-get install espeak`命令进行安装",ex)
    print(e, __file__)
    speaker_engine = None
class Speaker():        
    def speak(self, text="none", lan="en"):
        try:
            self.stop()
            speaker_engine.say(text)
            # speaker_engine.startLoop(False)
            speaker_engine.runAndWait()
        except:
            e = sys.exc_info()
            if "libespeak.so" in e[1].args[0]:
                try:
                    os.system("sudo apt-get install espeak -y")
                except Exception as ex:
                    print("linux下驱动未安装,请尝试使用`sudo apt-get install espeak`命令进行安装",ex)
            print(e, __file__)
    def stop(self):
        if speaker_engine is not None and speaker_engine.isBusy():
            speaker_engine.stop()
    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False


if __name__ == '__main__':
    s = Speaker()
    s.speak()
