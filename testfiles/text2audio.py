#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 09:37:38 2018
利用百度api实现图片文本识别
@author: XnCSD
"""

import glob
import time
from os import path
import os
import aip
import mp3play
from pygame import mixer
import webbrowser



APP_ID = '17302981'  # 刚才获取的 ID，下同
API_KEY = 'wuYjn1T9GxGIXvlNkPa9QWsw'
SECRECT_KEY = '89wrg1oEiDzh5r0L63NmWeYNZEWUNqvG'



def BaiduOCR(file):
    """利用百度api识别文本，并保存提取的文字
    picfile:    图片文件名
    outfile:    输出文件
    """



    client = aip.AipSpeech(APP_ID, API_KEY, SECRECT_KEY)

    # i = open(picfile, 'rb')
    # img = i.read()
    # print(img)
    # print("正在识别图片：\t" + filename)
    message = client.synthesis("滚哼",'zh', 1, {'vol': 4,'spd':4,'pit':5,'per':4})
    # 通用文字识别，每天 50 000 次免费spd语速pit音调，取值0-9vol音量per发音人选择, 0为女声，1为男声，
    # 3为情感合成-度逍遥，4为情感合成-度丫丫，默认为普通女
    # print(message)
    # message = client.basicAccurate(img)   # 通用文字高精度识别，每天 800 次免费
    # print("识别成功！")
    # i.close()
    if not isinstance(message, dict):
        with open('auido.mp3', 'wb') as f:
            f.write(message)
    webbrowser.open("auido.mp3")
    # mixer.init()
    #
    # mixer.music.load("auido.mp3")
    #
    # mixer.music.play()
    # with open(outfile, 'a+') as fo:
    #     fo.writelines("+" * 60 + '\n')
    #     fo.writelines("识别图片：\t" + filename + "\n" * 2)
    #     fo.writelines("文本内容：\n")
    #     # 输出文本内容
    #     for text in message.get('words_result'):
    #         fo.writelines(text.get('words') + '\n')
    #     fo.writelines('\n' * 2)
    #     print("文本导出成功！")


if __name__ == "__main__":

    # outfile = 'export.txt'
    # outdir = 'tmp'
    # if path.exists(outfile):
    #     os.remove(outfile)
    # if not path.exists(outdir):
    #     os.mkdir(outdir)
    # # print("压缩过大的图片...")
    # # // 首先对过大的图片进行压缩，以提高识别速度，将压缩的图片保存与临时文件夹中
    # for picfile in glob.glob("screenshots/*"):
    #     convertimg(picfile, outdir)
    # # print("图片识别...")
    # for picfile in glob.glob("tmp/*"):
    #     BaiduOCR(picfile, outfile)
    #     os.remove(picfile)
    # # print('图片文本提取结束！文本输出结果位于 %s 文件中。' % outfile)
    # os.removedirs(outdir)
    BaiduOCR(0)
