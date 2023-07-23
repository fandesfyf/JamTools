#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2020/11/8 19:29
# @Author  : Fandes
# @FileName: 滚动截屏3.0.py
# @Software: PyCharm
import math
import operator
import os
import random
import sys
import time
from functools import reduce
import numpy as np
import cv2
from PIL import Image
from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QStandardPaths, QTimer, QSettings, QFileInfo, \
    QSharedMemory, QPoint, QUrl, QMimeData, QRectF, QObject
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont, QImage, QTextCursor, QColor, QDesktopServices, QCursor, \
    QBrush, QPainterPath
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QToolTip, QAction, QTextEdit, QLineEdit, \
    QMessageBox, QFileDialog, QMenu, QSystemTrayIcon, QGroupBox, QComboBox, QCheckBox, QSpinBox, QTabWidget, \
    QDoubleSpinBox, QLCDNumber, QSlider, QScrollArea, QWidget, QToolBox, QRadioButton, QTimeEdit, QColorDialog, \
    QListWidget
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from pynput.mouse import Controller as MouseController
from pynput.mouse import Listener as  MouseListenner


class TipsShower(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFont(QFont('黑体', 15))
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)
        self.setText(text)
        self.show()

        self.setStyleSheet("color:white")

    def setText(self, text, autoclose=True) -> None:
        super(TipsShower, self).setText(text)
        self.adjustSize()
        self.show()
        if autoclose:
            self.timer.start(1000)

    def hide(self) -> None:
        super(TipsShower, self).hide()
        self.timer.stop()

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


class PicMatcher:
    def __init__(self, nfeatures=500, draw=False):
        self.SIFT = cv2.xfeatures2d_SIFT.create(nfeatures=nfeatures)
        self.bf = cv2.BFMatcher()
        self.draw = draw

    def match(self, im1, im2):
        # 提取特征并计算描述子
        kps1, des1 = self.SIFT.detectAndCompute(im1, None)
        kps2, des2 = self.SIFT.detectAndCompute(im2, None)
        # kps1, des1 = SURF.detectAndCompute(im1, None)
        # kps2, des2 = SURF.detectAndCompute(im2, None)

        # BFMatcher with default params
        matches = self.bf.knnMatch(des1, des2, k=2)
        good = []
        tempgoods = []
        distances = {}
        for m, n in matches:
            if m.distance == 0:
                pos0 = kps1[m.queryIdx].pt
                pos1 = kps2[m.trainIdx].pt
                if pos1[0] == pos0[0] and pos0[1] > pos1[1]:
                    d = int(pos0[1] - pos1[1])
                    if d in distances:
                        distances[d] += 1
                    else:
                        distances[d] = 0
                    # print(pos0, pos1)
                    tempgoods.append(m)
        sorteddistance = sorted(distances.items(), key=lambda kv: kv[1], reverse=True)
        max1y = 0
        max2y = 0
        try:
            distancesmode = sorteddistance[0][0]
            if sorteddistance[0][1] < 8:
                return 0, 0, 0
        except:
            print(sys.exc_info())
            return 0, 0, 0
        for match in tempgoods:
            pos0 = kps1[match.queryIdx].pt
            pos1 = kps2[match.trainIdx].pt
            if int(pos0[1] - pos1[1]) == distancesmode:
                if pos0[1] > max1y:
                    max1y = pos0[1]
                if pos1[1] > max2y:
                    max2y = pos1[1]
                good.append(match)
        print(len(good), distances, max1y, max2y)
        if self.draw:
            self.paint(im1, im2, kps1, kps2, good)
        return distancesmode, max1y, max2y

    def paint(self, im1, im2, kps1, kps2, good):
        img3 = cv2.drawMatches(im1, kps1, im2, kps2, good, None, flags=2)

        # 新建一个空图像用于绘制特征点
        img_sift1 = np.zeros(im1.shape, np.uint8)
        img_sift2 = np.zeros(im2.shape, np.uint8)

        # 绘制特征点
        cv2.drawKeypoints(im1, kps1, img_sift1)
        cv2.drawKeypoints(im2, kps2, img_sift2)
        # 展示
        # cv2.namedWindow("im1", cv2.WINDOW_NORMAL)
        # cv2.namedWindow("im2", cv2.WINDOW_NORMAL)
        # cv2.resizeWindow("im1", im2.shape[1], im2.shape[0])
        # cv2.resizeWindow("im2", im2.shape[1], im2.shape[0])
        # cv2.imshow("im1", img_sift1)
        # cv2.imshow("im2", img_sift2)
        cv2.imshow("match{}".format(random.randint(0, 8888)), img3)


class Transparent_windows(QLabel):
    def __init__(self, x=0, y=0, w=0, h=0, color=Qt.red, havelabel=False):
        super().__init__()
        self.setGeometry(x - 6, y - 6, w + 22, h + 22)
        self.x, self.y, self.w, self.h = x, y, w, h
        self.color = color
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        if havelabel:
            self.label = QLabel(self)
            self.label.setGeometry(self.w - 55, 6 + self.h + 1, 60, 14)
            self.label.setStyleSheet("color: green;border: 2 px;font-weight:bold;")

    def setGeometry(self, x=0, y=0, w=0, h=0) -> None:
        super().setGeometry(x - 6, y - 6, w + 22, h + 22)
        self.x, self.y, self.w, self.h = x, y, w, h

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setPen(QPen(self.color, 2, Qt.SolidLine))
        p.drawRect(6, 6, self.w, self.h)
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
        else:
            self.action()


class Splicing_shots(QObject):
    showm_signal = pyqtSignal(str)
    statusBar_signal = pyqtSignal(str)

    def __init__(self, parent: QLabel = None, nfeatures=500, draw=False):
        super(Splicing_shots, self).__init__()
        self.parent = parent
        self.picMatcher = PicMatcher(nfeatures=nfeatures, draw=draw)
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.setup)
        self.showrect = Transparent_windows()
        self.settings = QSettings('Fandes', 'jamtools')
        # self.init_splicing_shots_thread = Commen_Thread(self.init_splicing_shots)
        # self.init_splicing_shots_thread.start()
        self.init_splicing_shots()

    def init_splicing_shots(self):
        time.sleep(1)
        self.finalimg = None
        self.img_list = []
        self.roll_speed = self.settings.value('screenshot/roll_speed', 3, type=int)
        self.in_rolling = False
        if not os.path.exists(QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + '/JamPicture/screenshots'):
            os.mkdir(QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + '/JamPicture/screenshots')

    def setup(self):
        if self.clear_timer.isActive():
            self.clear_timer.stop()
            print('clear')
        time.sleep(1)
        self.finalimg = None
        self.img_list = []
        self.roll_speed = self.settings.value('screenshot/roll_speed', 3, type=int)
        self.in_rolling = False
        if not os.path.exists("j_temp"):
            os.mkdir("j_temp")

    def is_same(self, img1, img2):
        h1 = img1.histogram()
        h2 = img2.histogram()
        result = math.sqrt(reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, h1, h2))) / len(h1))
        if result <= 5:
            return True
        else:
            return False

    def match_and_merge(self):
        same = 0
        while not len(self.img_list):
            time.sleep(0.1)
        try:
            self.finalimg = self.img_list.pop(0)
            compare_img1 = cv2.cvtColor(self.finalimg, cv2.COLOR_RGB2GRAY)
        except:
            print("线程启动过早", sys.exc_info())
            return

        while self.in_rolling or len(self.img_list):
            if len(self.img_list):
                rgbimg2 = self.img_list.pop(0)
                compare_img2 = cv2.cvtColor(rgbimg2, cv2.COLOR_RGB2GRAY)
                distance, m1, m2 = self.picMatcher.match(compare_img1, compare_img2)
                # compare_img2 = self.offset(compare_img2, distance)
                if distance == 0:
                    print("重复!", same)
                    same += 1
                    if same >= 2:
                        break
                    continue
                else:
                    same = 0

                finalheightforcutting = self.finalimg.shape[0]
                imgheight = rgbimg2.shape[0]
                finalheightforcutting -= imgheight - int(m1)  # 拼接图片的裁剪高度
                i1 = self.finalimg[:finalheightforcutting, :, :]
                i2 = rgbimg2[int(m2):, :, :]
                self.finalimg = np.vstack((i1, i2))
                compare_img1 = compare_img2
                print("sucesmerge a img")
            else:
                # print("waiting for img")
                time.sleep(0.05)
        self.in_rolling = False
        print("end merge")
        cv2.imwrite("j_temp/final.png", self.finalimg)
        # cv2.imshow("finalimg", self.finalimg)
        # cv2.waitKey(0)

    def offset(self, img, offset):
        height, width = img.shape[:2]

        # 声明变换矩阵 向右平移10个像素， 向下平移30个像素
        M = np.float32([[1, 0, 0], [0, 1, offset]])
        # 进行2D 仿射变换
        shifted = cv2.warpAffine(img, M, (width, height + offset))
        return shifted

    def auto_roll(self, area):
        x, y, w, h = area
        self.tips.setText("单击停止")
        QApplication.processEvents()
        speed = round(1 / self.roll_speed, 2)
        screen = QApplication.primaryScreen()
        winid = QApplication.desktop().winId()

        def onclick(x, y, button, pressed):
            if pressed:
                print("click to stop")
                self.in_rolling = False
                listener.stop()

        controler = MouseController()
        listener = MouseListenner(on_click=onclick)
        self.match_thread = Commen_Thread(self.match_and_merge)
        self.in_rolling = True
        i = 0
        controler.position = (area[0] + int(area[2] / 2), area[1] + int(area[3] / 2))
        oldimg = Image.new("RGB", (128, 128), "#FF0f00")
        listener.start()
        while self.in_rolling:
            st = time.time()
            pix = screen.grabWindow(winid, x, y, w, h)
            newimg = Image.fromqpixmap(pix)
            img = cv2.cvtColor(np.asarray(newimg), cv2.COLOR_RGB2BGR)
            self.img_list.append(img)

            # cv2.imshow("FSd", img)
            # cv2.waitKey(0)
            if i >= 1:
                if i == 1:
                    self.match_thread.start()
                if self.is_same(oldimg, newimg):  # 每帧检查是否停止
                    self.in_rolling = False
                    i += 1
                    break
            oldimg = newimg
            controler.scroll(dx=0, dy=-3)
            time.sleep(speed)
            # cv2.imwrite('j_temp/{0}.png'.format(i), img)
            i += 1
        print("结束滚动,共截屏{}张".format(i))
        listener.stop()
        self.showrect.hide()
        self.match_thread.wait()
        self.showm_signal.emit("长截图完成")
    def inthearea(self,pos,area):
        if  area[0]<pos[0]<area[0]+area[2] and area[1]<pos[1]<area[1]+area[3]:
            return True
        else:
            return False
    def scroll_to_roll(self, area):
        x, y, w, h = area
        self.tips.setText("向下滚动,单击结束")
        QApplication.processEvents()
        screen = QApplication.primaryScreen()
        winid = QApplication.desktop().winId()
        self.id = self.rid = 0
        self.a_step = 0

        def onclick(x, y, button, pressed):
            if pressed:
                print("click to stop")
                self.in_rolling = False
                listener.stop()

        def on_scroll(px, py, x_axis, y_axis):
            print(px, py, x_axis, y_axis)
            # if not self.inthearea((px,py),area):
            #     return
            self.a_step += 1
            if self.a_step < 2:
                return
            else:
                self.a_step = 0
            if y_axis < 0:
                if self.rid >= self.id:
                    pix = screen.grabWindow(winid, x, y, w, h)
                    newimg = Image.fromqpixmap(pix)
                    img = cv2.cvtColor(np.asarray(newimg), cv2.COLOR_RGB2BGR)
                    self.img_list.append(img)
                    # cv2.imwrite("j_temp/{}.png".format(self.id), img)
                    self.id += 1
                    self.rid = self.id
                else:
                    print("跳过")
                    self.rid += 1
            else:
                self.rid -= 1
                print("方向错误")

        listener = MouseListenner(on_click=onclick, on_scroll=on_scroll)
        self.match_thread = Commen_Thread(self.match_and_merge)
        self.in_rolling = True
        i = 0
        listener.start()
        self.match_thread.start()
        while self.in_rolling:
            time.sleep(0.2)
        listener.stop()
        self.showrect.hide()
        self.match_thread.wait()

    def roll_manager(self, area):
        x, y, w, h = area
        self.mode = 1

        def on_click(x, y, button, pressed):
            print(x, y, button)
            if area[0] < x < area[0] + area[2] and area[1] < y < area[1] + area[3] and not pressed:
                self.mode = 1
                lis.stop()

        def on_scroll(x, y, button, pressed):
            self.mode = 0
            lis.stop()

        self.tips = TipsShower("单击自动滚动;\n或手动下滚;")
        if x < QApplication.desktop().width() - x - w:
            self.tips.move(x + w, y)
        else:
            self.tips.move(x - self.tips.width(), y)
        self.showrect.setGeometry(x, y, w, h)
        self.showrect.show()
        QApplication.processEvents()
        lis = MouseListenner(on_click=on_click, on_scroll=on_scroll)
        lis.start()
        print("等待用户开始")
        lis.join()
        lis.stop()
        if self.mode:
            print("auto_roll")
            self.auto_roll(area)
        else:
            print("scroll_to_roll")
            self.scroll_to_roll(area)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    s = Splicing_shots()
    # s.img_list = [cv2.imread("j_temp/{}.png".format(name)) for name in range(45, 51)]
    # s.match_and_merge()
    s.roll_manager((400, 60, 500, 600))
    # t = TipsShower("按下以开始")
    sys.exit(app.exec_())
