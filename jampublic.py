#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2020/11/13 22:42
# @Author  : Fandes
# @FileName: public.py
# @Software: PyCharm
import hashlib
import http.client
import os
import random
import re
import sys
import time

import requests
from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QStandardPaths, QTimer, QSettings, QFileInfo, \
    QUrl, QObject, QSize
from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QSettings, QSizeF, QStandardPaths, QUrl
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QBrush, QTextDocument, QTextCursor, QDesktopServices
from PyQt5.QtGui import QPainter, QPen, QIcon, QFont
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit, QWidget
from aip import AipOcr, AipImageClassify
from urllib.parse import quote

from fake_useragent import UserAgent

from jamspeak import Speaker

APP_ID = QSettings('Fandes', 'jamtools').value('BaiduAI_APPID', '17302981', str)  # 获取的 ID，下同
API_KEY = QSettings('Fandes', 'jamtools').value('BaiduAI_APPKEY', 'wuYjn1T9GxGIXvlNkPa9QWsw', str)
SECRECT_KEY = QSettings('Fandes', 'jamtools').value('BaiduAI_SECRECT_KEY', '89wrg1oEiDzh5r0L63NmWeYNZEWUNqvG', str)
print("platform is", sys.platform)
PLATFORM_SYS = sys.platform
CONFIG_DICT = {"last_pic_save_name":"{}".format( str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime())))}

def get_apppath():
    p = sys.path[0].replace("\\", "/").rstrip("/") if os.path.isdir(sys.path[0]) else os.path.split(sys.path[0])[0]
    # print("apppath",p)
    if sys.platform == "darwin" and p.endswith("MacOS"):
        p = os.path.join(p.rstrip("MacOS"), "Resources")
    return p


apppath = get_apppath()

def get_UserAgent():
    ua = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36 Edg/108.0.1462.54"
    try:
        ua_file = os.path.join(apppath,"fake_useragent_0.1.11.json")
        if os.path.exists(ua_file):
            ua = UserAgent(path=os.path.join(apppath,"fake_useragent_0.1.11.json"),verify_ssl=False).random
        else:
            ua = UserAgent(verify_ssl=False).random
    except Exception as e:
        print(e,"get_UserAgent")
    return ua
def gethtml(url, times=3):  # 下载一个链接
    try:
        ua = get_UserAgent()
        response = requests.get(url, headers={"User-Agent": ua}, timeout=8, verify=False)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text

    except Exception as e:
        print(sys.exc_info(), '重试中')
        time.sleep(1)
        if times > 0:
            gethtml(url, times=times - 1)
        else:
            return "网络连接失败!"
class TipsShower(QLabel):
    def __init__(self, text, targetarea=(0, 0, 0, 0), parent=None, fontsize=35, timeout=1000):
        super().__init__(parent)
        self.parent = parent
        self.area = targetarea
        self.timeout = timeout
        self.rfont = QFont('', fontsize)
        self.setFont(self.rfont)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)
        self.setText(text)

        self.show()

        self.setStyleSheet("color:white")

    def setText(self, text, autoclose=True, font: QFont = None, color: QColor = None) -> None:
        super(TipsShower, self).setText(text)
        print("settext")
        self.adjustSize()
        x, y, w, h = self.area
        if x < QApplication.desktop().width() - x - w:
            self.move(x + w + 5, y)
        else:
            self.move(x - self.width() - 5, y)
        self.show()
        if autoclose:
            self.timer.start(self.timeout)
        if font is not None:
            print("更换字体")
            self.setFont(font)
        if font is not None:
            self.setStyleSheet("color:{}".format(color.name()))

    def hide(self) -> None:
        super(TipsShower, self).hide()
        self.timer.stop()
        self.setFont(self.rfont)
        self.setStyleSheet("color:white")

    def textAreaChanged(self, minsize=0):
        self.document.adjustSize()
        newWidth = self.document.size().width() + 25
        newHeight = self.document.size().height() + 15
        if newWidth != self.width():
            if newWidth < minsize:
                self.setFixedWidth(minsize)
            else:
                self.setFixedWidth(newWidth)
        if newHeight != self.height():
            if newHeight < minsize:
                self.setFixedHeight(minsize)
            else:
                self.setFixedHeight(newHeight)



class linelabel(QLabel):
    def __init__(self, parent):
        super(linelabel, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, e):
        super(linelabel, self).paintEvent(e)
        painter = QPainter(self)
        brush = QBrush(Qt.Dense7Pattern)
        painter.setBrush(brush)
        painter.drawRect(0, 0, self.width(), self.height())
        painter.end()



class mutilocr(QThread):
    statusbarsignal = pyqtSignal(str)
    ocr_signal = pyqtSignal(str, str)

    def __init__(self, files):
        super(mutilocr, self).__init__()
        self.files = files
        self.threadlist = []
        self.filename = ""

    def run(self) -> None:
        for file in self.files:
            self.statusbarsignal.emit('开始识别图片')
            filename = os.path.basename(file)
            self.filename = filename
            with open(file, 'rb')as i:
                img = i.read()
            print("正在识别图片：\t" + filename)
            self.statusbarsignal.emit('正在识别: ' + filename)

            th = OcrimgThread(filename, img, 1)
            th.result_show_signal.connect(self.mutil_cla_signalhandle)
            th.start()
            th.wait()
            self.threadlist.append(th)

    def mutil_cla_signalhandle(self, text):
        print("aaaa mutil_cla_signalhandle")
        self.ocr_signal.emit(self.filename, text)
        print("已识别{}".format(self.filename))


class OcrimgThread(QThread):
    # simple_show_signal = pyqtSignal(str)
    result_show_signal = pyqtSignal(str)
    statusbar_signal = pyqtSignal(str)

    def __init__(self, args0, args1, ocrorimg=0):
        super(QThread, self).__init__()
        self.args0 = args0
        self.ocr = ocrorimg
        self.args = args1  # img
        # self.simple_show_signal.connect(jamtools.simple_show)

    def run(self):
        self.statusbar_signal.emit('正在识别文字...')
        if self.ocr == 1:
            try:
                client = AipOcr(APP_ID, API_KEY, SECRECT_KEY)
                # message = client.basicGeneral(self.args)  # 通用文字识别，每天 50 000 次免费
                message = client.basicAccurate(self.args)  # 通用文字高精度识别，每天 800 次免费
                text = ''
                # 输出文本内容
                # print("xxx", message.values())
                for res in message.get('words_result'):
                    text += res.get('words') + '\n'

            except:
                print("Unexpected error:", sys.exc_info(), "jampublic l326")
                self.statusbar_signal.emit('识别出错！请确保网络畅通')
                text = str(sys.exc_info()[0])
            # print(text)
            if text == '':
                text = '空'

            self.result_show_signal.emit(text)
            self.statusbar_signal.emit('识别完成！')

        elif self.ocr == 2:
            text = ''
            try:
                client = AipImageClassify(APP_ID, API_KEY, SECRECT_KEY)
                result = client.advancedGeneral(self.args0, self.args)['result']
                for i in result:
                    # print(i['keyword'],i['score'])
                    temp = str(i['keyword']) + str(i['score'])
                    text += temp + '\n'
            except KeyError:
                self.statusbar_signal.emit('识别出错！图像大小不正确！')
                text = '识别出错！图像大小不正确！'
            except:
                print("Unexpected error:", sys.exc_info()[0])
                text = "Unexpected error:" + str(sys.exc_info()[0])
                self.statusbar_signal.emit('识别出错！请确保网络畅通')
                # print(result)
                # jamtools.tra_from_edit.clear()
            self.result_show_signal.emit(text)
            self.statusbar_signal.emit("识图完成！")
        print("识别完成")


class Transparent_windows(QLabel):
    def __init__(self, x=0, y=0, w=0, h=0, color=Qt.red, havelabel=False):
        super().__init__()
        self.setGeometry(x - 5, y - 5, w + 10, h + 10)
        self.area = (x, y, w, h)
        self.x, self.y, self.w, self.h = x, y, w, h
        self.color = color
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        if havelabel:
            self.label = QLabel(self)
            self.label.setGeometry(self.w - 55, 6 + self.h + 1, 60, 14)
            self.label.setStyleSheet("color: green;border: 2 px;font-weight:bold;")

    def setGeometry(self, x, y, w, h):
        super(Transparent_windows, self).setGeometry(x - 5, y - 5, w + 10, h + 10)
        self.area = (x, y, w, h)

    def paintEvent(self, e):
        super().paintEvent(e)
        x, y, w, h = self.area
        p = QPainter(self)
        p.setPen(QPen(self.color, 2, Qt.SolidLine))
        p.drawRect(QRect(3, 3, w + 4, h + 4))
        p.end()


class Commen_Thread(QThread):
    def __init__(self, action, *args):
        super(QThread, self).__init__()
        self.action = action
        self.args = args

    def run(self):
        print('start_thread params:{}'.format(self.args))
        if self.args:
            print(self.args)
            if len(self.args) == 1:
                self.action(self.args[0])
            elif len(self.args) == 2:
                self.action(self.args[0], self.args[1])
            elif len(self.args) == 3:
                self.action(self.args[0], self.args[1], self.args[2])
            elif len(self.args) == 4:
                self.action(self.args[0], self.args[1], self.args[2], self.args[3])
        else:
            self.action()



if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # w = Transparent_windows(20, 20, 500, 200)
    # w.show()
    import json
    a = gethtml("https://raw.githubusercontent.com/fandesfyf/JamTools/main/ci_scripts/versions.json")
    print(json.loads(a))
    # w.setGeometry()
    # sys.exit(app.exec_())
