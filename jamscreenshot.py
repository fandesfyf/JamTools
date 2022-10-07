import gc
import math
import os
import re
import sys
import time

import cv2
from numpy import array, zeros, uint8, float32
from PyQt5.QtCore import QPoint, QRectF, QMimeData
from PyQt5.QtCore import QRect, Qt, pyqtSignal, QStandardPaths, QTimer, QSettings, QUrl
from PyQt5.QtGui import QCursor, QBrush, QScreen
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont, QImage, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit, QFileDialog, QMenu, QGroupBox, QSpinBox, \
    QWidget
from PyQt5.QtWidgets import QSlider, QColorDialog

from jampublic import FramelessEnterSendQTextEdit, OcrimgThread, Commen_Thread, TipsShower, PLATFORM_SYS,CONFIG_DICT
from jamroll_screenshot import Splicing_shots
import jamresourse
from pynput.mouse import Controller


def cut_polypng(img, pointlist):  # 多边形裁剪
    xlist = [i[0] for i in pointlist]
    ylist = [i[1] for i in pointlist]
    w = max(xlist) - min(xlist)
    h = max(ylist) - min(ylist)
    x0, y0 = min(xlist), min(ylist)
    for i, lis in enumerate(pointlist):
        pointlist[i] = [lis[0] - x0, lis[1] - y0]
    img = img[y0:y0 + h, x0:x0 + w]
    pts = array(pointlist)
    pts = array([pts])
    # 和原始图像一样大小的0矩阵，作为mask
    mask = zeros(img.shape[:2], uint8)
    # 在mask上将多边形区域填充为白色
    cv2.polylines(mask, pts, 1, 255)  # 描绘边缘
    cv2.fillPoly(mask, pts, 255)  # 填充
    # 逐位与，得到裁剪后图像，此时是黑色背景
    dstimg = cv2.bitwise_and(img, img, mask=mask)
    return dstimg


def cut_mutipic(img, pointlist):  # 透视裁剪
    xlist = [i[0] for i in pointlist]
    ylist = [i[1] for i in pointlist]
    w = max(xlist) - min(xlist)
    h = max(ylist) - min(ylist)
    bl = w / abs(pointlist[0][0] - pointlist[1][0])
    x0, y0 = min(xlist), min(ylist)
    for i, lis in enumerate(pointlist):
        pointlist[i] = [lis[0] - x0, lis[1] - y0]
    img = img[y0:y0 + h, x0:x0 + w]
    pts = array(pointlist)
    pts = array([pts])
    # 和原始图像一样大小的0矩阵，作为mask
    mask = zeros(img.shape[:2], uint8)
    # 在mask上将多边形区域填充为白色
    cv2.polylines(mask, pts, 1, 255)  # 描绘边缘
    cv2.fillPoly(mask, pts, 255)  # 填充
    # 逐位与，得到裁剪后图像，此时是黑色背景
    dstimg = cv2.bitwise_and(img, img, mask=mask)
    # cv2.imshow("dst", dst)
    tw = max(math.sqrt((pointlist[0][1] - pointlist[3][1]) ** 2 + (pointlist[0][0] - pointlist[3][0]) ** 2),
             math.sqrt((pointlist[1][1] - pointlist[2][1]) ** 2 + (pointlist[1][0] - pointlist[2][0]) ** 2))
    th = max(math.sqrt((pointlist[0][1] - pointlist[3][1]) ** 2 + (pointlist[0][0] - pointlist[3][0]) ** 2),
             math.sqrt((pointlist[2][1] - pointlist[1][1]) ** 2 + (pointlist[2][0] - pointlist[1][0]) ** 2),
             h)
    # if bl>1:
    #     th=th*bl
    tw, th = int(tw), int(th)
    org = array(pointlist, float32)
    dst = array([[0, 0],
                 [tw, 0],
                 [tw, th],
                 [0, th]], float32)
    warpR = cv2.getPerspectiveTransform(org, dst)
    result = cv2.warpPerspective(dstimg, warpR, (tw, th), borderMode=cv2.BORDER_TRANSPARENT)
    # cv2.namedWindow("result",0)
    # cv2.imshow("result", result)
    # cv2.waitKey(0)
    return result


def get_opposite_color(color: QColor):
    return QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())


def image_fill(image, x, y, color: tuple = (0, 0, 255), d=0):  # 泛洪填充
    src = image.copy()  # 先创建一个副本
    cv2.floodFill(src, None, (x, y), color, (d, d, d), (d, d, d), cv2.FLOODFILL_FIXED_RANGE)
    # cv2.circle(src, (x, y), 2, color=(0, 255, 0), thickness=4)
    # cv2.imshow('flood_fill', src)
    return src


def get_line_interpolation(p1, p2):  # 线性插值
    res = []
    dy = p1[1] - p2[1]
    dx = p1[0] - p2[0]
    n = max(abs(dy), abs(dx))
    nx = dx / n
    ny = dy / n
    for i in range(n):
        res.append([p2[0] + i * nx, p2[1] + i * ny])
    return res


class ColorButton(QPushButton):
    select_color_signal = pyqtSignal(str)

    def __init__(self, color, parent):
        super(ColorButton, self).__init__("", parent)
        self.color = QColor(color).name()
        self.setStyleSheet("background-color:{}".format(self.color))
        self.clicked.connect(self.sendcolor)

    def sendcolor(self):
        self.select_color_signal.emit(self.color)


class HoverButton(QPushButton):
    hoversignal = pyqtSignal(int)

    def enterEvent(self, e) -> None:
        super(HoverButton, self).enterEvent(e)
        self.hoversignal.emit(1)
        print("enter")

    def leaveEvent(self, e):
        super(HoverButton, self).leaveEvent(e)
        # time.sleep(2)
        self.hoversignal.emit(0)
        print("leave")


class HoverGroupbox(QGroupBox):
    hoversignal = pyqtSignal(int)

    def enterEvent(self, e) -> None:
        super(HoverGroupbox, self).enterEvent(e)
        self.hoversignal.emit(1)
        print("enter")

    def leaveEvent(self, e):
        super(HoverGroupbox, self).leaveEvent(e)
        # time.sleep(2)
        self.hoversignal.emit(0)
        print("leave")


class CanMoveGroupbox(QGroupBox):  # 移动groupbox
    def __init__(self, parent):
        super(CanMoveGroupbox, self).__init__(parent)
        self.drag = False
        self.p_x, self.p_y = 0, 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.x() < 100:
            self.setCursor(Qt.SizeAllCursor)
            self.drag = True
            self.p_x, self.p_y = event.x(), event.y()
        # super(CanMoveGroupbox, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ArrowCursor)
            self.drag = False
        # super(CanMoveGroupbox, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.isVisible():
            if self.drag:
                self.move(event.x() + self.x() - self.p_x, event.y() + self.y() - self.p_y)

        # super(CanMoveGroupbox, self).mouseMoveEvent(event)


class Finder():  # 选择智能选区
    def __init__(self, parent):
        self.h = self.w = 0
        self.rect_list = self.contours = []
        self.area_threshold = 200
        self.parent = parent
        self.img = None

    def find_contours_setup(self):

        try:
            self.area_threshold = self.parent.parent.ss_areathreshold.value()
        except:
            self.area_threshold = 200
        # t1 = time.process_time()
        # self.img = cv2.imread('j_temp/get.png')
        # t2 = time.process_time()
        self.h, self.w, _ = self.img.shape

        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)  # 灰度化
        # t3 = time.process_time()
        # ret, th = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 2)  # 自动阈值
        # th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_TRUNC, 11, 2)  # 自动阈值
        # t4 = time.process_time()
        self.contours = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]
        self.find_contours()
        # print('setuptime', t2 - t1, t3 - t2, t4 - t3)

    def find_contours(self):
        draw_img = cv2.drawContours(self.img.copy(), self.contours, -1, (0, 255, 0), 1)
        # cv2.imshow("tt", draw_img)
        # cv2.imwrite("test.png", self.img.copy())
        # cv2.waitKey(0)
        # newcontours = []
        self.rect_list = [[0, 0, self.w, self.h]]
        for i in self.contours:
            x, y, w, h = cv2.boundingRect(i)
            area = cv2.contourArea(i)
            if area > self.area_threshold and w > 10 and h > 10:
                # cv2.rectangle(self.img, (x, y), (x + w, y + h), (0, 0, 255), 1)
                # newcontours.append(i)
                self.rect_list.append([x, y, x + w, y + h])
        print('contours:', len(self.contours), 'left', len(self.rect_list))

    def find_targetrect(self, point):
        # print(len(self.rect_list))
        # point = (1000, 600)
        target_rect = [0, 0, self.w, self.h]
        target_area = 1920 * 1080
        for rect in self.rect_list:
            if point[0] in range(rect[0], rect[2]):
                # print('xin',rect)
                if point[1] in range(rect[1], rect[3]):
                    # print('yin', rect)
                    area = (rect[3] - rect[1]) * (rect[2] - rect[0])
                    # print(area,target_area)
                    if area < target_area:
                        target_rect = rect
                        target_area = area
                        # print('target', target_area, target_rect)
                        # x,y,w,h=target_rect[0],target_rect[1],target_rect[2]-target_rect[0],target_rect[3]-target_rect[1]
                        # cv2.rectangle(self.img, (x, y), (x + w, y + h), (0, 0, 255), 1)
        # cv2.imwrite("img.png", self.img)
        return target_rect

    def clear_setup(self):
        self.h = self.w = 0
        self.rect_list = self.contours = []
        self.img = None


class MaskLayer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.parent.on_init:
            print('oninit return')
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.parent.painter_tools["perspective_cut_on"]:  # 透视裁剪工具
            # painter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
            color = get_opposite_color(self.parent.pencolor)
            for i in range(len(self.parent.perspective_cut_pointlist)):
                painter.setPen(QPen(color, 10, Qt.SolidLine))
                painter.drawPoint(
                    QPoint(self.parent.perspective_cut_pointlist[i][0], self.parent.perspective_cut_pointlist[i][1]))
                painter.setPen(QPen(color, 3, Qt.SolidLine))
                if i < len(self.parent.perspective_cut_pointlist) - 1:
                    painter.drawLine(self.parent.perspective_cut_pointlist[i][0],
                                     self.parent.perspective_cut_pointlist[i][1],
                                     self.parent.perspective_cut_pointlist[i + 1][0],
                                     self.parent.perspective_cut_pointlist[i + 1][1])
                else:
                    painter.drawLine(self.parent.perspective_cut_pointlist[i][0],
                                     self.parent.perspective_cut_pointlist[i][1],
                                     self.parent.mouse_posx, self.parent.mouse_posy)
                    painter.drawLine(self.parent.perspective_cut_pointlist[0][0],
                                     self.parent.perspective_cut_pointlist[0][1],
                                     self.parent.mouse_posx, self.parent.mouse_posy)
            # 画网格
            painter.setPen(QPen(QColor(120, 180, 120, 180), 1, Qt.SolidLine))
            if len(self.parent.perspective_cut_pointlist) >= 2:
                p0 = self.parent.perspective_cut_pointlist[0]
                p1 = self.parent.perspective_cut_pointlist[1]
                pp1 = pp0 = (self.parent.mouse_posx, self.parent.mouse_posy)
                if len(self.parent.perspective_cut_pointlist) > 2:
                    pp1 = self.parent.perspective_cut_pointlist[2]
                dx1 = pp1[0] - p1[0]
                dy1 = pp1[1] - p1[1]
                dx0 = pp0[0] - p0[0]
                dy0 = pp0[1] - p0[1]
                maxs = max(math.sqrt(dy0 ** 2 + dx0 ** 2), math.sqrt(dy1 ** 2 + dx1 ** 2))
                if maxs > 25:
                    n = maxs // 25
                    ddx0 = dx0 / (n + 1)
                    ddy0 = dy0 / (n + 1)
                    ddx1 = dx1 / (n + 1)
                    ddy1 = dy1 / (n + 1)
                    for i in range(int(n) + 1):
                        painter.drawLine(pp0[0] - i * ddx0, pp0[1] - i * ddy0, pp1[0] - i * ddx1, pp1[1] - i * ddy1)
            if len(self.parent.perspective_cut_pointlist) >= 3:
                p0 = self.parent.perspective_cut_pointlist[1]
                p1 = self.parent.perspective_cut_pointlist[2]
                pp1 = (self.parent.mouse_posx, self.parent.mouse_posy)
                pp0 = self.parent.perspective_cut_pointlist[0]

                dx1 = pp1[0] - p1[0]
                dy1 = pp1[1] - p1[1]
                dx0 = pp0[0] - p0[0]
                dy0 = pp0[1] - p0[1]
                maxs = max(math.sqrt(dy0 ** 2 + dx0 ** 2), math.sqrt(dy1 ** 2 + dx1 ** 2))
                if maxs > 25:
                    n = maxs // 25
                    ddx0 = dx0 / (n + 1)
                    ddy0 = dy0 / (n + 1)
                    ddx1 = dx1 / (n + 1)
                    ddy1 = dy1 / (n + 1)
                    for i in range(int(n) + 1):
                        painter.drawLine(pp0[0] - i * ddx0, pp0[1] - i * ddy0, pp1[0] - i * ddx1, pp1[1] - i * ddy1)

        elif self.parent.painter_tools["polygon_ss_on"]:  # 多边形截图
            color = get_opposite_color(self.parent.pencolor)
            for i in range(len(self.parent.polygon_ss_pointlist)):
                painter.setPen(QPen(color, 3, Qt.SolidLine))
                if i < len(self.parent.polygon_ss_pointlist) - 1:
                    painter.drawLine(self.parent.polygon_ss_pointlist[i][0],
                                     self.parent.polygon_ss_pointlist[i][1],
                                     self.parent.polygon_ss_pointlist[i + 1][0],
                                     self.parent.polygon_ss_pointlist[i + 1][1])
                else:

                    painter.drawLine(self.parent.polygon_ss_pointlist[i][0],
                                     self.parent.polygon_ss_pointlist[i][1],
                                     self.parent.mouse_posx, self.parent.mouse_posy)
                    painter.setPen(QPen(QColor(200, 200, 200, 222), 2, Qt.DashDotLine))
                    painter.drawLine(self.parent.polygon_ss_pointlist[0][0],
                                     self.parent.polygon_ss_pointlist[0][1],
                                     self.parent.mouse_posx, self.parent.mouse_posy)

        elif not (self.parent.painter_tools['selectcolor_on'] or self.parent.painter_tools['bucketpainter_on']):
            # 正常显示选区
            rect = QRect(min(self.parent.x0, self.parent.x1), min(self.parent.y0, self.parent.y1),
                         abs(self.parent.x1 - self.parent.x0), abs(self.parent.y1 - self.parent.y0))

            painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
            painter.drawRect(rect)
            painter.drawRect(0, 0, self.width(), self.height())
            painter.setPen(QPen(QColor(0, 150, 0), 8, Qt.SolidLine))
            painter.drawPoint(
                QPoint(self.parent.x0, min(self.parent.y1, self.parent.y0) + abs(self.parent.y1 - self.parent.y0) // 2))
            painter.drawPoint(
                QPoint(min(self.parent.x1, self.parent.x0) + abs(self.parent.x1 - self.parent.x0) // 2, self.parent.y0))
            painter.drawPoint(
                QPoint(self.parent.x1, min(self.parent.y1, self.parent.y0) + abs(self.parent.y1 - self.parent.y0) // 2))
            painter.drawPoint(
                QPoint(min(self.parent.x1, self.parent.x0) + abs(self.parent.x1 - self.parent.x0) // 2, self.parent.y1))
            painter.drawPoint(QPoint(self.parent.x0, self.parent.y0))
            painter.drawPoint(QPoint(self.parent.x0, self.parent.y1))
            painter.drawPoint(QPoint(self.parent.x1, self.parent.y0))
            painter.drawPoint(QPoint(self.parent.x1, self.parent.y1))

            x = y = 100
            if self.parent.x1 > self.parent.x0:
                x = self.parent.x0 + 5
            else:
                x = self.parent.x0 - 72
            if self.parent.y1 > self.parent.y0:
                y = self.parent.y0 + 15
            else:
                y = self.parent.y0 - 5
            painter.setPen(QPen(Qt.darkGreen, 2, Qt.SolidLine))
            painter.drawText(x, y,
                             '{}x{}'.format(abs(self.parent.x1 - self.parent.x0), abs(self.parent.y1 - self.parent.y0)))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 120))
            painter.drawRect(0, 0, self.width(), min(self.parent.y1, self.parent.y0))
            painter.drawRect(0, min(self.parent.y1, self.parent.y0), min(self.parent.x1, self.parent.x0),
                             self.height() - min(self.parent.y1, self.parent.y0))
            painter.drawRect(max(self.parent.x1, self.parent.x0), min(self.parent.y1, self.parent.y0),
                             self.width() - max(self.parent.x1, self.parent.x0),
                             self.height() - min(self.parent.y1, self.parent.y0))
            painter.drawRect(min(self.parent.x1, self.parent.x0), max(self.parent.y1, self.parent.y0),
                             max(self.parent.x1, self.parent.x0) - min(self.parent.x1, self.parent.x0),
                             self.height() - max(self.parent.y1, self.parent.y0))
        # 以下为鼠标放大镜
        if not (self.parent.painter_tools['drawcircle_on'] or self.parent.painter_tools['drawrect_bs_on'] or
                self.parent.painter_tools['pen_on'] or self.parent.painter_tools['eraser_on'] or
                self.parent.painter_tools['drawtext_on'] or self.parent.painter_tools['backgrounderaser_on']
                or self.parent.painter_tools['drawpix_bs_on'] or self.parent.move_rect):

            painter.setPen(QPen(self.parent.pencolor, 2, Qt.SolidLine))
            if self.parent.mouse_posx > self.width() - 140:
                enlarge_box_x = self.parent.mouse_posx - 140
            else:
                enlarge_box_x = self.parent.mouse_posx + 20
            if self.parent.mouse_posy > self.height() - 140:
                enlarge_box_y = self.parent.mouse_posy - 120
            else:
                enlarge_box_y = self.parent.mouse_posy + 20
            enlarge_rect = QRect(enlarge_box_x, enlarge_box_y, 120, 120)
            painter.drawRect(enlarge_rect)
            painter.drawText(enlarge_box_x, enlarge_box_y - 8,
                             '({0}x{1})'.format(self.parent.mouse_posx, self.parent.mouse_posy))
            if self.parent.painter_tools['selectcolor_on'] or self.parent.painter_tools['bucketpainter_on']:  # 取色器或油漆桶
                color = QColor(self.parent.qimg.pixelColor(self.parent.mouse_posx, self.parent.mouse_posy))
                painter.drawText(enlarge_box_x + 70, enlarge_box_y - 8,
                                 color.name())
                painter.drawText(enlarge_box_x, enlarge_box_y - 25,
                                 " rgb({},{},{})".format(color.red(), color.green(), color.blue()))
                painter.setBrush(QBrush(color))
                painter.drawRect(QRect(enlarge_box_x - 20, enlarge_box_y, 20, 20))
                painter.setBrush(Qt.NoBrush)

            try:  # 鼠标放大镜
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                rpix = QPixmap(self.width() + 120, self.height() + 120)
                rpix.fill(QColor(0, 0, 0))
                rpixpainter = QPainter(rpix)
                rpixpainter.drawPixmap(60, 60, self.parent.pixmap())
                rpixpainter.end()
                larger_pix = rpix.copy(self.parent.mouse_posx, self.parent.mouse_posy, 120, 120).scaled(
                    120 + self.parent.tool_width * 10, 120 + self.parent.tool_width * 10)
                pix = larger_pix.copy(larger_pix.width() // 2 - 60, larger_pix.height() // 2 - 60, 120, 120)
                painter.drawPixmap(enlarge_box_x, enlarge_box_y, pix)
                painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
                painter.drawLine(enlarge_box_x, enlarge_box_y + 60, enlarge_box_x + 120, enlarge_box_y + 60)
                painter.drawLine(enlarge_box_x + 60, enlarge_box_y, enlarge_box_x + 60, enlarge_box_y + 120)
            except:
                print('draw_enlarge_box fail')

        painter.end()


class PaintLayer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # self.setAutoFillBackground(False)
        # self.setPixmap(QPixmap())
        self.setMouseTracking(True)
        self.px = self.py = -50
        self.pixpng = QPixmap(":/msk.jpg")

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.parent.on_init:
            print('oninit return')
            return
        if 1 in self.parent.painter_tools.values():  # 如果有画笔工具打开
            painter = QPainter(self)
            color = QColor(self.parent.pencolor)
            color.setAlpha(255)

            width = self.parent.tool_width
            if self.parent.painter_tools['selectcolor_on'] or self.parent.painter_tools['bucketpainter_on']:
                width = 5
                color = QColor(Qt.white)
            painter.setPen(QPen(color, 1, Qt.SolidLine))
            rect = QRectF(self.px - width // 2, self.py - width // 2,
                          width, width)
            painter.drawEllipse(rect)  # 画鼠标圆
            painter.end()
        # self.pixPainter.begin()
        try:
            self.pixPainter = QPainter(self.pixmap())
            self.pixPainter.setRenderHint(QPainter.Antialiasing)
        except:
            print('pixpainter fail!')
        while len(self.parent.eraser_pointlist):  # 橡皮擦工具
            # self.pixPainter.setRenderHint(QPainter.Antialiasing)
            self.pixPainter.setBrush(QColor(0, 0, 0, 0))
            self.pixPainter.setPen(Qt.NoPen)
            self.pixPainter.setCompositionMode(QPainter.CompositionMode_Clear)
            new_pen_point = self.parent.eraser_pointlist.pop(0)
            if self.parent.old_pen is None:
                self.parent.old_pen = new_pen_point
                continue
            if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                self.pixPainter.drawEllipse(new_pen_point[0] - self.parent.tool_width / 2,
                                            new_pen_point[1] - self.parent.tool_width / 2,
                                            self.parent.tool_width, self.parent.tool_width)
                if abs(new_pen_point[0] - self.parent.old_pen[0]) > 1 or abs(
                        new_pen_point[1] - self.parent.old_pen[1]) > 1:
                    interpolateposs = get_line_interpolation(new_pen_point[:], self.parent.old_pen[:])
                    if interpolateposs is not None:
                        for pos in interpolateposs:
                            x, y = pos
                            self.pixPainter.drawEllipse(x - self.parent.tool_width / 2,
                                                        y - self.parent.tool_width / 2,
                                                        self.parent.tool_width, self.parent.tool_width)

            self.parent.old_pen = new_pen_point

        def get_ture_pen_alpha_color():
            color = QColor(self.parent.pencolor)
            if color.alpha() != 255:
                al = self.parent.pencolor.alpha() / (self.parent.tool_width / 2)
                if al > 1:
                    color.setAlpha(al)
                else:
                    color.setAlpha(1)
            return color

        while len(self.parent.pen_pointlist):  # 画笔工具
            color = get_ture_pen_alpha_color()
            self.pixPainter.setBrush(color)
            self.pixPainter.setPen(Qt.NoPen)
            # self.pixPainter.setPen(QPen(self.parent.pencolor, self.parent.tool_width, Qt.SolidLine))
            self.pixPainter.setRenderHint(QPainter.Antialiasing)
            new_pen_point = self.parent.pen_pointlist.pop(0)
            if self.parent.old_pen is None:
                self.parent.old_pen = new_pen_point
                continue
            if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                self.pixPainter.drawEllipse(new_pen_point[0] - self.parent.tool_width / 2,
                                            new_pen_point[1] - self.parent.tool_width / 2,
                                            self.parent.tool_width, self.parent.tool_width)
                if abs(new_pen_point[0] - self.parent.old_pen[0]) > 1 or abs(
                        new_pen_point[1] - self.parent.old_pen[1]) > 1:
                    interpolateposs = get_line_interpolation(new_pen_point[:], self.parent.old_pen[:])
                    if interpolateposs is not None:
                        for pos in interpolateposs:
                            x, y = pos
                            self.pixPainter.drawEllipse(x - self.parent.tool_width / 2,
                                                        y - self.parent.tool_width / 2,
                                                        self.parent.tool_width, self.parent.tool_width)

            self.parent.old_pen = new_pen_point
        while len(self.parent.drawpix_pointlist):  # 贴图工具
            brush = QBrush(self.parent.pencolor)
            tpix = QPixmap(self.parent.tool_width, self.parent.tool_width)
            tpix.fill(Qt.transparent)
            tpixpainter = QPainter(tpix)
            tpixpainter.setCompositionMode(QPainter.CompositionMode_Source)
            tpixpainter.drawPixmap(0, 0, self.pixpng.scaled(self.parent.tool_width, self.parent.tool_width))
            tpixpainter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            if self.parent.pencolor.alpha() != 255:
                al = self.parent.pencolor.alpha() / (self.parent.tool_width / 2)
            else:
                al = 255
            tpixpainter.fillRect(tpix.rect(), QColor(0, 0, 0, al))
            tpixpainter.end()
            brush.setTexture(tpix)
            self.pixPainter.setBrush(brush)
            self.pixPainter.setPen(Qt.NoPen)
            new_pen_point = self.parent.drawpix_pointlist.pop(0)
            if self.parent.old_pen is None:
                self.parent.old_pen = new_pen_point
                continue
            if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                self.pixPainter.drawEllipse(new_pen_point[0] - self.parent.tool_width / 2,
                                            new_pen_point[1] - self.parent.tool_width / 2,
                                            self.parent.tool_width, self.parent.tool_width)
                if abs(new_pen_point[0] - self.parent.old_pen[0]) > 1 or abs(
                        new_pen_point[1] - self.parent.old_pen[1]) > 1:
                    interpolateposs = get_line_interpolation(new_pen_point[:], self.parent.old_pen[:])
                    if interpolateposs is not None:
                        for pos in interpolateposs:
                            x, y = pos
                            self.pixPainter.drawEllipse(x - self.parent.tool_width / 2,
                                                        y - self.parent.tool_width / 2,
                                                        self.parent.tool_width, self.parent.tool_width)

            self.parent.old_pen = new_pen_point
        if self.parent.drawrect_pointlist[0][0] != -2 and self.parent.drawrect_pointlist[1][0] != -2:  # 画矩形工具
            # print(self.parent.drawrect_pointlist)
            temppainter = QPainter(self)
            temppainter.setPen(QPen(self.parent.pencolor, self.parent.tool_width, Qt.SolidLine))

            poitlist = self.parent.drawrect_pointlist
            temppainter.drawRect(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                 abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))
            temppainter.end()
            if self.parent.drawrect_pointlist[2] == 1:
                self.pixPainter.setPen(QPen(self.parent.pencolor, self.parent.tool_width, Qt.SolidLine))
                self.pixPainter.drawRect(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                         abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))

                self.parent.drawrect_pointlist = [[-2, -2], [-2, -2], 0]
                # print("panit",self.parent.drawrect_pointlist)
                # self.parent.drawrect_pointlist[0] = [-2, -2]

        if self.parent.drawcircle_pointlist[0][0] != -2 and self.parent.drawcircle_pointlist[1][0] != -2:  # 画圆工具
            temppainter = QPainter(self)
            temppainter.setPen(QPen(self.parent.pencolor, self.parent.tool_width, Qt.SolidLine))
            poitlist = self.parent.drawcircle_pointlist
            temppainter.drawEllipse(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                    abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))
            temppainter.end()
            if self.parent.drawcircle_pointlist[2] == 1:
                self.pixPainter.setPen(QPen(self.parent.pencolor, self.parent.tool_width, Qt.SolidLine))
                self.pixPainter.drawEllipse(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                            abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))
                self.parent.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]
                # self.parent.drawcircle_pointlist[0] = [-2, -2]

        if self.parent.drawarrow_pointlist[0][0] != -2 and self.parent.drawarrow_pointlist[1][0] != -2:  # 画箭头
            # print(self.parent.drawarrow_pointlist)
            # self.pixPainter = QPainter(self.pixmap())
            temppainter = QPainter(self)
            # temppainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
            # brush = QBrush(self.parent.pencolor)
            # brush.setTexture(QPixmap(":/msk.jpg").scaled(225, 225))
            # temppainter.setBrush(brush)
            poitlist = self.parent.drawarrow_pointlist
            temppainter.translate(poitlist[0][0], poitlist[0][1])
            degree = math.degrees(math.atan2(poitlist[1][1] - poitlist[0][1], poitlist[1][0] - poitlist[0][0]))
            temppainter.rotate(degree)
            dx = math.sqrt((poitlist[1][1] - poitlist[0][1]) ** 2 + (poitlist[1][0] - poitlist[0][0]) ** 2)
            dy = 30
            temppainter.drawPixmap(0, -dy / 2, QPixmap(':/arrow.png').scaled(dx, dy))

            temppainter.end()
            if self.parent.drawarrow_pointlist[2] == 1:
                self.pixPainter.translate(poitlist[0][0], poitlist[0][1])
                degree = math.degrees(math.atan2(poitlist[1][1] - poitlist[0][1], poitlist[1][0] - poitlist[0][0]))
                self.pixPainter.rotate(degree)
                dx = math.sqrt((poitlist[1][1] - poitlist[0][1]) ** 2 + (poitlist[1][0] - poitlist[0][0]) ** 2)
                dy = 30
                self.pixPainter.drawPixmap(0, -dy / 2, QPixmap(':/arrow.png').scaled(dx, dy))
                self.parent.drawarrow_pointlist = [[-2, -2], [-2, -2], 0]
                # self.parent.drawarrow_pointlist[0] = [-2, -2]

        if len(self.parent.drawtext_pointlist) > 1 or self.parent.text_box.paint:  # 绘制文字
            self.parent.text_box.paint = False
            # print(self.parent.drawtext_pointlist)
            text = self.parent.text_box.toPlainText()
            self.parent.text_box.clear()
            pos = self.parent.drawtext_pointlist.pop(0)
            if text:
                self.pixPainter.setFont(QFont('', self.parent.tool_width))
                self.pixPainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
                self.pixPainter.drawText(pos[0] + self.parent.text_box.document.size().height() / 8,
                                         pos[1] + self.parent.text_box.document.size().height() * 32 / 41, text)
                self.parent.backup_shortshot()
                self.parent.setFocus()
                self.update()
                # self.repaint()
        try:
            self.pixPainter.end()
        except:
            print("pixpainter end fail!")


class AutotextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = self.document()
        self.document.contentsChanged.connect(self.textAreaChanged)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.paint = False
        self.parent = parent

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

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.paint = True
            self.hide()
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.parent.update()
        super().keyReleaseEvent(e)


class Freezer(QLabel):
    def __init__(self, parent=None, img=None, x=0, y=0, listpot=0):
        super().__init__()

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
        elif action == rectaction:
            self.drawRect = not self.drawRect
            self.update()

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
                    w = self.width() + dy * 5
                    if w < 50: w = 50
                    if w > 2 * QApplication.desktop().width(): w = 2 * QApplication.desktop().width()
                    scale = self.imgpix.height() / self.imgpix.width()
                    h = w * scale
                    s = self.width() / w  # 缩放比例
                    mdx = e.x() * s - e.x()
                    mdy = e.y() * s - e.y()
                    self.setPixmap(self.imgpix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.setGeometry(self.x() + mdx, self.y() + mdy, w, h)
                    QApplication.processEvents()

            self.update()

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
        super().clear()
        # jamtools.freeze_imgs[self.listpot] = None

    def closeEvent(self, e):
        self.clear()
        e.ignore()


class Slabel(QLabel):  # 区域截图功能
    showm_signal = pyqtSignal(str)
    recorder_recordchange_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        # self.ready_flag = False
        self.parent = parent
        if not os.path.exists("j_temp"):
            os.mkdir("j_temp")
        # self.pixmap()=QPixmap()

    def setup(self):  # 初始化界面
        self.on_init = True
        self.paintlayer = PaintLayer(self)  # 绘图层
        self.mask = MaskLayer(self)  # 遮罩层
        self.text_box = AutotextEdit(self)  # 文字工具类
        self.shower = FramelessEnterSendQTextEdit(self, enter_tra=True)  # 截屏时文字识别的小窗口
        self.settings = QSettings('Fandes', 'jamtools')
        self.setMouseTracking(True)
        if PLATFORM_SYS == "darwin":
            self.setWindowFlags(Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)  # Sheet
        # self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.botton_box = QGroupBox(self)  # botton_box是截屏选框旁边那个按钮堆的box
        self.save_botton = QPushButton(QIcon(":/saveicon.png"), '', self.botton_box)
        self.save_botton.clicked.connect(lambda: self.cutpic(1))
        self.ssrec_botton = QPushButton(QIcon(":/ssrecord.png"), '', self.botton_box)
        self.cla_botton = QPushButton(self.botton_box)
        self.ocr_botton = QPushButton(self.botton_box)
        self.btn2 = QPushButton(self.botton_box)
        self.btn1 = QPushButton("确定", self.botton_box)
        self.freeze_img_botton = QPushButton(self.botton_box)
        self.pencolor = QColor(Qt.red)
        self.painter_box = CanMoveGroupbox(self)  # painter_box是绘图工具堆里的那个box,可移动
        self.choice_clor_btn = HoverButton('', self.painter_box)
        self.selectcolor_btn = QPushButton("", self.painter_box)
        self.original_btn = QPushButton("", self.painter_box)
        self.size_slider = QSlider(Qt.Vertical, self.painter_box)
        self.alpha_slider = QSlider(Qt.Vertical, self.painter_box)
        self.sizetextlabel = QLabel(self.painter_box)
        self.alphatextlabel = QLabel(self.painter_box)
        self.size_slider_label = QLabel(self.painter_box)
        self.alpha_slider_label = QLabel(self.painter_box)
        self.drawarrow = QPushButton('', self.painter_box)
        self.msk = QPushButton('', self.painter_box)
        self.choise_pix = QPushButton('', self.painter_box)
        self.drawcircle = QPushButton('', self.painter_box)
        self.bs = QPushButton('', self.painter_box)
        self.drawtext = QPushButton('', self.painter_box)
        self.pen = QPushButton('', self.painter_box)
        self.eraser = QPushButton('', self.painter_box)
        self.backgrounderaser = QPushButton('', self.painter_box)
        self.smartcursor_btn = QPushButton('', self.painter_box)
        self.bucketpainter_btn = QPushButton("", self.painter_box)
        self.bucketpainter_tolerance = QSpinBox(self.painter_box)
        self.backgroundrepair_btn = QPushButton("", self.painter_box)
        self.perspective_cut_btn = QPushButton("", self.painter_box)
        self.polygon_ss_btn = QPushButton("", self.painter_box)
        self.lastbtn = QPushButton("", self.painter_box)
        self.nextbtn = QPushButton("", self.painter_box)
        self.finder = Finder(self)  # 智能选区的寻找器
        self.Tipsshower = TipsShower("  ", targetarea=(100, 70, 0, 0), parent=self)  # 左上角的大字提示
        self.Tipsshower.hide()
        self.shower.showm_signal.connect(self.Tipsshower.setText)
        if PLATFORM_SYS == "darwin":
            self.init_slabel_ui()
            print("init slabel ui")
        else:
            self.init_slabel_ui()
            print("init slabel ui")
            # self.init_slabel_thread = Commen_Thread(self.init_slabel_ui)
            # self.init_slabel_thread.start()

        # self.setVisible(False)
        # self.setWindowOpacity(0)
        # self.showFullScreen()
        # self.hide()
        # self.setWindowOpacity(1)

        self.init_parameters()
        self.backup_ssid = 0  # 当前备份数组的id,用于确定回退了几步
        self.backup_pic_list = []  # 备份页面的数组,用于前进/后退
        self.on_init = False

    def init_parameters(self):  # 初始化参数
        self.NpainterNmoveFlag = self.choicing = self.move_rect = self.move_y0 = self.move_x0 = self.move_x1 \
            = self.change_alpha = self.move_y1 = False
        self.x0 = self.y0 = self.rx0 = self.ry0 = self.x1 = self.y1 = self.mouse_posx = self.mouse_posy = -50
        self.bx = self.by = 0
        self.alpha = 255  # 透明度值
        self.smartcursor_on = self.settings.value("screenshot/smartcursor", True, type=bool)
        self.finding_rect = True  # 正在自动寻找选取的控制变量,就进入截屏之后会根据鼠标移动到的位置自动选取,
        self.tool_width = 5
        self.roller_area = (0, 0, 1, 1)
        self.backgrounderaser_pointlist = []  # 下面xxpointlist都是储存绘图数据的列表
        self.eraser_pointlist = []
        self.pen_pointlist = []
        self.drawpix_pointlist = []
        self.repairbackground_pointlist = []
        self.drawtext_pointlist = []
        self.perspective_cut_pointlist = []
        self.polygon_ss_pointlist = []
        self.drawrect_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawarrow_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]
        self.painter_tools = {'drawpix_bs_on': 0, 'drawarrow_on': 0, 'drawcircle_on': 0, 'drawrect_bs_on': 0,
                              'pen_on': 0, 'eraser_on': 0, 'drawtext_on': 0,
                              'backgrounderaser_on': 0, 'selectcolor_on': 0, "bucketpainter_on": 0,
                              "repairbackground_on": 0, "perspective_cut_on": 0, "polygon_ss_on": 0}

        self.old_pen = self.old_eraser = self.old_brush = self.old_backgrounderaser = [-2, -2]
        self.left_button_push = False

    def init_slabel_ui(self):  # 初始化界面的参数

        self.shower.hide()
        self.shower.setWindowOpacity(0.8)
        if PLATFORM_SYS == "darwin":
            self.move(-QApplication.desktop().width(), -QApplication.desktop().height())

        self.setToolTip("左键框选，右键返回")

        self.ssrec_botton.setGeometry(0, 0, 40, 35)
        self.ssrec_botton.clicked.connect(self.ssrec)
        self.ssrec_botton.setToolTip('开始录屏')
        self.save_botton.setGeometry(self.ssrec_botton.x() + self.ssrec_botton.width(), 0, 40, 35)
        self.save_botton.setToolTip('另存为文件')
        self.freeze_img_botton.setGeometry(self.save_botton.x() + self.save_botton.width(), 0, 40, 35)
        self.freeze_img_botton.setIcon(QIcon(":/freeze.png"))
        self.freeze_img_botton.setToolTip('固定图片于屏幕上')
        self.freeze_img_botton.clicked.connect(self.freeze_img)
        self.cla_botton.setGeometry(self.freeze_img_botton.x() + self.freeze_img_botton.width(), 0, 40, 35)
        self.cla_botton.setIcon(QIcon(":/CLA.png"))
        self.cla_botton.setToolTip('图像主体识别')
        self.cla_botton.clicked.connect(self.cla)
        self.ocr_botton.setGeometry(self.cla_botton.x() + self.cla_botton.width(), 0, 40, 35)
        self.ocr_botton.setIcon(QIcon(":/OCR.png"))
        self.ocr_botton.setToolTip('文字识别')
        self.ocr_botton.clicked.connect(self.ocr)

        if PLATFORM_SYS == "darwin":  # 不支持macos滚动截屏
            self.btn2.hide()
            self.btn1.setGeometry(self.ocr_botton.x() + self.ocr_botton.width(), 0, 60, 35)
        else:
            self.btn2.setGeometry(self.ocr_botton.x() + self.ocr_botton.width(), 0, 40, 35)
            self.btn2.clicked.connect(self.roll_shot)
            self.btn2.setToolTip('滚动截屏功能')
            self.btn2.setIcon(QIcon(":/scroll_icon.png"))
            self.btn1.setGeometry(self.btn2.x() + self.btn2.width(), 0, 60, 35)

        self.btn1.clicked.connect(self.cutpic)
        a = self.btn2.width() if PLATFORM_SYS != "darwin" else 0
        self.botton_box.resize(
            self.btn1.width() + self.cla_botton.width() + self.ocr_botton.width() + self.ssrec_botton.width()
            + a + self.save_botton.width() + self.freeze_img_botton.width(),
            self.btn1.height())
        self.botton_box.hide()

        self.painter_box.setGeometry(0, QApplication.desktop().height() // 2 - 200, 100, 400)

        self.size_slider_label.setStyleSheet('background-color:rgba(0,0,0,0);color: rgb(255,255,255);')
        self.size_slider_label.resize(20, 20)
        self.size_slider.setGeometry(10, 20, 25, 60)
        self.size_slider.setToolTip('设置画笔大小,也可用鼠标滚轮调节')
        self.size_slider.valueChanged.connect(self.change_size_fun)
        self.sizetextlabel.setText("size")

        self.sizetextlabel.setGeometry(self.size_slider.x() - 2, self.size_slider.y() + self.size_slider.height() - 2,
                                       35, 20)

        self.sizetextlabel.setStyleSheet('background-color:rgba(0,0,0,0);color: rgb(255,255,255);')
        self.size_slider.setMaximum(99)
        self.size_slider.setValue(5)
        self.size_slider.setMinimum(1)

        self.size_slider_label.move(self.size_slider.x() + 5, 0)
        self.size_slider.show()

        self.alpha_slider_label.setStyleSheet('background-color:rgba(0,0,0,0);color: rgb(255,255,255);')
        self.alpha_slider_label.resize(25, 20)
        self.alpha_slider.setGeometry(55, 20, 25, 60)
        self.alpha_slider.setToolTip('设置画笔透明度,按住Ctrl+滚轮也可以调节透明度')
        self.alpha_slider.valueChanged.connect(self.change_alpha_fun)
        self.alphatextlabel.setText("alpha")
        self.alphatextlabel.setGeometry(self.alpha_slider.x() - 4,
                                        self.alpha_slider.y() + self.alpha_slider.height() - 2,
                                        40, 20)
        self.alphatextlabel.setStyleSheet('background-color:rgba(0,0,0,0);color: rgb(255,255,255);')
        self.alpha_slider.setMaximum(255)
        self.alpha_slider.setValue(255)
        self.alpha_slider.setMinimum(1)

        self.alpha_slider_label.move(self.alpha_slider.x() + 2, 0)
        self.alpha_slider.show()
        # print(pic)

        self.choice_clor_btn.setToolTip('选择画笔颜色,点击可选择更多')
        self.choice_clor_btn.setIcon(QIcon(":/yst.png"))
        self.choice_clor_btn.setGeometry(4, 100, 41, 28)
        self.choice_clor_btn.clicked.connect(self.get_color)
        self.choice_clor_btn.hoversignal.connect(self.Color_hoveraction)

        self.selectcolor_btn.setIcon(QIcon(":/colorsampler.png"))
        self.selectcolor_btn.setGeometry(50, self.choice_clor_btn.y(), self.choice_clor_btn.width(),
                                         self.choice_clor_btn.height())
        self.selectcolor_btn.setToolTip("取色器")
        self.selectcolor_btn.clicked.connect(self.selectcolor)

        self.msk.setToolTip('材质贴图工具,可以充当马赛克')
        self.msk.setIcon(QIcon(":/mskicon.png"))
        self.msk.setGeometry(self.choice_clor_btn.x(), self.choice_clor_btn.y() + self.choice_clor_btn.height(),
                             self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.msk.clicked.connect(self.change_msk_fun)
        self.choise_pix.setToolTip('选择笔刷材质贴图')
        self.choise_pix.setIcon(QIcon(":/msk.jpg"))
        self.choise_pix.setGeometry(35, self.msk.y(), self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.choise_pix.clicked.connect(self.choise_drawpix_fun)
        self.choise_pix.setStyleSheet("background-color:rgb(255,255,255);border: 3px solid #ffffff;")
        self.choise_pix.hide()

        self.drawarrow.setToolTip('绘制箭头')
        self.drawarrow.setIcon(QIcon(":/arrowicon.png"))
        self.drawarrow.setGeometry(self.selectcolor_btn.x(), self.selectcolor_btn.y() + self.selectcolor_btn.height(),
                                   self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.drawarrow.clicked.connect(self.draw_arrow_fun)

        self.drawcircle.setToolTip('绘制圆')
        self.drawcircle.setIcon(QIcon(":/circle.png"))
        self.drawcircle.setGeometry(self.choice_clor_btn.x(), self.msk.y() + self.msk.height(),
                                    self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.drawcircle.clicked.connect(self.drawcircle_fun)

        self.bs.setToolTip('绘制矩形')
        self.bs.setIcon(QIcon(":/rect.png"))
        self.bs.setGeometry(self.drawarrow.x(), self.drawarrow.y() + self.drawarrow.height(),
                            self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.bs.clicked.connect(self.change_bs_fun)

        self.drawtext.setToolTip('绘制文字')
        self.drawtext.setIcon(QIcon(":/texticon.png"))
        self.drawtext.setGeometry(self.choice_clor_btn.x(), self.drawcircle.y() + self.drawcircle.height(),
                                  self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.drawtext.clicked.connect(self.drawtext_fun)

        self.pen.setToolTip('画笔工具')
        self.pen.setIcon(QIcon(":/pen.png"))
        self.pen.setGeometry(self.bs.x(), self.bs.y() + self.bs.height(),
                             self.choice_clor_btn.width(), self.choice_clor_btn.height())

        self.pen.clicked.connect(self.change_pen_fun)

        self.eraser.setToolTip('橡皮擦')
        self.eraser.setIcon(QIcon(":/eraser.png"))
        self.eraser.setGeometry(self.choice_clor_btn.x(), self.drawtext.y() + self.drawtext.height(),
                                self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.eraser.clicked.connect(self.clear_paint_fun)
        self.backgrounderaser.setIcon(QIcon(":/backgrounderaser.png"))
        self.backgrounderaser.setToolTip('背景橡皮擦,图片包含透明通道,擦除部分图片将变透明,\n但由于win的剪切板不支持透明通道,只有另存时透明通道才有作用!')
        self.backgrounderaser.setGeometry(self.pen.x(), self.pen.y() + self.pen.height(),
                                          self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.backgrounderaser.clicked.connect(self.clear_background_fun)

        self.backgroundrepair_btn.setIcon(QIcon(":/backgroundrepair.png"))
        self.backgroundrepair_btn.setToolTip('背景修复画笔,用于将背景图片层复原')
        self.backgroundrepair_btn.setGeometry(self.backgrounderaser.x(),
                                              self.backgrounderaser.y() + self.backgrounderaser.height(),
                                              self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.backgroundrepair_btn.clicked.connect(self.repair_background_fun)

        self.bucketpainter_btn.setToolTip("油漆桶工具")
        self.bucketpainter_btn.setIcon(QIcon(":/yqt.png"))
        self.bucketpainter_btn.setGeometry(self.choice_clor_btn.x(),
                                           self.backgrounderaser.y() + self.backgrounderaser.height(),
                                           self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.bucketpainter_btn.clicked.connect(self.bucketpaint)
        self.bucketpainter_tolerance.setToolTip('设置填充容差')
        self.bucketpainter_tolerance.setGeometry(self.choice_clor_btn.x(), self.painter_box.height() - 30, 85, 25)
        self.bucketpainter_tolerance.setMaximum(255)
        self.bucketpainter_tolerance.setPrefix("容差")
        self.bucketpainter_tolerance.setValue(self.settings.value("screenshot/tolerance", 0, int))
        self.bucketpainter_tolerance.setStyleSheet(
            "border: 2px solid rgb(200,200,200);color:rgb(255,255,255);background-color:rgb(110,110,120);border-radius:2px;")
        self.bucketpainter_tolerance.valueChanged.connect(self.bucketpainter_tolerancechange)
        self.bucketpainter_tolerance.hide()

        self.polygon_ss_btn.setToolTip("多边形截图")
        self.polygon_ss_btn.setIcon(QIcon(":/polygon_ss.png"))
        self.polygon_ss_btn.setGeometry(self.choice_clor_btn.x(),
                                        self.bucketpainter_btn.y() + self.bucketpainter_btn.height(),
                                        self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.polygon_ss_btn.clicked.connect(self.polygon_ss)

        self.perspective_cut_btn.setToolTip("透视裁剪工具")
        self.perspective_cut_btn.setIcon(QIcon(":/perspective.png"))
        self.perspective_cut_btn.setGeometry(self.backgroundrepair_btn.x(),
                                             self.backgroundrepair_btn.y() + self.backgroundrepair_btn.height(),
                                             self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.perspective_cut_btn.clicked.connect(self.perspective_cut)

        self.smartcursor_btn.setToolTip("智能选区")
        self.smartcursor_btn.setIcon(QIcon(":/smartcursor.png"))
        self.smartcursor_btn.setGeometry(self.choice_clor_btn.x(),
                                         self.polygon_ss_btn.y() + self.polygon_ss_btn.height(),
                                         self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.smartcursor_btn.clicked.connect(self.change_smartcursor)

        self.original_btn.setIcon(QIcon(":/original.png"))
        self.original_btn.setGeometry(self.perspective_cut_btn.x(),
                                      self.perspective_cut_btn.y() + self.perspective_cut_btn.height(),
                                      self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.original_btn.setToolTip("还原所有")
        self.original_btn.clicked.connect(self.setoriginalpix)

        self.lastbtn.setToolTip("上一步Ctrl+Z")
        self.lastbtn.setIcon(QIcon(":/last.png"))
        self.lastbtn.setGeometry(self.smartcursor_btn.x(), self.smartcursor_btn.y() + self.smartcursor_btn.height(),
                                 self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.lastbtn.clicked.connect(self.last_step)

        self.nextbtn.setToolTip("下一步Ctrl+Y")
        self.nextbtn.setIcon(QIcon(":/next.png"))
        self.nextbtn.setGeometry(self.original_btn.x(), self.original_btn.y() + self.original_btn.height(),
                                 self.choice_clor_btn.width(), self.choice_clor_btn.height())
        self.nextbtn.clicked.connect(self.next_step)
        print(1)
        tipsfont = QFont("", 35)
        # tipsfont.setBold(True)
        self.Tipsshower.setFont(tipsfont)
        self.choice_clor_btn.setStyleSheet('background-color:rgb(255,0,0);')
        if self.settings.value("screenshot/smartcursor", True, type=bool):
            self.smartcursor_btn.setStyleSheet("background-color:rgb(50,50,50);")

    def ssrec(self):  # 录屏函数
        self.parent.setingarea = True
        self.cutpic()
        self.recorder_recordchange_signal.emit()
        # recorder.recordchange()

    def Color_hoveraction(self, hover):  # 鼠标滑过选色按钮时触发的
        if hover:
            try:
                self.closenomalcolorboxtimer.stop()
                self.nomalcolorbox.show()
                print("nomalcolorbox show")
            except AttributeError:
                self.nomalcolorbox = HoverGroupbox(self)
                self.closenomalcolorboxtimer = QTimer(self)
                btnscolors = [Qt.red, Qt.darkRed, Qt.green, Qt.darkGreen, Qt.blue, Qt.darkBlue, Qt.yellow,
                              Qt.darkYellow,
                              Qt.darkCyan, Qt.darkMagenta, Qt.white, QColor(200, 200, 200), Qt.gray, Qt.darkGray,
                              Qt.black,
                              QColor(50, 50, 50)]
                y1 = 0
                y2 = 30
                d = 30
                for i in range((len(btnscolors) + 1) // 2):
                    btn1 = ColorButton(btnscolors[2 * i], self.nomalcolorbox)
                    btn1.resize(d, d)
                    btn1.select_color_signal.connect(self.selectnomal_color)
                    btn1.move(5 + i * d, y1)
                    if len(btnscolors) > 2 * i + 1:
                        btn2 = ColorButton(btnscolors[2 * i + 1], self.nomalcolorbox)
                        btn2.resize(d, d)
                        btn2.select_color_signal.connect(self.selectnomal_color)
                        btn2.move(5 + i * d, y2)
                self.nomalcolorbox.setGeometry(
                    self.painter_box.x() + self.choice_clor_btn.x() + self.choice_clor_btn.width() + 1,
                    self.painter_box.y() + self.choice_clor_btn.y() + self.choice_clor_btn.height() - y2 * 2,
                    (len(btnscolors) // 2 + 1) * 50 + 10, y2 * 2)
            except:
                print(sys.exc_info(), 1150)

            self.nomalcolorbox.hoversignal.connect(self.closenomalcolorboxsignalhandle)
            self.nomalcolorbox.show()
            self.nomalcolorbox.raise_()

            self.closenomalcolorboxtimer.timeout.connect(self.closenomalcolorbox)
            self.closenomalcolorboxtimer.start(2000)

            # self.refresh_hideclosenomalsignal()
        # else:

    def closenomalcolorboxsignalhandle(self, s):  # 关闭常见颜色浮窗的函数
        if s:
            try:
                self.closenomalcolorboxtimer.stop()
            except:
                print(sys.exc_info(), 1162)
        else:
            print("离开box信号", s)

            self.closenomalcolorboxtimer.start(1000)

    def closenomalcolorbox(self):
        try:
            self.nomalcolorbox.hide()
            self.closenomalcolorboxtimer.stop()
            self.nomalcolorbox = None
        except:
            print(sys.exc_info())

    def selectnomal_color(self, color):
        # print(color)
        self.get_color(QColor(color))
        # self.nomalcolorbox = None

    def get_color(self, color: QColor = None):  # 选择颜色
        if type(color) is not QColor:
            self.Tipsshower.setText("选择颜色")
            try:
                self.nomalcolorbox.hide()
            except:
                print(sys.exc_info())
            colordialog = QColorDialog(self)
            colordialog.setCurrentColor(self.pencolor)
            colordialog.setOption(QColorDialog.ShowAlphaChannel)
            colordialog.exec()
            self.pencolor = colordialog.currentColor()
        else:
            self.pencolor = color
        self.alpha_slider.setValue(self.pencolor.alpha())

        self.text_box.setTextColor(self.pencolor)
        self.choice_clor_btn.setStyleSheet('background-color:{0};'.format(self.pencolor.name()))

    def bucketpainter_tolerancechange(self, value):
        self.settings.setValue("screenshot/tolerance", value)

    def bucketpaint(self):  # 油漆桶工具
        if self.painter_tools['bucketpainter_on']:
            self.painter_tools['bucketpainter_on'] = 0
            self.bucketpainter_btn.setStyleSheet('')
            self.bucketpainter_tolerance.hide()
        else:
            self.change_tools_fun('bucketpainter_on')
            self.bucketpainter_btn.setStyleSheet('background-color:rgb(50,50,50)')
            self.Tipsshower.setText("油漆桶工具")
            self.bucketpainter_tolerance.show()
            self.setCursor(QCursor(QPixmap(":/yqt.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))

    def polygon_ss(self):  # 透视裁剪工具
        if self.painter_tools['polygon_ss_on']:
            self.painter_tools['polygon_ss_on'] = 0
            self.polygon_ss_btn.setStyleSheet('')
            self.polygon_ss_pointlist = []
            self.update()
        else:
            self.change_tools_fun('polygon_ss_on')
            self.polygon_ss_btn.setStyleSheet('background-color:rgb(50,50,50)')
            self.Tipsshower.setText("多边形截图工具")
            self.botton_box.hide()
            self.setCursor(QCursor(QPixmap(":/polygon_ss.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
            self.polygon_ss_pointlist = []
            QApplication.processEvents()

    def perspective_cut(self):
        if self.painter_tools['perspective_cut_on']:
            self.painter_tools['perspective_cut_on'] = 0
            self.perspective_cut_btn.setStyleSheet('')
            self.perspective_cut_pointlist = []
        else:
            self.change_tools_fun('perspective_cut_on')
            self.perspective_cut_btn.setStyleSheet('background-color:rgb(50,50,50)')
            self.Tipsshower.setText("透视裁剪工具")
            self.botton_box.hide()
            self.setCursor(QCursor(QPixmap(":/perspective.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
            self.perspective_cut_pointlist = []

    def change_smartcursor(self):
        self.settings.setValue("screenshot/smartcursor",
                               not self.settings.value("screenshot/smartcursor", True, type=bool))
        if self.settings.value("screenshot/smartcursor", True, type=bool):
            self.smartcursor_btn.setStyleSheet("background-color:rgb(50,50,50);")
            self.smartcursor_on = True
            self.Tipsshower.setText("智能选区:开")
        else:
            self.smartcursor_on = False
            self.smartcursor_btn.setStyleSheet("")
            self.Tipsshower.setText("智能选区:关")

    def selectcolor(self):
        if self.painter_tools['selectcolor_on']:
            self.painter_tools['selectcolor_on'] = 0
            self.selectcolor_btn.setStyleSheet('')
        else:
            self.change_tools_fun('selectcolor_on')
            self.selectcolor_btn.setStyleSheet('background-color:rgb(50,50,50)')
            self.Tipsshower.setText("取色器")
            self.setCursor(QCursor(QPixmap(":/colorsampler.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
            allpix = self.cutpic(save_as=3)
            self.qimg = allpix.toImage()

    def setoriginalpix(self):
        self.change_tools_fun("")
        self.setCursor(Qt.ArrowCursor)
        self.screen_shot(self.originalPix)

        self.Tipsshower.setText("已清除所有修改!")

    def drawcircle_fun(self):
        if self.painter_tools['drawcircle_on']:
            self.painter_tools['drawcircle_on'] = 0
            self.drawcircle.setStyleSheet('')
        else:
            self.change_tools_fun('drawcircle_on')
            self.drawcircle.setStyleSheet('background-color:rgb(50,50,50)')
            self.setCursor(QCursor(QPixmap(":/circle.png").scaled(32, 32, Qt.KeepAspectRatio), 16, 16))
            if self.tool_width > 6:
                self.size_slider.setValue(6)
            if self.alpha < 200:
                self.alpha_slider.setValue(255)
            self.Tipsshower.setText("圆形框工具")

    def draw_arrow_fun(self):
        if self.painter_tools['drawarrow_on']:
            self.painter_tools['drawarrow_on'] = 0
            self.drawarrow.setStyleSheet('')
        else:
            self.change_tools_fun('drawarrow_on')
            self.drawarrow.setStyleSheet('background-color:rgb(50,50,50)')
            self.setCursor(QCursor(QPixmap(":/arrowicon.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
            self.Tipsshower.setText("箭头工具")

    def drawtext_fun(self):
        if self.painter_tools['drawtext_on']:
            self.painter_tools['drawtext_on'] = 0
            self.drawtext.setStyleSheet('')
        else:
            self.change_tools_fun('drawtext_on')
            self.drawtext.setStyleSheet('background-color:rgb(50,50,50)')
            self.setCursor(QCursor(QPixmap(":/texticon.png").scaled(16, 16, Qt.KeepAspectRatio), 0, 0))
            self.Tipsshower.setText("绘制文本")

    def change_pen_fun(self):
        if self.painter_tools['pen_on']:
            self.painter_tools['pen_on'] = 0
            self.pen.setStyleSheet('')
        else:
            self.change_tools_fun('pen_on')
            self.pen.setStyleSheet('background-color:rgb(50,50,50)')
            self.Tipsshower.setText("画笔")
            self.setCursor(QCursor(QPixmap(":/pen.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))

    def clear_paint_fun(self):
        if self.painter_tools['eraser_on']:
            self.painter_tools['eraser_on'] = 0
            self.eraser.setStyleSheet('')
        else:
            self.change_tools_fun('eraser_on')
            self.eraser.setStyleSheet('background-color:rgb(50,50,50)')
            self.setCursor(QCursor(QPixmap(":/eraser.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
            self.Tipsshower.setText("画笔橡皮擦")

    def repair_background_fun(self):
        if self.painter_tools['repairbackground_on']:
            self.painter_tools['repairbackground_on'] = 0
            self.backgroundrepair_btn.setStyleSheet('')
        else:
            self.change_tools_fun('repairbackground_on')
            self.backgroundrepair_btn.setStyleSheet('background-color:rgb(50,50,50)')
            self.Tipsshower.setText("背景还原画笔")
            self.setCursor(QCursor(QPixmap(":/backgroundrepair.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 26))

    def clear_background_fun(self):
        if self.painter_tools['backgrounderaser_on']:
            self.painter_tools['backgrounderaser_on'] = 0
            self.backgrounderaser.setStyleSheet('')
        else:
            self.change_tools_fun('backgrounderaser_on')
            self.backgrounderaser.setStyleSheet('background-color:rgb(50,50,50)')
            self.Tipsshower.setText("背景橡皮擦")
            self.setCursor(QCursor(QPixmap(":/backgrounderaser.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))

    def change_size_fun(self):
        self.size_slider_label.setText(str(self.size_slider.value()))
        self.tool_width = self.size_slider.value()

    def change_alpha_fun(self):
        self.alpha_slider_label.setText(str(self.alpha_slider.value()))
        self.alpha = self.alpha_slider.value()
        self.pencolor.setAlpha(self.alpha)

    def change_tools_fun(self, r):  # 更改工具时统一调用的函数,用于重置所有样式
        self.pen.setStyleSheet('')
        self.bs.setStyleSheet('')
        self.eraser.setStyleSheet('')
        self.backgrounderaser.setStyleSheet('')
        self.msk.setStyleSheet('')
        self.drawarrow.setStyleSheet('')
        self.drawcircle.setStyleSheet('')
        self.drawtext.setStyleSheet('')
        self.selectcolor_btn.setStyleSheet("")
        self.bucketpainter_btn.setStyleSheet("")
        self.backgroundrepair_btn.setStyleSheet("")
        self.perspective_cut_btn.setStyleSheet('')
        self.polygon_ss_btn.setStyleSheet('')
        self.text_box.clear()
        self.text_box.hide()
        self.choise_pix.hide()
        self.bucketpainter_tolerance.hide()
        for tool in self.painter_tools:
            if tool == r:
                self.painter_tools[tool] = 1
            else:
                self.painter_tools[tool] = 0
        self.update()

    def change_msk_fun(self):
        if self.painter_tools['drawpix_bs_on']:
            self.painter_tools['drawpix_bs_on'] = 0
            self.msk.setStyleSheet('')
            self.choise_pix.hide()
        else:
            self.change_tools_fun('drawpix_bs_on')
            self.msk.setStyleSheet('background-color:rgb(50,50,50)')
            self.choise_pix.show()
            self.Tipsshower.setText("材质画笔工具")
            self.setCursor(QCursor(self.paintlayer.pixpng.scaled(32, 32, Qt.KeepAspectRatio), 0, 32))

    def change_bs_fun(self):
        # print('cahngegbs')
        if self.painter_tools['drawrect_bs_on']:
            self.painter_tools['drawrect_bs_on'] = 0
            self.bs.setStyleSheet('')
        else:
            self.change_tools_fun('drawrect_bs_on')
            self.bs.setStyleSheet('background-color:rgb(50,50,50)')
            if self.tool_width > 6:
                self.size_slider.setValue(6)
            if self.alpha < 200:
                self.alpha_slider.setValue(255)
            self.Tipsshower.setText("矩形框工具")
            self.setCursor(QCursor(QPixmap(":/rect.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 30))

    def choise_drawpix_fun(self):
        self.Tipsshower.setText("设置材质")

        pic, l = QFileDialog.getOpenFileName(self, "选择图片", QStandardPaths.writableLocation(
            QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                              ";;all files(*.*)")
        if pic:
            self.paintlayer.pixpng = QPixmap(pic)
            self.choise_pix.setIcon(QIcon(pic))
    def search_in_which_screen(self):
        mousepos=Controller().position
        screens = QApplication.screens()
        secondscreen = QApplication.primaryScreen()
        for i in screens:
            rect=i.geometry().getRect()
            if mousepos[0]in range(rect[0],rect[0]+rect[2]) and mousepos[1]in range(rect[1],rect[1]+rect[3]):
                secondscreen = i
                break
        print("t", self.x(), QApplication.desktop().width(),QApplication.primaryScreen().geometry(),secondscreen.geometry(),mousepos)
        return secondscreen

    def screen_shot(self, pix=None):
        # 截屏函数,功能有二:当有传入pix时直接显示pix中的图片作为截屏背景,否则截取当前屏幕作为背景;前者用于重置所有修改
        # if PLATFORM_SYS=="darwin":
        self.sshoting = True
        t1 = time.process_time()
        if type(pix) is QPixmap:
            get_pix = pix
            self.init_parameters()
        else:
            self.setup()  # 初始化截屏
            if QApplication.desktop().screenCount()>1:
                sscreen=self.search_in_which_screen()
            else:
                sscreen=QApplication.primaryScreen()
            get_pix = sscreen.grabWindow(0)  # 截取屏幕
        pixmap = QPixmap(get_pix.width(), get_pix.height())
        pixmap.fill(Qt.transparent)  # 填充透明色,不然没有透明通道

        painter = QPainter(pixmap)
        # painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, get_pix)
        painter.end()  # 一定要end
        self.originalPix = pixmap.copy()
        self.setPixmap(pixmap)
        self.mask.setGeometry(0, 0, get_pix.width(), get_pix.height())
        self.mask.show()

        # self.paintlayer.__init__(self)
        # self.paintlayer.pixpng = ":/msk.jpg"
        self.paintlayer.setGeometry(0, 0, get_pix.width(), get_pix.height())
        self.paintlayer.setPixmap(QPixmap(get_pix.width(), get_pix.height()))
        self.paintlayer.pixmap().fill(Qt.transparent)  # 重点,不然不透明
        self.paintlayer.show()
        self.text_box.hide()
        self.botton_box.hide()
        # self.setGeometry(0, 0, pix.width(), pix.height())  # 全屏必须在所有控件画完再进行

        self.setWindowOpacity(1)
        # self.showNormal()
        self.showFullScreen()
        if type(pix) is not QPixmap:
            self.backup_ssid = 0
            self.backup_pic_list = [self.originalPix.copy()]

        self.init_ss_thread_fun(get_pix)
        self.paintlayer.pixpng = QPixmap(":/msk.jpg")
        self.text_box.setTextColor(self.pencolor)
        # 以下设置样式
        self.text_box.setStyleSheet("background-color: rgba(0, 0, 0, 10);")
        self.setStyleSheet("QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                           "QPushButton:hover{color:green;background-color:rgb(200,200,100);}"
                           "QGroupBox{border:none;}")
        self.painter_box.setStyleSheet("QPushButton{color:black;background-color:rgb(100,100,100);padding:-1px -1px;}"
                                       "QPushButton:hover{color:green;background-color:rgb(200,200,200);padding:1px 1px;}"
                                       "QGroupBox{border: 2px solid rgb(200,200,200);background-color:rgba(110,110,120,222);border-radius:6px;}"
                                       """QSlider{background-color: rgba(0,0,0,0); 
                                       	border-style: outset; 
                                       	border-radius: 2px;}
                                       QSlider::handle 
                                       {background: qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 white, stop:1 green);
                                       	width: 16px;
                                       	height: 5px;
                                       	margin: -5px 5px -5px 5px;
                                       	border-radius:5px; 
                                       	border: 3px solid #ffffff;
                                       }"""
                                       )
        print('sstime:', time.process_time() - t1)
        self.setFocus()
        self.setMouseTracking(True)
        self.activateWindow()
        self.raise_()
        self.update()
        QApplication.processEvents()

    def init_ss_thread_fun(self, get_pix):  # 后台初始化截屏线程,用于寻找所有智能选区

        self.x0 = self.y0 = 0
        self.x1 = QApplication.desktop().width()
        self.y1 = QApplication.desktop().height()
        self.mouse_posx = self.mouse_posy = -150
        self.qimg = get_pix.toImage()
        temp_shape = (self.qimg.height(), self.qimg.width(), 4)
        ptr = self.qimg.bits()
        ptr.setsize(self.qimg.byteCount())
        result = array(ptr, dtype=uint8).reshape(temp_shape)[..., :3]
        self.finder.img = result
        self.finder.find_contours_setup()
        QApplication.processEvents()

    def backup_shortshot(self):
        if self.backup_ssid != len(self.backup_pic_list) - 1:
            self.backup_pic_list = self.backup_pic_list[:self.backup_ssid + 1]
        while len(self.backup_pic_list) >= 10:
            self.backup_pic_list.pop(0)
        allpix = self.cutpic(save_as=3)
        self.backup_pic_list.append(QPixmap(allpix))
        self.backup_ssid = len(self.backup_pic_list) - 1
        print("备份动作", self.backup_ssid, len(self.backup_pic_list))
        # self.update()

    def last_step(self):
        if self.backup_ssid > 0:
            self.Tipsshower.setText("上一步")
            self.backup_ssid -= 1
            self.return_shortshot()
        else:
            self.Tipsshower.setText("没有上一步了")

    def next_step(self):
        if self.backup_ssid < len(self.backup_pic_list) - 1:
            self.Tipsshower.setText("下一步")
            self.backup_ssid += 1
            self.return_shortshot()
        else:
            self.Tipsshower.setText("没有下一步了")

    def return_shortshot(self):
        print("还原", self.backup_ssid, len(self.backup_pic_list))
        pix = self.backup_pic_list[self.backup_ssid]
        self.setPixmap(pix)
        self.paintlayer.pixmap().fill(Qt.transparent)
        self.paintlayer.update()
        self.update()

    def freeze_img(self):
        self.cutpic(save_as=2)
        self.parent.freeze_imgs.append(Freezer(None, self.final_get_img,
                                               min(self.x0, self.x1), min(self.y0, self.y1),
                                               len(self.parent.freeze_imgs)))
        if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
            self.parent.show()
        self.clear_and_hide()

    def ocr(self):
        self.Tipsshower.setText("正在识别...")
        self.shower.move(self.x1, self.y1)
        self.shower.show()
        self.shower.clear()
        self.cutpic(save_as=2)
        ocrimg_temp_path = 'j_temp/{}.png'.format("ocrtemp")
        self.final_get_img.save(ocrimg_temp_path)
        with open(ocrimg_temp_path, 'rb') as i:
            img = i.read()
        self.ocrthread = OcrimgThread('ocrtemp', img, 1)
        self.ocrthread.result_show_signal.connect(self.ocr_res_signalhandle)
        self.ocrthread.start()
        QApplication.processEvents()

    def ocr_res_signalhandle(self, text):
        self.shower.insertPlainText(text)
        jt = re.sub(r'[^\w]', '', text).replace('_', '')
        n = 0
        for i in text:
            if self.is_alphabet(i):
                n += 1
        if n / len(jt) > 0.4:
            print("is en")
            self.shower.tra()

    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False

    def cla(self):
        self.Tipsshower.setText("正在识别...")
        self.shower.move(self.x1, self.y1)
        self.shower.show()
        self.shower.clear()
        self.cutpic(save_as=2)
        ocrimg_temp_path = 'j_temp/{}.png'.format("ocrtemp")
        self.final_get_img.save(ocrimg_temp_path)
        with open(ocrimg_temp_path, 'rb') as i:
            img = i.read()
        options = {"top_num": 5}
        self.ocrthread = OcrimgThread(img, options, 2)
        self.ocrthread.result_show_signal.connect(self.shower.insertPlainText)
        self.ocrthread.start()
        QApplication.processEvents()

    def choice(self):  # 选区完毕后显示选择按钮的函数
        self.choicing = True

        botton_boxw = self.x1 + 5
        botton_boxh = self.y1 + 5
        dx = abs(self.x1 - self.x0)
        dy = abs(self.y1 - self.y0)
        x = QApplication.desktop().width()
        y = QApplication.desktop().height()
        if dx < self.botton_box.width() + 10:
            if max(self.x1, self.x0) + self.botton_box.width() > x:
                botton_boxw = min(self.x0, self.x1) - self.botton_box.width() - 5
            else:
                botton_boxw = max(self.x1, self.x0) + 5
        else:
            if self.x1 > self.x0:
                botton_boxw = self.x1 - self.botton_box.width() - 5
        if dy < self.botton_box.height() + 105:
            if max(self.y1, self.y0) + self.botton_box.height() + 20 > y:
                botton_boxh = min(self.y0, self.y1) - self.botton_box.height() - 5
            else:
                botton_boxh = max(self.y0, self.y1) + 5
        else:
            if self.y1 > self.y0:
                botton_boxh = self.y1 - self.botton_box.height() - 5
        self.botton_box.move(botton_boxw, botton_boxh)
        self.botton_box.show()

    def roll_shot(self):  # 滚动截屏
        x0 = min(self.x0, self.x1)
        y0 = min(self.y0, self.y1)
        x1 = max(self.x0, self.x1)
        y1 = max(self.y0, self.y1)
        roller = Splicing_shots()
        area = (x0, y0, x1 - x0, y1 - y0)
        if (x1 - x0) < 50 or (y1 - y0) < 50:
            self.showm_signal.emit('过小!')
            self.Tipsshower.setText("滚动面积过小!")
            return
        self.hide()
        roller.setup()

        try:
            if not self.parent.ssview:
                self.parent.init_ssview()
        except:
            print(sys.exc_info())
        exi = roller.roll_manager(area)
        print('roller end')
        if exi:
            print("未完成滚动截屏,用户退出")
            self.clear_and_hide()
            return

        self.final_get_img = QPixmap('j_temp/{}.png'.format(CONFIG_DICT["last_pic_save_name"]))
        if __name__ == '__main__':  # 当直接运行本文件时直接保存,测试用
            QApplication.clipboard().setPixmap(self.final_get_img)
            self.clear_and_hide()
            print("已复制到剪切板")
            return  # 直接运行本文件时到此结束
        self.manage_data()

    def cutpic(self, save_as=0):  # 裁剪图片
        """裁剪图片"""
        self.sshoting = False
        transparentpix = self.pixmap().copy()
        paintlayer = self.paintlayer.pixmap()
        painter = QPainter(transparentpix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, paintlayer)
        painter.end()  # 一定要end
        if save_as == 3:  # 油漆桶工具
            return transparentpix

        pix = QPixmap(transparentpix.width(), transparentpix.height())
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.drawPixmap(0, 0, transparentpix)
        p.end()

        x0 = min(self.x0, self.x1)
        y0 = min(self.y0, self.y1)
        x1 = max(self.x0, self.x1)
        y1 = max(self.y0, self.y1)
        w = x1 - x0
        h = y1 - y0

        # print(x0, y0, x1, y1)
        if (x1 - x0) < 1 or (y1 - y0) < 1:
            self.Tipsshower.setText("范围过小<1")
            return
        self.final_get_img = pix.copy(x0, y0, w, h)

        if save_as:
            if save_as == 1:
                path, l = QFileDialog.getSaveFileName(self, "保存为", QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                                      ";;all files(*.*)")
                if path:
                    print(path)
                    transparentpix.save(path)
                    self.clear_and_hide()
                else:
                    return
            elif save_as == 2:
                return
        if __name__ == '__main__':  # 当直接运行本文件时直接保存,测试用
            self.final_get_img.save('j_temp/{}.png'.format(CONFIG_DICT["last_pic_save_name"]))
            QApplication.clipboard().setPixmap(self.final_get_img)
            print("已复制到剪切板")
            self.clear_and_hide()
            return
        # 以下为作者软件的保存操作,懒得删了...
        if self.parent.setingarea:
            self.parent.setingarea = False
            if self.parent.samplingingid != -1:
                self.parent.controller_conditions[self.parent.samplingingid].sampling_update((x0, y0, w, h),
                                                                                             "j_temp/triggerpix0{}.png".format(
                                                                                                 self.parent.samplingingid))
                self.final_get_img.save("j_temp/triggerpix0{}.png".format(self.parent.samplingingid))
                self.parent.samplingingid = -1
                print('savetriggerpix')
            else:
                print('setting recarea')
                self.parent.recorder.x = x0
                self.parent.recorder.y = y0
                self.parent.recorder.w = (x1 - self.parent.recorder.x + 1) // 2 * 2
                self.parent.recorder.h = (y1 - self.parent.recorder.y + 1) // 2 * 2
                if self.parent.recorder.h == 0 or self.parent.recorder.w == 0:
                    self.showm_signal.emit('选择范围过小，请重新选择！')
                    if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                        self.parent.show()
                    self.parent.recorder.h = self.parent.recorder.w = 2
                    self.clear_and_hide()
                    return
            if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                self.parent.show()
            self.clear_and_hide()
        else:
            def save():
                CONFIG_DICT["last_pic_save_name"]="{}".format( str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime())))
                self.final_get_img.save('j_temp/{}.png'.format(CONFIG_DICT["last_pic_save_name"]))
                if not self.parent.bdocr:
                    try:
                        if self.parent.settings.value('screenshot/open_png', False, type=bool):
                            os.startfile('j_temp/{}.png'.format(CONFIG_DICT["last_pic_save_name"]))
                    except:
                        print("can't open", sys.exc_info())
                    try:
                        if self.parent.settings.value('screenshot/save_png', False, type=bool):
                            name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
                            p = QStandardPaths.writableLocation(
                                QStandardPaths.PicturesLocation) + '/JamPicture/screenshot/{}'.format(
                                str(time.strftime("%Y_%m_%d")))
                            if not os.path.exists(p): os.makedirs(p)

                            self.final_get_img.save(os.path.join(p, name + '.png'))
                    except:
                        print("can't save", sys.exc_info())
                print('saved')

            self.save_data_thread = Commen_Thread(save)
            self.save_data_thread.start()
            st = time.process_time()
            self.manage_data()
            print('managetime:', time.process_time() - st)

    def manage_data(self):
        """截屏完之后数据处理,不用可自己写"""
        if not self.parent.bdocr:
            if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                self.parent.screenshot()
                self.parent.ss_imgshower.setpic(self.final_get_img)

            clipboard = QApplication.clipboard()
            try:
                if self.parent.settings.value('screenshot/copy_type_ss', '图像数据', type=str) == '图像数据':
                    clipboard.setPixmap(self.final_get_img)
                    print('sava 图像数据')
                    self.showm_signal.emit('图像数据已复制到剪切板！')
                elif self.parent.settings.value('screenshot/copy_type_ss', '图像数据', type=str) == '图像文件':
                    data = QMimeData()
                    url = QUrl.fromLocalFile(os.getcwd()+'/j_temp/{}.png'.format(CONFIG_DICT["last_pic_save_name"]))
                    data.setUrls([url])
                    clipboard.setMimeData(data)
                    print('save url {}'.format(url))
                    self.showm_signal.emit('图像文件已复制到剪切板！')
            except:
                clipboard.setPixmap(self.final_get_img)
                self.showm_signal.emit('图像数据已复制到剪切板！')
        elif self.parent.bdocr:
            try:
                self.save_data_thread.wait()
                self.parent.BaiduOCR()
            except:
                print(sys.exc_info(), 1822)

        # self.save_data_thread.wait()
        # self.clear()
        self.clear_and_hide()

        # self.close()

    def cut_polygonpng(self):
        allpix = self.cutpic(save_as=3)
        self.qimg = allpix.toImage()
        temp_shape = (self.qimg.height(), self.qimg.width(), 4)
        ptr = self.qimg.bits()
        ptr.setsize(self.qimg.byteCount())
        cv2img = array(ptr, dtype=uint8).reshape(temp_shape)[..., :3]
        polygoncv2pic = cut_polypng(cv2img, self.polygon_ss_pointlist)
        cv2.imwrite('j_temp/{}.png'.format(CONFIG_DICT["last_pic_save_name"]), polygoncv2pic)
        self.polygon_ss_pointlist = []
        QApplication.clipboard().setImage(QImage('j_temp/{}.png'.format(CONFIG_DICT["last_pic_save_name"])))
        self.showm_signal.emit("已复制到剪切板")
        self.polygon_ss_btn.setStyleSheet('')
        self.clear_and_hide()

    def mouseDoubleClickEvent(self, e):  # 双击
        if e.button() == Qt.LeftButton:
            if self.painter_tools["polygon_ss_on"]:
                self.change_tools_fun("")
                print("裁剪点", self.polygon_ss_pointlist)
                self.cut_polygonpng()
            print("左键双击")

    # 鼠标点击事件
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:  # 按下了左键
            self.left_button_push = True
            if 1 in self.painter_tools.values():  # 如果有绘图工具打开了,说明正在绘图
                if self.painter_tools['drawrect_bs_on']:
                    # print("ch",self.drawrect_pointlist)
                    self.drawrect_pointlist = [[event.x(), event.y()], [-2, -2], 0]
                elif self.painter_tools['drawarrow_on']:
                    self.drawarrow_pointlist = [[event.x(), event.y()], [-2, -2], 0]
                    # self.drawarrow_pointlist[0] = [event.x(), event.y()]
                elif self.painter_tools['drawcircle_on']:
                    self.drawcircle_pointlist = [[event.x(), event.y()], [-2, -2], 0]
                    # self.drawcircle_pointlist[0] = [event.x(), event.y()]
                elif self.painter_tools['drawtext_on']:
                    self.text_box.move(event.x(), event.y())
                    self.drawtext_pointlist.append([event.x(), event.y()])
                    self.text_box.setFont(QFont('', self.tool_width))
                    self.text_box.setTextColor(self.pencolor)
                    self.text_box.textAreaChanged()
                    self.text_box.show()
                    self.text_box.setFocus()
                elif self.painter_tools['selectcolor_on']:
                    allpix = self.cutpic(save_as=3)
                    self.qimg = allpix.toImage()
                    color = self.qimg.pixelColor(event.x(), event.y())
                    self.pencolor = color
                    self.alpha_slider.setValue(255)
                    self.change_tools_fun("")
                elif self.painter_tools['bucketpainter_on']:  # 油漆桶工具
                    allpix = self.cutpic(save_as=3)
                    self.qimg = allpix.toImage()
                    temp_shape = (self.qimg.height(), self.qimg.width(), 4)
                    ptr = self.qimg.bits()
                    ptr.setsize(self.qimg.byteCount())
                    ci = array(ptr, dtype=uint8).reshape(temp_shape)[..., :3]

                    cv2img = image_fill(cv2.cvtColor(ci, cv2.COLOR_RGB2BGR), event.x(), event.y(),
                                        (self.pencolor.red(), self.pencolor.green(), self.pencolor.blue()),
                                        self.bucketpainter_tolerance.value())
                    height, width, depth = cv2img.shape
                    pix = QPixmap.fromImage(QImage(cv2img.data, width, height, width * depth, QImage.Format_RGB888))
                    tpix = QPixmap(pix.width(), pix.height())
                    tpix.fill(Qt.transparent)
                    p = QPainter(tpix)
                    p.drawPixmap(0, 0, pix)
                    p.end()
                    self.setPixmap(tpix)
                    self.paintlayer.pixmap().fill(Qt.transparent)
                    self.Tipsshower.setText("已填充并合并图层!", color=QColor(Qt.green))
                    allpix = self.cutpic(save_as=3)
                    self.qimg = allpix.toImage()
                elif self.painter_tools["polygon_ss_on"]:

                    if len(self.polygon_ss_pointlist) and self.polygon_ss_pointlist[0][0] - 10 < event.x() < \
                            self.polygon_ss_pointlist[0][0] + 10 and self.polygon_ss_pointlist[0][
                        1] - 10 < event.y() < self.polygon_ss_pointlist[0][1] + 10:
                        print("相同点结束")
                        self.setCursor(QCursor(QPixmap(":/smartcursor.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                        self.cut_polygonpng()
                    else:
                        self.setCursor(QCursor(QPixmap(":/polygon_ss.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                        self.polygon_ss_pointlist.append([event.x(), event.y()])

                elif self.painter_tools["perspective_cut_on"]:
                    self.setCursor(QCursor(QPixmap(":/perspective.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                    self.perspective_cut_pointlist.append([event.x(), event.y()])
                    if len(self.perspective_cut_pointlist) >= 4:
                        allpix = self.cutpic(save_as=3)
                        self.qimg = allpix.toImage()
                        temp_shape = (self.qimg.height(), self.qimg.width(), 4)
                        ptr = self.qimg.bits()
                        ptr.setsize(self.qimg.byteCount())
                        cv2img = array(ptr, dtype=uint8).reshape(temp_shape)[..., :3]
                        res = cut_mutipic(cv2img, self.perspective_cut_pointlist)
                        cv2.imwrite("perspective_cut.jpg", res)
                        QApplication.clipboard().setImage(QImage("perspective_cut.jpg"))
                        # cv2.imwrite("respng.png",res)
                        self.Tipsshower.setText("已复制到剪切板!")
                        print("四个点", self.perspective_cut_pointlist)
                        self.setCursor(Qt.ArrowCursor)
                        self.perspective_cut_pointlist = []
                        self.change_tools_fun("")
                        self.choicing = False
                        self.finding_rect = True
            else:  # 否则说明正在选区或移动选区
                r = 0
                x0 = min(self.x0, self.x1)
                x1 = max(self.x0, self.x1)
                y0 = min(self.y0, self.y1)
                y1 = max(self.y0, self.y1)
                my = (y1 + y0) // 2
                mx = (x1 + x0) // 2
                # print(x0, x1, y0, y1, mx, my, event.x(), event.y())
                # 以下为判断点击在哪里
                if not self.finding_rect and (self.x0 - 8 < event.x() < self.x0 + 8) and (
                        my - 8 < event.y() < my + 8 or y0 - 8 < event.y() < y0 + 8 or y1 - 8 < event.y() < y1 + 8):
                    self.move_x0 = True
                    r = 1

                elif not self.finding_rect and (self.x1 - 8 < event.x() < self.x1 + 8) and (
                        my - 8 < event.y() < my + 8 or y0 - 8 < event.y() < y0 + 8 or y1 - 8 < event.y() < y1 + 8):
                    self.move_x1 = True
                    r = 1
                    # print('x1')

                elif not self.finding_rect and (self.y0 - 8 < event.y() < self.y0 + 8) and (
                        mx - 8 < event.x() < mx + 8 or x0 - 8 < event.x() < x0 + 8 or x1 - 8 < event.x() < x1 + 8):
                    self.move_y0 = True
                    print('y0')
                elif not self.finding_rect and self.y1 - 8 < event.y() < self.y1 + 8 and (
                        mx - 8 < event.x() < mx + 8 or x0 - 8 < event.x() < x0 + 8 or x1 - 8 < event.x() < x1 + 8):
                    self.move_y1 = True

                elif (x0 + 8 < event.x() < x1 - 8) and (
                        y0 + 8 < event.y() < y1 - 8) and not self.finding_rect:
                    # if not self.finding_rect:
                    self.move_rect = True
                    self.setCursor(Qt.SizeAllCursor)
                    self.bx = abs(max(self.x1, self.x0) - event.x())
                    self.by = abs(max(self.y1, self.y0) - event.y())
                else:
                    self.NpainterNmoveFlag = True  # 没有绘图没有移动还按下了左键,说明正在选区,标志变量
                    # if self.finding_rect:
                    #     self.rx0 = event.x()
                    #     self.ry0 = event.y()
                    # else:
                    self.rx0 = event.x()  # 记录下点击位置
                    self.ry0 = event.y()
                    if self.x1 == -50:
                        self.x1 = event.x()
                        self.y1 = event.y()

                    # print('re')
                if r:  # 判断是否点击在了对角线上
                    if (self.y0 - 8 < event.y() < self.y0 + 8) and (
                            x0 - 8 < event.x() < x1 + 8):
                        self.move_y0 = True
                        # print('y0')
                    elif self.y1 - 8 < event.y() < self.y1 + 8 and (
                            x0 - 8 < event.x() < x1 + 8):
                        self.move_y1 = True
                        # print('y1')
            if self.finding_rect:
                self.finding_rect = False
                # self.finding_rectde = True
            self.botton_box.hide()
            self.update()
        elif event.button() == Qt.RightButton:  # 右键
            self.setCursor(Qt.ArrowCursor)
            if 1 in self.painter_tools.values():  # 退出绘图工具
                if self.painter_tools["selectcolor_on"]:
                    self.Tipsshower.setText("取消取色器")
                    self.choice_clor_btn.setStyleSheet(
                        'background-color:{0};'.format(self.pencolor.name()))  # 还原choiceclor显示的颜色
                if self.painter_tools["perspective_cut_on"] and len(self.perspective_cut_pointlist) > 0:
                    self.setCursor(QCursor(QPixmap(":/perspective.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                    self.perspective_cut_pointlist.pop()
                    # if not len(self.perspective_cut_pointlist):
                    #     self.choicing = False
                    #     self.finding_rect = True
                elif self.painter_tools["polygon_ss_on"] and len(self.polygon_ss_pointlist) > 0:
                    self.setCursor(QCursor(QPixmap(":/polygon_ss.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                    self.polygon_ss_pointlist.pop()
                    # if not len(self.polygon_ss_pointlist):
                    #     self.choicing = False
                    #     self.finding_rect = True
                else:
                    self.choicing = False
                    self.finding_rect = True
                    self.shower.hide()
                    self.change_tools_fun("")

            elif self.choicing:  # 退出选定的选区
                self.botton_box.hide()
                self.choicing = False
                self.finding_rect = True
                self.shower.hide()
                self.x0 = self.y0 = self.x1 = self.y1 = -50
            else:  # 退出截屏
                try:
                    if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                        self.parent.show()

                    self.parent.bdocr = False
                except:
                    print(sys.exc_info(), 2051)
                self.clear_and_hide()
            self.update()

    # 鼠标释放事件
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.left_button_push = False
            if 1 in self.painter_tools.values():  # 绘图工具松开
                if self.painter_tools['pen_on']:
                    self.pen_pointlist.append([-2, -2])
                elif self.painter_tools['drawpix_bs_on']:
                    self.drawpix_pointlist.append([-2, -2])
                elif self.painter_tools['repairbackground_on']:
                    self.repairbackground_pointlist.append([-2, -2])
                elif self.painter_tools['drawrect_bs_on']:
                    self.drawrect_pointlist[1] = [event.x(), event.y()]
                    self.drawrect_pointlist[2] = 1
                elif self.painter_tools['drawarrow_on']:
                    self.drawarrow_pointlist[1] = [event.x(), event.y()]
                    self.drawarrow_pointlist[2] = 1
                elif self.painter_tools['drawcircle_on']:
                    self.drawcircle_pointlist[1] = [event.x(), event.y()]
                    self.drawcircle_pointlist[2] = 1
                elif self.painter_tools['eraser_on']:
                    self.eraser_pointlist.append([-2, -2])
                elif self.painter_tools['backgrounderaser_on']:
                    self.backgrounderaser_pointlist.append([-2, -2])
                if not self.painter_tools["perspective_cut_on"] and not self.painter_tools["polygon_ss_on"]:
                    self.backup_shortshot()
            else:  # 调整选区松开
                self.setCursor(Qt.ArrowCursor)
            self.NpainterNmoveFlag = False  # 选区结束标志置零
            self.move_rect = self.move_y0 = self.move_x0 = self.move_x1 = self.move_y1 = False
            if not self.painter_tools["perspective_cut_on"] and not self.painter_tools["polygon_ss_on"]:
                self.choice()
            # self.btn1.show()
            self.update()

    # 鼠标滑轮事件
    def wheelEvent(self, event):
        if self.isVisible():
            angleDelta = event.angleDelta() / 8
            dy = angleDelta.y()
            # print(dy)
            if self.change_alpha:  # 正在调整透明度
                if dy > 0 and self.alpha < 254:
                    self.alpha_slider.setValue(self.alpha_slider.value() + 2)
                elif dy < 0 and self.alpha > 2:
                    self.alpha_slider.setValue(self.alpha_slider.value() - 2)
                self.Tipsshower.setText("透明度值{}".format(self.alpha))

            else:  # 否则是调节画笔大小
                # angleDelta = event.angleDelta() / 8
                # dy = angleDelta.y()
                # print(dy)
                if dy > 0:
                    self.tool_width += 1
                elif self.tool_width > 1:
                    self.tool_width -= 1
                self.size_slider.setValue(self.tool_width)
                self.Tipsshower.setText("大小{}px".format(self.tool_width))

                # if 1 in self.painter_tools.values():

                if self.painter_tools['drawtext_on']:
                    # self.text_box.move(event.x(), event.y())
                    # self.drawtext_pointlist.append([event.x(), event.y()])
                    self.text_box.setFont(QFont('', self.tool_width))
                    # self.text_box.setTextColor(self.pencolor)
                    self.text_box.textAreaChanged()
            self.update()

    # 鼠标移动事件
    def mouseMoveEvent(self, event):
        # print(self.isVisible(), 12121, self.finding_rect, self.smartcursor_on, self.isActiveWindow(), self.isHidden())
        if self.isVisible():
            self.mouse_posx = event.x()  # 先储存起鼠标位置,用于画笔等的绘图计算
            self.mouse_posy = event.y()
            if self.finding_rect and self.smartcursor_on:  # 如果允许智能选取并且在选选区步骤
                self.x0, self.y0, self.x1, self.y1 = self.finder.find_targetrect((self.mouse_posx, self.mouse_posy))
                self.setCursor(QCursor(QPixmap(":/smartcursor.png").scaled(32, 32, Qt.KeepAspectRatio), 16, 16))
                # print(self.x0, self.y0, self.x1, self.y1 )
                # print("findtime {}".format(time.process_time()-st))
            elif 1 in self.painter_tools.values():  # 如果有绘图工具已经被选择,说明正在绘图
                self.paintlayer.px = event.x()
                self.paintlayer.py = event.y()
                if self.left_button_push:
                    if self.painter_tools['pen_on']:
                        self.pen_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools['drawpix_bs_on']:
                        self.drawpix_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools['repairbackground_on']:
                        self.repairbackground_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools['drawrect_bs_on']:
                        self.drawrect_pointlist[1] = [event.x(), event.y()]
                    elif self.painter_tools['drawarrow_on']:
                        self.drawarrow_pointlist[1] = [event.x(), event.y()]
                    elif self.painter_tools['drawcircle_on']:
                        self.drawcircle_pointlist[1] = [event.x(), event.y()]
                    elif self.painter_tools['eraser_on']:
                        self.eraser_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools['backgrounderaser_on']:
                        # print('bakpoint')
                        self.backgrounderaser_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools["polygon_ss_on"]:
                        self.polygon_ss_pointlist.append([event.x(), event.y()])
                # self.update()
                if self.painter_tools['pen_on']:
                    self.setCursor(QCursor(QPixmap(":/pen.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['drawpix_bs_on']:
                    self.setCursor(QCursor(self.paintlayer.pixpng.scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['repairbackground_on']:
                    self.setCursor(QCursor(QPixmap(":/backgroundrepair.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 26))
                elif self.painter_tools['drawrect_bs_on']:
                    self.setCursor(QCursor(QPixmap(":/rect.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 30))
                elif self.painter_tools['drawarrow_on']:
                    self.setCursor(QCursor(QPixmap(":/arrowicon.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['drawcircle_on']:
                    self.setCursor(QCursor(QPixmap(":/circle.png").scaled(32, 32, Qt.KeepAspectRatio), 16, 16))
                elif self.painter_tools['drawtext_on']:
                    self.setCursor(QCursor(QPixmap(":/texticon.png").scaled(16, 16, Qt.KeepAspectRatio), 0, 0))
                elif self.painter_tools['eraser_on']:
                    self.setCursor(QCursor(QPixmap(":/eraser.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['backgrounderaser_on']:
                    self.setCursor(QCursor(QPixmap(":/backgrounderaser.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['selectcolor_on']:
                    color = self.qimg.pixelColor(event.x(), event.y())
                    self.choice_clor_btn.setStyleSheet('background-color:{0};'.format(color.name()))
                    self.setCursor(QCursor(QPixmap(":/colorsampler.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 31))
                elif self.painter_tools['bucketpainter_on']:
                    self.setCursor(QCursor(QPixmap(":/yqt.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['perspective_cut_on']:
                    self.setCursor(QCursor(QPixmap(":/perspective.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['polygon_ss_on']:
                    if len(self.polygon_ss_pointlist) and self.polygon_ss_pointlist[0][0] - 10 < event.x() < \
                            self.polygon_ss_pointlist[0][0] + 10 and self.polygon_ss_pointlist[0][
                        1] - 10 < event.y() < self.polygon_ss_pointlist[0][1] + 10:
                        self.setCursor(QCursor(QPixmap(":/smartcursor.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                    else:
                        self.setCursor(QCursor(QPixmap(":/polygon_ss.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))

            else:  # 不在绘画
                minx = min(self.x0, self.x1)
                maxx = max(self.x0, self.x1)
                miny = min(self.y0, self.y1)
                maxy = max(self.y0, self.y1)  # 以上取选区的最小值和最大值
                my = (maxy + miny) // 2
                mx = (maxx + minx) // 2  # 取中间值
                if ((minx - 8 < event.x() < minx + 8) and (miny - 8 < event.y() < miny + 8)) or \
                        ((maxx - 8 < event.x() < maxx + 8) and (maxy - 8 < event.y() < maxy + 8)):
                    self.setCursor(Qt.SizeFDiagCursor)
                elif ((minx - 8 < event.x() < minx + 8) and (maxy - 8 < event.y() < maxy + 8)) or \
                        ((maxx - 8 < event.x() < maxx + 8) and (miny - 8 < event.y() < miny + 8)):
                    self.setCursor(Qt.SizeBDiagCursor)
                elif (self.x0 - 8 < event.x() < self.x0 + 8) and (
                        my - 8 < event.y() < my + 8 or miny - 8 < event.y() < miny + 8 or maxy - 8 < event.y() < maxy + 8):
                    self.setCursor(Qt.SizeHorCursor)
                elif (self.x1 - 8 < event.x() < self.x1 + 8) and (
                        my - 8 < event.y() < my + 8 or miny - 8 < event.y() < miny + 8 or maxy - 8 < event.y() < maxy + 8):
                    self.setCursor(Qt.SizeHorCursor)
                elif (self.y0 - 8 < event.y() < self.y0 + 8) and (
                        mx - 8 < event.x() < mx + 8 or minx - 8 < event.x() < minx + 8 or maxx - 8 < event.x() < maxx + 8):
                    self.setCursor(Qt.SizeVerCursor)
                elif (self.y1 - 8 < event.y() < self.y1 + 8) and (
                        mx - 8 < event.x() < mx + 8 or minx - 8 < event.x() < minx + 8 or maxx - 8 < event.x() < maxx + 8):
                    self.setCursor(Qt.SizeVerCursor)
                elif (minx + 8 < event.x() < maxx - 8) and (
                        miny + 8 < event.y() < maxy - 8):
                    self.setCursor(Qt.SizeAllCursor)
                elif self.move_x1 or self.move_x0 or self.move_y1 or self.move_y0:  # 再次判断防止光标抖动
                    b = (self.x1 - self.x0) * (self.y1 - self.y0) > 0
                    if (self.move_x0 and self.move_y0) or (self.move_x1 and self.move_y1):
                        if b:
                            self.setCursor(Qt.SizeFDiagCursor)
                        else:
                            self.setCursor(Qt.SizeBDiagCursor)
                    elif (self.move_x1 and self.move_y0) or (self.move_x0 and self.move_y1):
                        if b:
                            self.setCursor(Qt.SizeBDiagCursor)
                        else:
                            self.setCursor(Qt.SizeFDiagCursor)
                    elif (self.move_x0 or self.move_x1) and not (self.move_y0 or self.move_y1):
                        self.setCursor(Qt.SizeHorCursor)
                    elif not (self.move_x0 or self.move_x1) and (self.move_y0 or self.move_y1):
                        self.setCursor(Qt.SizeVerCursor)
                    elif self.move_rect:
                        self.setCursor(Qt.SizeAllCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
                # 以上几个ifelse都是判断鼠标移动的位置和选框的关系然后设定光标形状
                # print(11)
                if self.NpainterNmoveFlag:  # 如果没有在绘图也没在移动(调整)选区,在选区,则不断更新选区的数值
                    # self.btn1.hide()
                    # self.btn2.hide()
                    self.x1 = event.x()  # 储存当前位置到self.x1下同
                    self.y1 = event.y()
                    self.x0 = self.rx0  # 鼠标按下时记录的坐标,下同
                    self.y0 = self.ry0
                    if self.y1 > self.y0:  # 下面是边界修正,由于选框占用了一个像素,否则有误差
                        self.y1 += 1
                    else:
                        self.y0 += 1
                    if self.x1 > self.x0:
                        self.x1 += 1
                    else:
                        self.x0 += 1
                else:  # 说明在移动或者绘图,不过绘图没有什么处理的,下面是处理移动/拖动选区
                    if self.move_x0:  # 判断拖动标志位,下同
                        self.x0 = event.x()
                    elif self.move_x1:
                        self.x1 = event.x()
                    if self.move_y0:
                        self.y0 = event.y()
                    elif self.move_y1:
                        self.y1 = event.y()
                    elif self.move_rect:  # 拖动选框
                        dx = abs(self.x1 - self.x0)
                        dy = abs(self.y1 - self.y0)
                        if self.x1 > self.x0:
                            self.x1 = event.x() + self.bx
                            self.x0 = self.x1 - dx
                        else:
                            self.x0 = event.x() + self.bx
                            self.x1 = self.x0 - dx

                        if self.y1 > self.y0:
                            self.y1 = event.y() + self.by
                            self.y0 = self.y1 - dy
                        else:
                            self.y0 = event.y() + self.by
                            self.y1 = self.y0 - dy
            # print("movetime{}".format(time.process_time()-st))
            self.update()  # 更新界面
        # QApplication.processEvents()

    def keyPressEvent(self, e):  # 按键按下,没按一个键触发一次
        super(Slabel, self).keyPressEvent(e)
        # self.pixmap().save(temp_path + '/aslfdhds.png')
        if e.key() == Qt.Key_Escape:  # 退出
            self.clear_and_hide()
        elif e.key() == Qt.Key_Control:  # 按住ctrl,更改透明度标志位置一
            print("cahnge")
            self.change_alpha = True

        elif self.change_alpha:  # 如果已经按下了ctrl
            if e.key() == Qt.Key_S:  # 还按下了s,说明是保存,ctrl+s
                self.cutpic(1)
            elif not self.painter_tools["polygon_ss_on"] and not self.painter_tools["perspective_cut_on"]:
                if e.key() == Qt.Key_Z:  # 前一步
                    self.last_step()
                elif e.key() == Qt.Key_Y:  # 后一步
                    self.next_step()

    def keyReleaseEvent(self, e) -> None:  # 按键松开
        super(Slabel, self).keyReleaseEvent(e)
        if e.key() == Qt.Key_Control:
            self.change_alpha = False

    def clear_and_hide(self):  # 清理退出
        print("clear and hide")
        if PLATFORM_SYS == "darwin":  # 如果系统为macos
            print("drawin hide")
            self.setWindowOpacity(0)
            self.showNormal()
        self.hide()
        self.clearotherthread = Commen_Thread(self.clear_and_hide_thread)
        self.clearotherthread.start()

    def clear_and_hide_thread(self):  # 后台等待线程
        self.close_signal.emit()
        try:
            self.save_data_thread.wait()
        except:
            print(sys.exc_info(), 2300)

    # 绘制事件
    def paintEvent(self, event):  # 绘图函数,每次调用self.update时触发
        super().paintEvent(event)
        if self.on_init:
            print('oninit return')
            return
        pixPainter = QPainter(self.pixmap())  # 画笔
        while len(self.backgrounderaser_pointlist):  # 背景橡皮擦工具有值,则说明正在使用背景橡皮擦
            # print(self.backgrounderaser_pointlist)
            pixPainter.setRenderHint(QPainter.Antialiasing)
            pixPainter.setBrush(QColor(0, 0, 0, 0))
            pixPainter.setPen(Qt.NoPen)
            # pixPainter.setPen(Qt.NoPen)
            pixPainter.setCompositionMode(QPainter.CompositionMode_Clear)
            new_pen_point = self.backgrounderaser_pointlist.pop(0)
            if self.old_pen is None:
                self.old_pen = new_pen_point
                continue
            if self.old_pen[0] != -2 and new_pen_point[0] != -2:
                pixPainter.drawEllipse(new_pen_point[0] - self.tool_width / 2,
                                       new_pen_point[1] - self.tool_width / 2,
                                       self.tool_width, self.tool_width)
                if abs(new_pen_point[0] - self.old_pen[0]) > 3 or abs(
                        new_pen_point[1] - self.old_pen[1]) > 3:
                    interpolateposs = get_line_interpolation(new_pen_point[:], self.old_pen[:])
                    if interpolateposs is not None:
                        for pos in interpolateposs:
                            x, y = pos
                            pixPainter.drawEllipse(x - self.tool_width / 2,
                                                   y - self.tool_width / 2,
                                                   self.tool_width, self.tool_width)

            self.old_pen = new_pen_point

        while len(self.repairbackground_pointlist):  # 背景修复画笔有值
            brush = QBrush(self.pencolor)

            brush.setTexture(self.originalPix)
            pixPainter.setBrush(brush)
            pixPainter.setPen(Qt.NoPen)
            new_pen_point = self.repairbackground_pointlist.pop(0)
            if self.old_pen is None:
                self.old_pen = new_pen_point
                continue
            if self.old_pen[0] != -2 and new_pen_point[0] != -2:
                pixPainter.drawEllipse(new_pen_point[0] - self.tool_width / 2,
                                       new_pen_point[1] - self.tool_width / 2,
                                       self.tool_width, self.tool_width)
                if abs(new_pen_point[0] - self.old_pen[0]) > 1 or abs(
                        new_pen_point[1] - self.old_pen[1]) > 1:
                    interpolateposs = get_line_interpolation(new_pen_point[:], self.old_pen[:])
                    if interpolateposs is not None:
                        for pos in interpolateposs:
                            x, y = pos
                            pixPainter.drawEllipse(x - self.tool_width / 2,
                                                   y - self.tool_width / 2,
                                                   self.tool_width, self.tool_width)

            self.old_pen = new_pen_point
        pixPainter.end()


if __name__ == '__main__':
    class testwin(QWidget):  # 随便设置的一个ui,
        def __init__(self):
            super(testwin, self).__init__()
            self.freeze_imgs = []  # 储存固定截屏在屏幕上的数组
            btn = QPushButton("截屏", self)
            btn.setGeometry(20, 20, 60, 30)
            btn.setShortcut("Alt+Z")
            btn.clicked.connect(self.ss)
            self.temppos = [500, 100]
            self.s = Slabel(self)
            self.s.close_signal.connect(self.ss_end)  # 截屏结束信号连接
            self.resize(300, 200)

        def ss(self):  # 截屏开始
            self.setWindowOpacity(0)  # 设置透明度而不是hide是因为透明度更快
            self.temppos = [self.x(), self.y()]
            self.move(QApplication.desktop().width(), QApplication.desktop().height())
            self.s.screen_shot()
            # self.hide()

        def ss_end(self):
            del self.s
            self.move(self.temppos[0], self.temppos[1])
            self.show()
            self.setWindowOpacity(1)
            self.raise_()
            gc.collect()
            print(gc.isenabled(), gc.get_count(), gc.get_freeze_count())
            print('cleard')
            self.s = Slabel(self)
            self.s.close_signal.connect(self.ss_end)

        def show(self) -> None:
            super(testwin, self).show()
            print("ss show")


    app = QApplication(sys.argv)
    s = testwin()
    s.show()
    sys.exit(app.exec_())
