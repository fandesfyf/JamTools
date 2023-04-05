import os
import re
from PyQt5.QtCore import Qt, pyqtSignal, QStandardPaths, QUrl
from PyQt5.QtGui import QTextCursor, QDesktopServices
from PyQt5.QtGui import QPainter, QPen, QIcon, QFont,QImage,QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit
from PyQt5.QtGui import QPainter, QColor, QLinearGradient,QMovie,QPolygon
from PyQt5.QtCore import Qt, QTimer,QSize,QPoint
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
        self.setGeometry(QApplication.desktop().width()//2,QApplication.desktop().height()//2,100,100)
        self.menu_size = 28
        self.label = linelabel()
        self.label.setGeometry(self.x() + self.width(),self.y(), 28, self.height())
        self.label.move_signal.connect(self.move_signal_callback)
        self.colse_botton = QPushButton('X', self.label)
        self.colse_botton.setToolTip('关闭')
        self.colse_botton.resize(self.menu_size, self.menu_size)
        self.colse_botton.clicked.connect(self.hide)
        self.colse_botton.show()
        self.colse_botton.setStyleSheet(
            "QPushButton{color:white}"
            "QPushButton{background-color:rgb(239,0,0)}"
            "QPushButton:hover{color:green}"
            "QPushButton:hover{background-color:rgb(150,50,0)}"
            "QPushButton{border-radius:0};")
        self.tra_botton = QPushButton(QIcon(":./tra.png"),'', self.label)
        self.tra_botton.resize(self.menu_size, self.menu_size)
        self.tra_botton.clicked.connect(self.tra)
        self.tra_botton.setToolTip('翻译/快捷键Ctrl+回车')
        self.tra_botton.show()

        self.copy_botton = QPushButton(QIcon(":./copy.png"),'', self.label)
        self.copy_botton.resize(self.menu_size, self.menu_size)
        self.copy_botton.clicked.connect(self.copy_text)
        self.copy_botton.setToolTip('复制内容到剪切板')
        self.copy_botton.show()
        
        self.detail_botton = QPushButton('详', self.label)
        self.detail_botton.resize(self.menu_size, self.menu_size)
        self.detail_botton.clicked.connect(self.detail)
        self.detail_botton.setToolTip('跳转百度翻译网页版查看详细解析')
        self.detail_botton.show()

        self.speak_botton = QPushButton('听', self.label)
        self.speak_botton.resize(self.menu_size, self.menu_size)
        self.speak_botton.clicked.connect(self.speak)
        self.speak_botton.setToolTip('播放音频/快捷键F4')
        self.speak_botton.show()

        self.clear_botton = QPushButton(QIcon(":./clear.png"), "", self.label)
        self.clear_botton.resize(self.menu_size, self.menu_size)
        self.clear_botton.clicked.connect(self.clear)
        self.clear_botton.setToolTip('清空')
        self.clear_botton.show()
        self.last_botton = QPushButton('<', self.label)
        self.last_botton.resize(self.menu_size//2, self.menu_size//2)
        self.last_botton.clicked.connect(self.last_history)
        self.last_botton.setToolTip('上一个历史记录Ctrl+←')
        self.last_botton.show()
        self.next_botton = QPushButton('>', self.label)
        self.next_botton.resize(self.menu_size//2, self.menu_size//2)
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
    def move(self,x,y,active=False):
        super().move(x,y)
        self.label.move(self.x()+self.width(), self.y())
    def move_signal_callback(self,x,y):
        if self.x() != x-self.width() or self.y() != y:
            self.move(x-self.width(),y)
    def copy_text(self):
        text = self.toPlainText().lstrip("\n").rstrip("\n")
        if len(text):
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

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

    def textAreaChanged(self, minsize=200, recheck=True,border=30):
        self.document.adjustSize()
        newWidth = self.document.size().width() + border
        newHeight = self.document.size().height() + border//2
        winwidth, winheight = QApplication.desktop().width(), QApplication.desktop().height()
        if newWidth != self.width():
            if newWidth < minsize:
                self.setFixedWidth(minsize)
            elif newWidth > winwidth // 2:
                self.setFixedWidth(winwidth // 2 + border)
            else:
                self.setFixedWidth(newWidth)
            if self.x() + self.width() > winwidth:
                self.move(winwidth - border - self.width(), self.y())
        if newHeight != self.height():
            if newHeight < minsize:
                self.setFixedHeight(minsize)
            elif newHeight > winheight * 2 // 3:
                self.setFixedHeight(winheight * 2 // 3 + 15)
            else:
                self.setFixedHeight(newHeight)
            if self.y() + self.height() > winheight:
                self.move(self.x(), winheight - border - self.height())
        if recheck:
            self.textAreaChanged(recheck=False)
            self.textAreaChanged(recheck=False)
        self.adjustBotton()

    def adjustBotton(self):
        self.label.setGeometry(self.x()+self.width(), self.y(), 28, self.height())
        self.colse_botton.move(0, 1)
        self.tra_botton.move(0, self.height() - self.tra_botton.height())
        self.speak_botton.move(self.tra_botton.x(), self.tra_botton.y() - self.speak_botton.height())
        self.detail_botton.move(self.speak_botton.x(), self.speak_botton.y() - self.detail_botton.height())
        self.clear_botton.move(self.detail_botton.x(), self.detail_botton.y() - self.clear_botton.height())
        self.copy_botton.move(self.clear_botton.x(), self.clear_botton.y() - self.copy_botton.height())
        self.last_botton.move(self.copy_botton.x(), self.copy_botton.y() - self.last_botton.height())
        self.next_botton.move(self.copy_botton.x() + self.copy_botton.width() - self.next_botton.width(),
                              self.copy_botton.y() - self.next_botton.height())

    def get_tra_resultsignal(self, text,fr,to):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText("\n\n翻译结果:\n{}".format(text))
        self.addhistory()

    def insertPlainText(self, text):
        super(FramelessEnterSendQTextEdit, self).insertPlainText(text)
        self.show()

    

    def wheelEvent(self, e) -> None:
        super(FramelessEnterSendQTextEdit, self).wheelEvent(e)
        angle = e.angleDelta() / 8
        angle = angle.y()
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if angle > 0 and self.windowOpacity() < 1:
                self.setWindowOpacity(self.windowOpacity() + 0.1 if angle > 0 else -0.1)
            elif angle < 0 and self.windowOpacity() > 0.2:
                self.setWindowOpacity(self.windowOpacity() - 0.1)

    
            

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
    def showEvent(self,e):
        super().showEvent(e)
        self.label.show()
    def hide(self) -> None:
        self.addhistory()
        super(FramelessEnterSendQTextEdit, self).hide()
        self.label.hide()
        if self.autoreset:
            print('删除', self.autoreset - 1)
            self.del_myself_signal.emit(self.autoreset - 1)
            self.label.close()
            self.close()

    def closeEvent(self, e) -> None:
        super(FramelessEnterSendQTextEdit, self).closeEvent(e)
        self.label.close()
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
        self.text_shower = FramelessEnterSendQTextEdit(self, enter_tra=True)
        self.text_shower.hide()
        self.origin_imgpix = img
        self.showing_imgpix = self.origin_imgpix
        self.ocr_res_imgpix = None
        self.listpot = listpot
        self.setPixmap(self.showing_imgpix)
        self.settingOpacity = False
        self.setWindowOpacity(0.95)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self.drawRect = True
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setGeometry(x, y, self.showing_imgpix.width(), self.showing_imgpix.height())
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
        self.ocr_status = "waiting"
        self.ocr_res_info = []
        
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
                clipboard.setPixmap(self.showing_imgpix)
            except:
                self.tips_shower.setText("复制失败",color=Qt.green)
            else:
                self.tips_shower.setText("已复制图片",color=Qt.green)
        elif "save" in s:
            self.tips_shower.setText("图片另存为...",color=Qt.green)
            img = self.showing_imgpix
            path, l = QFileDialog.getSaveFileName(self, "另存为", QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation), "png Files (*.png);;"
                                                  "jpg file(*.jpg);;jpeg file(*.JPEG);; bmp file(*.BMP );;ico file(*.ICO);;"
                                                  ";;all files(*.*)")
            if path:
                img.save(path)
    def ocr(self):
        if self.ocr_status == "ocr":
            self.tips_shower.setText("取消识别...",color=Qt.green)
            self.ocr_status = "abort"
            self.Loading_label.stop()
            self.text_shower.hide()
            self.showing_imgpix = self.origin_imgpix
            self.setPixmap(self.showing_imgpix.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            return
        elif self.ocr_status == "show":#正在展示结果,取消展示
            self.tips_shower.setText("退出文字识别...",color=Qt.green)
            self.ocr_status = "waiting"
            self.Loading_label.stop()
            self.text_shower.hide()
            self.showing_imgpix = self.origin_imgpix
            self.setPixmap(self.showing_imgpix.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            return
        self.ocr_status = "ocr"
        if not os.path.exists("j_temp"):
            os.mkdir("j_temp")
        self.pixmap().save("j_temp/tempocr.png", "PNG")
        cv_image = cv2.imread("j_temp/tempocr.png")
        self.ocrthread = OcrimgThread(cv_image)
        self.ocrthread.result_show_signal.connect(self.ocr_res_signalhandle)
        self.ocrthread.boxes_info_signal.connect(self.orc_boxes_info_callback)
        self.ocrthread.det_res_img.connect(self.det_res_img_callback)
        self.ocrthread.start()
        self.Loading_label = Loading_label(self)
        self.Loading_label.setGeometry(0, 0, self.width(), self.height())
        self.Loading_label.start()
        
        self.text_shower.setPlaceholderText("正在识别,请耐心等待...")
        self.text_shower.move(self.x(), self.y()+self.height())
        self.text_shower.show()
        self.text_shower.clear()
        QApplication.processEvents()
    def orc_boxes_info_callback(self,text_boxes):
        if self.ocr_status == "ocr":
            for tb in text_boxes:
                tb["select"]=False
            self.ocr_res_info = text_boxes
            print("rec orc_boxes_info_callback")

    def det_res_img_callback(self,piximg):
        if self.ocr_status == "ocr":
            print("rec det_res_img_callback")
            self.showing_imgpix = piximg
            self.ocr_res_imgpix = piximg
            self.setPixmap(piximg.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
    def ocr_res_signalhandle(self,text):
        if self.ocr_status == "ocr":
            self.text_shower.setPlaceholderText("")
            self.text_shower.insertPlainText(text)
            self.Loading_label.stop()
            self.ocr_status = "show"
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
            img = self.showing_imgpix
            path, l = QFileDialog.getSaveFileName(self, "另存为", QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation), "png Files (*.png);;"
                                                  "jpg file(*.jpg);;jpeg file(*.JPEG);; bmp file(*.BMP );;ico file(*.ICO);;"
                                                  ";;all files(*.*)")
            if path:
                img.save(path)
        elif action == copyaction:
            clipboard = QApplication.clipboard()
            try:
                clipboard.setPixmap(self.showing_imgpix)
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
                    scale = self.showing_imgpix.height() / self.showing_imgpix.width()
                    h = w * scale
                    s = self.width() / w  # 缩放比例
                    self.setPixmap(self.showing_imgpix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
        self.text_shower.move(self.x(), self.y()+self.height())#主动移动
        
    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if hasattr(self,"Loading_label"):
            self.Loading_label.setGeometry(0, 0, self.width(), self.height())
    def draw_ocr_select_result(self,ids = []):
        qpixmap = self.ocr_res_imgpix.copy()
        painter = QPainter(qpixmap)
        
        for i,text_box in enumerate(self.ocr_res_info):
            if i in ids:
                pen = QPen(Qt.green)
            else:
                pen = QPen(Qt.red)
            pen.setWidth(2) 
            painter.setPen(pen)
            contour = text_box["box"]
            points = []
            for point in contour:
                x, y = point
                points.append(QPoint(x, y))
            polygon = QPolygon(points + [points[0]])
            painter.drawPolyline(polygon)
        painter.end()
        return qpixmap
    def check_select_ocr_box(self,x,y):
        select_ids = []
        change = False
        for i,text_box in enumerate(self.ocr_res_info):
            contour = text_box["box"]
            dist = cv2.pointPolygonTest(contour, (x,y), False)
            if dist >= 0:
                text_box["select"] = ~text_box["select"]
                change = True
            if text_box["select"]:
                select_ids.append(i)
            
        return select_ids,change
    def update_ocr_text(self,ids):
        match_text_box = []
        for i,text_box in enumerate(self.ocr_res_info):
            if i in ids:
                match_text_box.append(text_box)
        if hasattr(self,"ocrthread"):
            res = self.ocrthread.get_match_text(match_text_box)
            if res is not None:
                return res
        return None
    def update_ocr_select_result(self,x,y):
        select_ids,changed = self.check_select_ocr_box(x,y)
        if changed:
            pix = self.draw_ocr_select_result(ids = select_ids)
            self.showing_imgpix = pix
            self.setPixmap(pix.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            update_res = self.update_ocr_text(select_ids)
            if update_res is not None:
                # 更新结果
                self.text_shower.move(self.x(), self.y()+self.height())
                self.text_shower.show()
                self.text_shower.clear()
                self.text_shower.insertPlainText(update_res)
        return changed
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.ocr_status=="show":
                sx,sy = self.origin_imgpix.width()/self.width(),self.origin_imgpix.height()/self.height()
                realx,realy = event.x()*sx,event.y()*sy
                changed = self.update_ocr_select_result(realx,realy)
                if changed:
                    return
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
                    scale = self.showing_imgpix.height() / self.showing_imgpix.width()
                    h = w * scale
                    self.resize(w, h)
                    self.setPixmap(self.showing_imgpix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
        if hasattr(self,"Loading_label"):
            self.Loading_label.stop()
        self.text_shower.clear()
        self.text_shower.hide()
        del self.showing_imgpix
        self.hung_widget.clear()
        super().clear()
        # jamtools.freeze_imgs[self.listpot] = None

    def closeEvent(self, e):
        self.clear()
        
        e.ignore()


