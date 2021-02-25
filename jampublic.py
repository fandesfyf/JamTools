#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2020/11/13 22:42
# @Author  : Fandes
# @FileName: public.py
# @Software: PyCharm
import hashlib
import http.client
import random
import re
import sys

from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPainter, QPen, QIcon, QFont
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit
from aip import AipOcr, AipImageClassify
from urllib.parse import quote

APP_ID = QSettings('Fandes', 'jamtools').value('BaiduAI_APPID', '17302981', str)  # 获取的 ID，下同
API_KEY = QSettings('Fandes', 'jamtools').value('BaiduAI_APPKEY', 'wuYjn1T9GxGIXvlNkPa9QWsw', str)
SECRECT_KEY = QSettings('Fandes', 'jamtools').value('BaiduAI_SECRECT_KEY', '89wrg1oEiDzh5r0L63NmWeYNZEWUNqvG', str)
print("platform is", sys.platform)
PLATFORM_SYS = sys.platform



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


class FramelessEnterSendQTextEdit(QTextEdit):  # 无边框回车文本框
    clear_signal = pyqtSignal()
    showm_signal=pyqtSignal(str)

    def __init__(self, parent=None,enter_tra=False):
        super().__init__(parent)
        self.parent = parent
        self.action = self.show
        self.moving = False
        self.document = self.document()
        self.document.contentsChanged.connect(self.textAreaChanged)
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFont(QFont('', 8))
        self.setPlaceholderText('...')
        self.setStyleSheet("QPushButton{color:black}"
                           "QPushButton:hover{color:green}"
                           "QPushButton:hover{background-color:rgb(200,200,100)}"
                           "QPushButton{background-color:rgb(239,239,239)}"
                           "QPushButton{padding:1px 4px }"
                           "QScrollBar{width:3px;border:none; background-color:rgb(200,200,200);"
                           "border-radius: 8px;}"
                           )
        self.colse_botton = QPushButton('X', self)
        self.colse_botton.setToolTip('关闭')
        self.colse_botton.setGeometry(self.width() - 20, 2, 18, 18)
        self.colse_botton.clicked.connect(self.hide)
        self.colse_botton.show()
        self.colse_botton.setStyleSheet(
            "QPushButton{color:black}"
            "QPushButton{background-color:rgb(239,0,0)}"
            "QPushButton:hover{color:green}"
            "QPushButton:hover{background-color:rgb(200,50,0)}"
            "QPushButton{border-radius:9};")
        self.tra_botton = QPushButton(QIcon(':/tra.png'), '', self)
        self.tra_botton.resize(25, 25)
        self.tra_botton.move(self.width() - 28, self.height() - 26)
        self.tra_botton.clicked.connect(self.tra)
        self.tra_botton.setToolTip('翻译')
        self.tra_botton.show()
        self.setToolTip('回车可快速翻译,拖动边框可改变位置')
        self.clear_signal.connect(self.clear)
        if enter_tra:
            self.action = self.tra

    def tra(self):
        # self.transtalater_signal.emit()
        # transtalater.Bdtra()
        self.showm_signal.emit("正在翻译..")
        text=self.toPlainText()
        text = re.sub(r'[^\w]', '', text).replace('_', '')
        print(text)
        n=0
        for i in text:
            if self.is_alphabet(i):
                n += 1
        if n / len(text) > 0.4:
            print("is en")
            fr="en"
            to="zh"
        else:
            fr="zh"
            to="en"
        self.traThread = TrThread(self.toPlainText(),fr, to)
        self.traThread.resultsignal.connect(self.insertPlainText)
        self.traThread.start()
    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False
    def textAreaChanged(self, minsize=100):
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
        self.colse_botton.move(self.width() - 20, 2)
        self.tra_botton.move(self.width() - 28, self.height() - 26)

    def get_tra_resultsignal(self, text):
        self.insertPlainText("\n翻译结果:\n{}".format(text))

    def insertPlainText(self, text):
        super(FramelessEnterSendQTextEdit, self).insertPlainText(text)
        self.show()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if e.x() > self.width() - 25 or e.y() < 10 or e.y() > self.height() - 20:
                self.moving = True
                self.dx = e.x()
                self.dy = e.y()
                self.viewport().setCursor(Qt.SizeAllCursor)
                self.viewport().update()
            else:
                super().mousePressEvent(e)
            # self.update()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if e.button() == Qt.LeftButton:
            self.moving = False
            self.viewport().setCursor(Qt.ArrowCursor)
            self.viewport().update()

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        if self.isVisible():

            if e.x() > self.width() - 25 or e.y() < 10 or e.y() > self.height() - 20:
                self.viewport().setCursor(Qt.SizeAllCursor)
                if self.moving:
                    # print(e.x()+self.x()-self.dx,e.y()+self.y()-self.dy)
                    self.move(e.x() + self.x() - self.dx, e.y() + self.y() - self.dy)
            else:
                self.viewport().setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_Return:
            try:
                if QApplication.keyboardModifiers() in (Qt.ShiftModifier, Qt.ControlModifier, Qt.AltModifier):
                    if QApplication.keyboardModifiers() in (Qt.ControlModifier, Qt.AltModifier):
                        self.insertPlainText('\n')
                    else:
                        # print('enter')
                        pass
                else:
                    # print('returnkey')
                    self.action()
            except:
                print('回车失败')
            return

    def keyenter_connect(self, action):
        self.action = action


class TrThread(QThread):
    resultsignal = pyqtSignal(str)
    showm_singal = pyqtSignal(str)
    change_item_signal = pyqtSignal(str)

    def __init__(self, text, from_lan, to_lan):
        super(QThread, self).__init__()
        self.text = text
        self.toLang = to_lan
        # self.resultsignal.connect(transtalater.translate_signal)
        self.appid = QSettings('Fandes', 'jamtools').value('tran_appid', '20190928000337891', str)
        self.secretKey = QSettings('Fandes', 'jamtools').value('tran_secretKey', 'SiNITAufl_JCVpk7fAUS', str)
        salt = str(random.randint(32768, 65536))
        sign = self.appid + self.text + salt + self.secretKey
        m1 = hashlib.md5()
        m1.update(sign.encode(encoding='utf-8'))
        sign = m1.hexdigest()
        self.re_url = '/api/trans/vip/translate?appid=' + self.appid + '&q=' + quote(
            self.text) + '&from=' + from_lan + '&to={0}&salt=' + str(
            salt) + '&sign=' + sign
        self.geturl = self.re_url.format(self.toLang)

    def run(self):
        try:
            # res = requests.get("https://api.fanyi.baidu.com", params=self.args)
            # print(res)
            httpClient0 = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient0.request('GET', self.geturl)
            response = httpClient0.getresponse()
        except:
            print(sys.exc_info())
            self.showm_singal.emit("翻译出错！请确保网络畅通！{}".format(sys.exc_info()[0]))
        else:
            s = response.read().decode('utf-8')
            print(s)
            s = eval(s)
            text = ''
            # print(s)
            f_l = s['from']
            t_l = s['to']
            if f_l == t_l:
                if t_l == 'zh':
                    self.geturl = self.re_url.format('en')
                    try:
                        # jamtools.tra_to.setCurrentText('英语')
                        self.change_item_signal.emit("英语")
                    except:
                        print(sys.exc_info())
                else:
                    self.geturl = self.re_url.format('zh')
                    try:
                        self.change_item_signal.emit("中文")
                        # jamtools.tra_to.setCurrentText('中文')
                    except:
                        print(sys.exc_info())

                self.run()
                return
            for line in s['trans_result']:
                temp = line['dst'] + '\n'
                text += temp
            self.resultsignal.emit(text)


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
                # print(message.values())
                for res in message.get('words_result'):
                    text += res.get('words') + '\n'

            except:
                print("Unexpected error:", sys.exc_info())
                self.statusbar_signal.emit('识别出错！请确保网络畅通')
                text = str(sys.exc_info()[0])
            print(text)
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
        # print(self.args)

    def run(self):
        print('start_thread')
        if self.args:
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
    app = QApplication(sys.argv)
    w = Transparent_windows(20, 20, 500, 200)
    w.show()
    # w.setGeometry()
    sys.exit(app.exec_())
