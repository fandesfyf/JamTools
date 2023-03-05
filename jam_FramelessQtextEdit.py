import os
import sys
import re
from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QSettings, QSizeF, QStandardPaths, QUrl
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QBrush, QTextDocument, QTextCursor, QDesktopServices
from PyQt5.QtGui import QPainter, QPen, QIcon, QFont
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit, QWidget

from jampublic import linelabel
from jam_transtalater import Translator
from jamspeak import Speaker

class FramelessEnterSendQTextEdit(QTextEdit):  # 小窗,翻译,文字识别,语音
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
        self.activateWindow()
        self.setFocus()

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
            fr = "英语"
            to = "中文"
        else:
            fr = "中文"
            to = "英语"
        self.translator = Translator()
        self.translator.result_signal.connect(self.get_tra_resultsignal)
        self.translator.translate(self.toPlainText(), fr, to)

    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False

    def speak(self):
        text = self.toPlainText().split("翻译结果")[0].lstrip("\n").rstrip("\n")
        if text != "":
            Speaker().speak(text)

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

    def get_tra_resultsignal(self, text,fr,to):
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
