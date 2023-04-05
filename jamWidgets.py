import os
import re
from PyQt5.QtCore import Qt, pyqtSignal, QStandardPaths, QUrl
from PyQt5.QtGui import QTextCursor, QDesktopServices
from PyQt5.QtGui import QPainter, QPen, QIcon, QFont,QImage
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit
from PyQt5.QtGui import QPainter, QColor, QLinearGradient,QMovie
from PyQt5.QtCore import Qt, QTimer,QSize
from PyQt5.QtWidgets import QApplication, QLabel, QWidget

from PyQt5.QtCore import Qt, pyqtSignal, QStandardPaths, QUrl,QTimer
from PyQt5.QtGui import QPainter, QPen, QIcon, QFont
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit, QFileDialog, QMenu
import numpy as np
import cv2
import jamresourse
from jampublic import linelabel,TipsShower,OcrimgThread
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
            if self.moving:
                self.move(e.x() + self.x() - self.dx, e.y() + self.y() - self.dy)
                self.viewport().update()
            if e.x() > self.width() - 25 or e.y() < 10 or e.y() > self.height() - 20:
                self.viewport().setCursor(Qt.SizeAllCursor)
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
class Hung_widget(QLabel):
    button_signal = pyqtSignal(str)
    def __init__(self,parent=None,funcs = []):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        size = 30
        self.buttonsize = size
        self.buttons = []
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0); border-radius: 6px;")  # 设置背景色和边框
        for i,func in enumerate(funcs):
            if str(func).endswith(("png","jpg")):
                botton = QPushButton(QIcon(func), '', self)
            else:
                botton = QPushButton(str(func), self)
            botton.clicked.connect(lambda checked, index=func: self.button_signal.emit(index))
            botton.setGeometry(0,i*size,size,size)
            botton.setStyleSheet("""QPushButton {
            border: 2px solid #8f8f91;
            background-color: qradialgradient(
                cx: -0.3, cy: 0.4,
                fx: -0.3, fy: 0.4,
                radius: 1.35,
                stop: 0 #fff,
                stop: 1 #888
            );
            color: white;
            font-size: 16px;
            padding: 6px;
        }

        QPushButton:hover {
            background-color: qradialgradient(
                cx: -0.3, cy: 0.4,
                fx: -0.3, fy: 0.4,
                radius: 1.35,
                stop: 0 #fff,
                stop: 1 #bbb
            );
        }""")
            self.buttons.append(botton)
        self.resize(size,size*len(funcs))

        
    def set_ontop(self,on_top=True):
        if on_top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.setWindowFlag(Qt.Tool, False)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.setWindowFlag(Qt.Tool, True)
    def clear(self):
        self.clearMask()
        self.hide()
        super().clear()

    def closeEvent(self, e):
        self.clear()
        super().closeEvent(e)
        
class Loading_label(QLabel):
    def __init__(self, parent=None,size = 100,text=None):
        super().__init__(parent)
        self.giflabel = QLabel(parent = self,text=text if text is not None else "")
        self.giflabel.resize(size, size)
        self.giflabel.setAlignment(Qt.AlignCenter)
        self.gif = QMovie(':./load.gif')
        self.gif.setScaledSize(QSize(size, size))
        self.giflabel.setMovie(self.gif)
    def resizeEvent(self, a0) -> None:
        
        size = min(self.width(),self.height())//3 
        if size < 50:
            size = min(self.width(),self.height())-5
            
        self.gif.setScaledSize(QSize(size, size))
        self.giflabel.resize(size, size)
        self.giflabel.move(self.width()//2-self.giflabel.width()//2,self.height()//2-self.giflabel.height()//2)
        return super().resizeEvent(a0)
    
    def start(self):
        self.gif.start()
        self.show()
    def stop(self):
        self.gif.stop()
        self.hide()
class Freezer(QLabel):
    def __init__(self, parent=None, img=None, x=0, y=0, listpot=0):
        super().__init__()
        self.hung_widget = Hung_widget(funcs =[":/exit.png",":/ontop.png",":/OCR.png",":/copy.png",":/saveicon.png"])
        self.tips_shower = TipsShower(" ",(QApplication.desktop().width()//2,50,120,50))
        self.tips_shower.hide()
        self.imgpix = img
        self.listpot = listpot
        self.setPixmap(self.imgpix)
        self.settingOpacity = False
        self.setWindowOpacity(0.95)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self.drawRect = True
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setGeometry(x, y, self.imgpix.width(), self.imgpix.height())
        self.show()
        self.drag = self.resize_the_window = False
        self.on_top = True
        self.p_x = self.p_y = 0
        self.setToolTip("Ctrl+滚轮可以调节透明度")
        # self.setMaximumSize(QApplication.desktop().size())
        self.timer = QTimer(self)  # 创建一个定时器
        self.timer.setInterval(200)  # 设置定时器的时间间隔为1秒
        self.timer.timeout.connect(self.check_mouse_leave)  # 定时器超时时触发check_mouse_leave函数
        
        self.hung_widget.button_signal.connect(self.hw_signalcallback)
        self.hung_widget.show()
        self.move(x, y)

        self.on_ocr = False
    def hw_signalcallback(self,s):
        print("callback",s)
        s = s.lower()
        self.tips_shower.set_pos(self.x(),self.y())
        if "exit" in s:#退出
            self.clear()
        elif "ocr" in s:#文字识别
            self.tips_shower.setText("文字识别中...",color=Qt.green)
            self.ocr()
        elif "ontop" in s:
            self.tips_shower.setText("{}置顶...".format("取消"if self.on_top else "设置"),color=Qt.green)
            self.change_ontop()
        elif "copy" in s:
            clipboard = QApplication.clipboard()
            try:
                clipboard.setPixmap(self.imgpix)
            except:
                self.tips_shower.setText("复制失败",color=Qt.green)
            else:
                self.tips_shower.setText("已复制图片",color=Qt.green)
        elif "save" in s:
            self.tips_shower.setText("图片另存为...",color=Qt.green)
            img = self.imgpix
            path, l = QFileDialog.getSaveFileName(self, "另存为", QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation), "png Files (*.png);;"
                                                  "jpg file(*.jpg);;jpeg file(*.JPEG);; bmp file(*.BMP );;ico file(*.ICO);;"
                                                  ";;all files(*.*)")
            if path:
                img.save(path)
    def ocr(self):
        self.on_ocr = True
        if not os.path.exists("j_temp"):
            os.mkdir("j_temp")
        self.pixmap().save("j_temp/tempocr.png", "PNG")
        cv_image = cv2.imread("j_temp/tempocr.png")
        self.ocrthread = OcrimgThread(cv_image)
        self.ocrthread.result_show_signal.connect(self.ocr_res_signalhandle)
        self.ocrthread.start()
        self.Loading_label = Loading_label(self)
        self.Loading_label.setGeometry(0, 0, self.width(), self.height())
        self.Loading_label.start()
        QApplication.processEvents()
    def ocr_res_signalhandle(self,result):
        pass
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        quitAction = menu.addAction("退出")
        copyaction = menu.addAction('复制')
        saveaction = menu.addAction('另存为')
        topaction = menu.addAction('(取消)置顶')
        rectaction = menu.addAction('(取消)边框')

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == quitAction:
            self.clear()
        elif action == saveaction:
            img = self.imgpix
            path, l = QFileDialog.getSaveFileName(self, "另存为", QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation), "png Files (*.png);;"
                                                  "jpg file(*.jpg);;jpeg file(*.JPEG);; bmp file(*.BMP );;ico file(*.ICO);;"
                                                  ";;all files(*.*)")
            if path:
                img.save(path)
        elif action == copyaction:
            clipboard = QApplication.clipboard()
            try:
                clipboard.setPixmap(self.imgpix)
            except:
                print('复制失败')
        elif action == topaction:
            self.change_ontop()
        elif action == rectaction:
            self.drawRect = not self.drawRect
            self.update()
            
    def change_ontop(self):
        if self.on_top:
            self.on_top = False
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.setWindowFlag(Qt.Tool, False)
            self.show()
        else:
            self.on_top = True
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.setWindowFlag(Qt.Tool, True)
            self.show()
    def setWindowOpacity(self,opacity):
        super().setWindowOpacity(opacity)
        self.hung_widget.setWindowOpacity(opacity)
        
    def wheelEvent(self, e):
        if self.isVisible():
            angleDelta = e.angleDelta() / 8
            dy = angleDelta.y()
            if self.settingOpacity:
                if dy > 0:
                    if (self.windowOpacity() + 0.1) <= 1:
                        self.setWindowOpacity(self.windowOpacity() + 0.1)
                    else:
                        self.setWindowOpacity(1)
                elif dy < 0 and (self.windowOpacity() - 0.1) >= 0.11:
                    self.setWindowOpacity(self.windowOpacity() - 0.1)
            else:
                if 2 * QApplication.desktop().width() >= self.width() >= 50:
                    # 获取鼠标所在位置相对于窗口的坐标
                    old_pos = e.pos()
                    old_width = self.width()
                    old_height = self.height()
                    w = self.width() + dy * 5
                    if w < 50: w = 50
                    if w > 2 * QApplication.desktop().width(): w = 2 * QApplication.desktop().width()
                    scale = self.imgpix.height() / self.imgpix.width()
                    h = w * scale
                    s = self.width() / w  # 缩放比例
                    self.setPixmap(self.imgpix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.resize( w, h)
                    delta_x = -(w - old_width)*old_pos.x()/old_width
                    delta_y = -(h - old_height)*old_pos.y()/old_height
                    self.move(self.x() + delta_x, self.y() + delta_y)
                    QApplication.processEvents()

            self.update()
    def move(self,x,y):
        super().move(x,y)
        hw_w = self.hung_widget.width()
        hw_h = self.hung_widget.height()
        hw_x = self.x()+self.width()
        hw_y = self.y()+self.height()-hw_h
        
        if self.x()+self.width() > QApplication.desktop().width() - hw_w:
            hw_x = self.x()-hw_w
        self.hung_widget.move(hw_x,hw_y)
        
    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if hasattr(self,"Loading_label"):
            self.Loading_label.setGeometry(0, 0, self.width(), self.height())
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.x() > self.width() - 20 and event.y() > self.height() - 20:
                self.resize_the_window = True
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.SizeAllCursor)
                self.drag = True
                self.p_x, self.p_y = event.x(), event.y()
            # self.resize(self.width()/2,self.height()/2)
            # self.setPixmap(self.pixmap().scaled(self.pixmap().width()/2,self.pixmap().height()/2))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ArrowCursor)
            self.drag = self.resize_the_window = False
    def underMouse(self) -> bool:
        return super().underMouse()
    def mouseMoveEvent(self, event):
        if self.isVisible():
            if self.drag:
                self.move(event.x() + self.x() - self.p_x, event.y() + self.y() - self.p_y)
            elif self.resize_the_window:
                if event.x() > 10 and event.y() > 10:
                    w = event.x()
                    scale = self.imgpix.height() / self.imgpix.width()
                    h = w * scale
                    self.resize(w, h)
                    self.setPixmap(self.imgpix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            elif event.x() > self.width() - 20 and event.y() > self.height() - 20:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    def enterEvent(self,e):
        super().enterEvent(e)
        self.timer.stop()
        self.hung_widget.show()
    def leaveEvent(self,e):
        super().leaveEvent(e)
        self.timer.start()
        self.settingOpacity = False
        
    def check_mouse_leave(self):
        if not self.underMouse() and not self.hung_widget.underMouse():
            self.hung_widget.hide()
            self.timer.stop()
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.clear()
        elif e.key() == Qt.Key_Control:
            self.settingOpacity = True

    def keyReleaseEvent(self, e) -> None:
        if e.key() == Qt.Key_Control:
            self.settingOpacity = False

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drawRect:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
            painter.end()

    def clear(self):
        self.clearMask()
        self.hide()
        del self.imgpix
        self.hung_widget.clear()
        super().clear()
        # jamtools.freeze_imgs[self.listpot] = None

    def closeEvent(self, e):
        self.clear()
        
        e.ignore()


