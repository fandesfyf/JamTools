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

def gethtml(url, times=3):  # 下载一个链接
    try:
        response = requests.get(url, headers={"User-Agent": UserAgent().random}, timeout=8, verify=False)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text

    except requests.exceptions.RequestException:
        print(sys.exc_info(), '重试中')
        time.sleep(1)
        if times > 0:
            gethtml(url, times=times - 1)
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
    showm_signal = pyqtSignal(str)
    del_myself_signal = pyqtSignal(int)

    def __init__(self, parent=None, enter_tra=False, autoresetid=0):
        super().__init__(parent)
        self.parent = parent
        self.action = self.show
        self.moving = False
        self.autoreset = autoresetid
        self.hsp = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
                                "JamtoolsSimpleModehistory.txt")
        if os.path.exists(self.hsp):
            with open(self.hsp, "r", encoding="utf-8")as f:
                self.history = f.read().split("<\n\n<<>>\n\n>")
        else:
            self.history = []
        self.history_pos = len(self.history)
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
                           "QScrollBar{width:3px;border:none; background-color:rgb(200,200,200);"
                           "border-radius: 8px;}"
                           )
        self.label = linelabel(self)
        self.colse_botton = QPushButton('X', self)
        self.colse_botton.setToolTip('关闭')
        self.colse_botton.resize(25, 25)
        self.colse_botton.clicked.connect(self.hide)
        self.colse_botton.show()
        self.colse_botton.setStyleSheet(
            "QPushButton{color:white}"
            "QPushButton{background-color:rgb(239,0,0)}"
            "QPushButton:hover{color:green}"
            "QPushButton:hover{background-color:rgb(150,50,0)}"
            "QPushButton{border-radius:0};")
        self.tra_botton = QPushButton('译', self)
        self.tra_botton.resize(25, 25)
        self.tra_botton.clicked.connect(self.tra)
        self.tra_botton.setToolTip('翻译/快捷键Ctrl+回车')
        self.tra_botton.show()

        self.detail_botton = QPushButton('详', self)
        self.detail_botton.resize(25, 25)
        self.detail_botton.clicked.connect(self.detail)
        self.detail_botton.setToolTip('跳转百度翻译网页版查看详细解析')
        self.detail_botton.show()

        self.speak_botton = QPushButton('听', self)
        self.speak_botton.resize(25, 25)
        self.speak_botton.clicked.connect(self.speak)
        self.speak_botton.setToolTip('播放音频/快捷键F4')
        self.speak_botton.show()

        self.clear_botton = QPushButton(QIcon(":./clear.png"), "", self)
        self.clear_botton.resize(25, 25)
        self.clear_botton.clicked.connect(self.clear)
        self.clear_botton.setToolTip('清空')
        self.clear_botton.show()
        self.last_botton = QPushButton('<', self)
        self.last_botton.resize(13, 13)
        self.last_botton.clicked.connect(self.last_history)
        self.last_botton.setToolTip('上一个历史记录Ctrl+←')
        self.last_botton.show()
        self.next_botton = QPushButton('>', self)
        self.next_botton.resize(13, 13)
        self.next_botton.clicked.connect(self.next_history)
        self.next_botton.setToolTip('下一个历史记录Ctrl+→')
        self.next_botton.show()

        self.setToolTip('Ctrl+回车可快速翻译,拖动边框可改变位置')
        self.clear_signal.connect(self.clear)
        self.textAreaChanged()

        if enter_tra:
            self.action = self.tra

    def detail(self):
        text = self.toPlainText().split("翻译结果")[0].lstrip("\n").rstrip("\n")
        url = 'https://fanyi.baidu.com/#auto/zh/' + text
        QDesktopServices.openUrl(QUrl(url))

    def tra(self):
        self.showm_signal.emit("正在翻译..")
        text = self.toPlainText()
        if len(text) == 0:
            print("无文本")
            return
        text = re.sub(r'[^\w]', '', text).replace('_', '')
        print(text)
        n = 0
        for i in text:
            if self.is_alphabet(i):
                n += 1
        if n / len(text) > 0.4:
            print("is en")
            fr = "en"
            to = "zh"
        else:
            fr = "zh"
            to = "en"
        self.traThread = TrThread(self.toPlainText(), fr, to)
        self.traThread.resultsignal.connect(self.get_tra_resultsignal)
        self.traThread.start()

    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False

    def speak(self):
        text = self.toPlainText().split("翻译结果")[0].lstrip("\n").rstrip("\n")
        if text != "":
            s = Speaker()
            s.speak(text)

    def textAreaChanged(self, minsize=180, recheck=True):
        self.document.adjustSize()
        newWidth = self.document.size().width() + 28
        newHeight = self.document.size().height() + 15
        winwidth, winheight = QApplication.desktop().width(), QApplication.desktop().height()
        if newWidth != self.width():
            if newWidth < minsize:
                self.setFixedWidth(minsize)
            elif newWidth > winwidth * 3 // 7:
                self.setFixedWidth(winwidth * 3 // 7 + 28)
            else:
                self.setFixedWidth(newWidth)
            if self.x() + self.width() > winwidth:
                self.move(winwidth - 28 - self.width(), self.y())
        if newHeight != self.height():
            if newHeight < minsize:
                self.setFixedHeight(minsize)
            elif newHeight > winheight * 2 // 3:
                self.setFixedHeight(winheight * 2 // 3 + 15)
            else:
                self.setFixedHeight(newHeight)
            if self.y() + self.height() > winheight:
                self.move(self.x(), winheight - 28 - self.height())
        if recheck:
            self.textAreaChanged(recheck=False)
        self.adjustBotton()

    def adjustBotton(self):
        self.label.setGeometry(self.width() - 28, 0, 28, self.height())
        self.colse_botton.move(self.width() - 26, 1)
        self.tra_botton.move(self.width() - 26, self.height() - 26)
        self.speak_botton.move(self.tra_botton.x(), self.tra_botton.y() - self.speak_botton.height())
        self.detail_botton.move(self.speak_botton.x(), self.speak_botton.y() - self.detail_botton.height())
        self.clear_botton.move(self.detail_botton.x(), self.detail_botton.y() - self.clear_botton.height())
        self.last_botton.move(self.clear_botton.x(), self.clear_botton.y() - self.last_botton.height())
        self.next_botton.move(self.clear_botton.x() + self.clear_botton.width() - self.next_botton.width(),
                              self.clear_botton.y() - self.next_botton.height())

    def get_tra_resultsignal(self, text):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText("\n\n翻译结果:\n{}".format(text))
        self.addhistory()

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

    def wheelEvent(self, e) -> None:
        super(FramelessEnterSendQTextEdit, self).wheelEvent(e)
        angle = e.angleDelta() / 8
        angle = angle.y()
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if angle > 0 and self.windowOpacity() < 1:
                self.setWindowOpacity(self.windowOpacity() + 0.1 if angle > 0 else -0.1)
            elif angle < 0 and self.windowOpacity() > 0.2:
                self.setWindowOpacity(self.windowOpacity() - 0.1)

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
                    self.move(e.x() + self.x() - self.dx, e.y() + self.y() - self.dy)
            else:
                self.viewport().setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, e):
        super(FramelessEnterSendQTextEdit, self).keyPressEvent(e)
        # print(e.key())
        if e.key() == Qt.Key_Return:
            try:
                if QApplication.keyboardModifiers() in (Qt.ShiftModifier, Qt.ControlModifier, Qt.AltModifier):
                    self.action()
                else:
                    pass
            except:
                print('回车失败')
            return
        elif e.key() ==16777267:
            self.speak()
        elif e.key() == Qt.Key_S and QApplication.keyboardModifiers() == Qt.ControlModifier:
            print("save")
            self.addhistory()
        elif QApplication.keyboardModifiers() not in (Qt.ShiftModifier, Qt.ControlModifier, Qt.AltModifier):
            self.history_pos = len(self.history)
        elif QApplication.keyboardModifiers() == Qt.ControlModifier and e.key() == Qt.Key_Left:
            self.last_history()
        elif QApplication.keyboardModifiers() == Qt.ControlModifier and e.key() == Qt.Key_Right:
            self.next_history()


    def addhistory(self):
        text = self.toPlainText()
        if text not in self.history and len(text.replace(" ", "").replace("\n", "")):
            self.history.append(text)
            mode = "r+"
            if not os.path.exists(self.hsp):
                mode = "w+"
            with open(self.hsp, mode, encoding="utf-8")as f:
                hislist = f.read().split("<\n\n<<>>\n\n>")
                hislist.append(text)
                if len(hislist) > 20:
                    hislist = hislist[-20:]
                    self.history = self.history[-20:]
                newhis = "<\n\n<<>>\n\n>".join(hislist)
                f.seek(0)
                f.truncate()
                f.write(newhis)
            self.history_pos = len(self.history)

    def keyenter_connect(self, action):
        self.action = action

    def next_history(self):
        if self.history_pos < len(self.history) - 1:
            hp = self.history_pos
            self.clear()
            self.history_pos = hp + 1
            self.setText(self.history[self.history_pos])
        # print("next h", self.history_pos, len(self.history))

    def last_history(self):
        hp = self.history_pos
        self.addhistory()
        self.history_pos = hp
        if self.history_pos > 0:
            hp = self.history_pos
            self.clear()
            self.history_pos = hp - 1
            self.setText(self.history[self.history_pos])
        # print("last h", self.history_pos, len(self.history))

    def hide(self) -> None:
        self.addhistory()
        super(FramelessEnterSendQTextEdit, self).hide()
        if self.autoreset:
            print('删除', self.autoreset - 1)
            self.del_myself_signal.emit(self.autoreset - 1)
            self.close()

    def closeEvent(self, e) -> None:
        super(FramelessEnterSendQTextEdit, self).closeEvent(e)

    def clear(self, notsave=False):
        save = not notsave
        if save:
            self.addhistory()
        self.history_pos = len(self.history)
        super(FramelessEnterSendQTextEdit, self).clear()


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


class TrThread(QThread):
    resultsignal = pyqtSignal(str)
    showm_singal = pyqtSignal(str)
    change_item_signal = pyqtSignal(str)

    def __init__(self, text, from_lan, to_lan):
        super(QThread, self).__init__()
        self.text = text
        self.toLang = to_lan
        self.appid = QSettings('Fandes', 'jamtools').value('tran_appid', '20190928000337891', str)
        self.secretKey = QSettings('Fandes', 'jamtools').value('tran_secretKey', 'SiNITAufl_JCVpk7fAUS', str)
        salt = str(random.randint(32768, 65536))
        sign = self.appid + self.text + salt + self.secretKey
        m1 = hashlib.md5()
        m1.update(sign.encode(encoding='utf-8'))
        sign = m1.hexdigest()
        q= quote(self.text)
        self.re_url = '/api/trans/vip/translate?appid=' + self.appid + '&q=' + q + '&from=' + from_lan + '&to={0}&salt=' + str(
            salt) + '&sign=' + sign
        self.geturl = self.re_url.format(self.toLang)
        # self.args={"sign": sign,"salt":salt, "appid": self.appid,"to": to_lan,"from":from_lan ,"q":q}

    def run(self):

        if len(str(self.text).replace(" ", "").replace("\n", "")) == 0:
            print("空翻译")
            self.resultsignal.emit("没有文本!")
            return
        try:
            # res = requests.get("https://api.fanyi.baidu.com",headers=self.args)
            # print(res.text)
            httpClient0 = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient0.request('GET', self.geturl)
            response = httpClient0.getresponse()
            print("strat t")
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
    app = QApplication(sys.argv)
    w = Transparent_windows(20, 20, 500, 200)
    w.show()
    # w.setGeometry()
    sys.exit(app.exec_())
