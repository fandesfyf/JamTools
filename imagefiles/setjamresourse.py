#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2020/12/11 11:15
# @Author  : Fandes
# @FileName: setjamresourse.py
# @Software: PyCharm

import os
import shutil
import subprocess, setuptools

imglist = ["p.png", "ico.png", "tra.png", "screenshot.png", "record.png", "OCR.png", "MOCR.png", "CLA.png", "chat.png",
           "Control.png", "switch.png", "filestransmitter.png", "wjj.png", "rect.png", "pen.png", "yst.png", "msk.jpg",
           "mskicon.png", "search.png", "backgrounderaser.png", "eraser.png", "arrow.png", "arrowicon.png",
           "circle.png", "texticon.png", "saveicon.png", "recording.png", "scroll_icon.png", "freeze.png",
           "timetable.png", "ssrecord.png", "choice_path.png", "add.png", "remove.png", "update.png", "why.png",
           "load.gif", "original.png", "sound0.png", "sound3.png", "smartcursor.png", "colorsampler.png", "yqt.png",
           "backgroundrepair.png", "perspective.png", "polygon_ss.png", "last.png", "next.png", "videowjj.png",
           "clear.png"

           ]
with open("jamresourse.qrc", "w", encoding="utf-8")as qrcf:
    qrcf.write('<!DOCTYPE RCC>\n<RCC version="1.0">\n<qresource>')
    for png in imglist:
        if os.path.exists(png):
            qrcf.write("\t<file>{}</file>\n".format(png))
        else:
            print("找不到{}".format(png))
    qrcf.write("""</qresource>\n</RCC>""")
print("正在生成...")
Compiler = subprocess.Popen('pyrcc5 jamresourse.qrc -o jamresourse.py', shell=True)
Compiler.wait()
print("复制jamresourse.py")
shutil.copy2('jamresourse.py', r'..\jamresourse.py')
