import math
import operator
import os
import sys
import time
from functools import reduce
import time

import cv2
import os
import numpy as np
from numpy import array, uint8

import crc16

from PIL import Image
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QApplication
from pynput import mouse
from pynput.mouse import Controller as MouseController


class Splicing_shots(object):
    def __init__(self):
        # self.init_splicing_shots_thread = Commen_Thread(self.init_splicing_shots)
        # self.init_splicing_shots_thread.start()
        self.init_splicing_shots()
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.setup)

    def init_splicing_shots(self):
        """后台初始化"""
        self.img = []
        self.pos_list = []
        self.crc16_list = []
        self.img_list = []
        self.images_data_line_list = []
        self.img_width = 0
        self.img_height = 0
        self.compare_row = 50
        self.cut_width = 0
        self.rate = 0.85
        self.roll_speed = 5
        self.min_head = 0
        self.left_border = 0
        self.right_border = 0
        self.head_pos = {}
        self.maybe_errorlist = []
        self.in_rolling = False
        self.arrange = 0
        self.max_arrange = 999
        if not os.path.exists("j_temp"):
            os.mkdir("j_temp")

    def setup(self):
        """清理&初始化"""
        if self.clear_timer.isActive():
            self.clear_timer.stop()
            print('clear')
        self.img = []
        self.img_list = []
        self.images_data_line_list = []
        self.img_width = 0
        self.img_height = 0
        self.compare_row = 50
        self.cut_width = 0
        self.rate = 0.85
        self.roll_speed = 3
        self.min_head = 0
        self.left_border = 0
        self.right_border = 0
        self.head_pos = {}
        self.maybe_errorlist = []
        self.in_rolling = False
        self.arrange = 0
        self.max_arrange = 999
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.setup)

    def find_the_same_head_to_remove(self, s1, s2):
        """寻找相同的头部(上边界)"""
        # if self.images_data
        line = 0
        for i in range(len(s1)):
            if s1[i] == s2[i]:
                line += 1
            else:
                break
        return line

    def find_pos(self, s1, s2):
        # m = [[0 for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]
        mmax = 0
        p = (0, 0)
        sameline = self.find_the_same_head_to_remove(s1, s2)
        for i in range(sameline, len(s1) - 50):
            t = 0
            for j in range(sameline, sameline + 50):
                if s1[i + j - sameline] == s2[j]:
                    t += 1
                    if t > mmax:
                        mmax = t
                        p = (mmax, i)

        return p[0],p[1],sameline

    def crc16_run(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        crc16_list = []
        for l in gray:
            crc16_list.append(crc16.crc16xmodem(l))
        return crc16_list

    def efind_the_pos(self):
        """在滚动的同时后台寻找拼接点"""
        while self.in_rolling or self.arrange < self.max_arrange:  # 如果正在截屏或截屏没有处理完
            print(self.arrange, '  max:', self.max_arrange, len(self.img_list))
            self.arrange += 1
            time.sleep(0.1)
            w=self.img_list[0].shape[1]
            crc1 = self.crc16_run(self.img_list[self.arrange - 1][:,50:w+50,:])
            crc2 = self.crc16_run(self.img_list[self.arrange][:,50:w+50,:])
            p = self.find_pos(crc1, crc2)
            self.pos_list.append(p)
            print(p)
            # self.find_the_same_head_to_remove()

    def qpix_to_cv2(self, get_pix):
        """qpixmap 转cv2格式"""
        qimg = get_pix.toImage()
        temp_shape = (qimg.height(), qimg.bytesPerLine() * 8 // qimg.depth())
        temp_shape += (4,)
        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        result = array(ptr, dtype=uint8).reshape(temp_shape)
        result = result[..., :3]
        return result

    def merge_all(self):
        """根据拼接点拼接所有图片"""
        final_pic =[]
        final_pic.extend(self.img_list[0])
        # print(self.pos_list,len(self.pos_list),len(self.img_list))
        h=0
        for i in range(len(self.pos_list)):
            pos=self.pos_list[i]
            imgpart=self.img_list[i+1]
            print(pos,i)
            head=pos[1]
            h+=head
            imgpart=imgpart[pos[2]:,:,:]
            final_pic=final_pic[:h]
            final_pic.extend(imgpart)
        cv2.imwrite('final.jpg', np.array(final_pic))


        print('saved in j_temp/jam_outputfile.png')

    def pHash(self, img):
        """感知哈希算法(pHash)"""
        # 缩放32*32
        img = cv2.resize(img, (32, 32))  # , interpolation=cv2.INTER_CUBIC

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 将灰度图转为浮点型，再进行dct变换
        dct = cv2.dct(np.float32(gray))
        # opencv实现的掩码操作
        dct_roi = dct[0:8, 0:8]

        hash = []
        avreage = np.mean(dct_roi)
        for i in range(dct_roi.shape[0]):
            for j in range(dct_roi.shape[1]):
                if dct_roi[i, j] > avreage:
                    hash.append(1)
                else:
                    hash.append(0)
        return hash

    def is_same(self, img1, img2):
        """简单判断两幅图片是否相同,用于停止滚动截屏,速度非常快!"""
        hash1 = self.pHash(img1)
        hash2 = self.pHash(img2)
        n = 0
        # hash长度不同则返回-1代表传参出错
        if len(hash1) != len(hash2):
            return -1
        # 遍历判断
        for i in range(len(hash1)):
            # 不相等则n计数+1，n最终为相似度
            if hash1[i] != hash2[i]:
                n = n + 1
        print('相似度', n)
        if n < 1:
            return True
        else:
            return False

    def auto_roll(self, area):
        """自动滚动截屏,总函数"""
        x, y, w, h = area
        self.img_width = w
        self.img_height = h
        speed = round(1 / self.roll_speed, 2)
        screen = QApplication.primaryScreen()
        controler = MouseController()
        find_pos = Commen_Thread(self.efind_the_pos)
        self.in_rolling = True
        i = 0
        controler.position = (area[0] + int(area[2] / 2), area[1] + int(area[3] / 2))
        while self.in_rolling:
            pix = screen.grabWindow(QApplication.desktop().winId(), x, y, w, h)  # 区域截屏获取图像pixmap
            img = self.qpix_to_cv2(pix)  # 将qt的pixmap转为pil模块的img对象
            self.img_list.append(img)  # 储存图片的列表
            if i >= 1:
                if self.is_same(self.img_list[i - 1], self.img_list[i]):  # 每帧检查是否停止(图片是否相同)
                    self.in_rolling = False
                    i += 1
                    break
                if i == 5:  # 图片大于5张才开始寻找拼接点
                    find_pos.start()
            controler.scroll(dx=0, dy=-3)  # 滚动屏幕
            time.sleep(0.1)  # 速度控制
            cv2.imwrite('j_temp/{0}.png'.format(i), img)
            i += 1
        print('图片数', i)
        self.max_arrange = i - 1  # 获取图片序列用于控制寻找边界点的结束
        if i <= 2:
            print('过短！一张图还不如直接截呐')
            self.clear_timer.start(0)
            return
        else:
            find_pos.wait()  # 等待拼接点寻找完成
        print('found_pos_done')
        self.merge_all()  # 调用图片拼接函数

        self.clear_timer.start(10000)  # 10s后初始化内存


def listen():
    """鼠标监听,截屏中当按下鼠标停止截屏"""
    global listener
    print("listen")

    def on_click(x, y, button, pressed):
        if button == mouse.Button.left:
            if roller.in_rolling:
                roller.in_rolling = False

    listener = mouse.Listener(on_click=on_click)
    listener.start()


class Commen_Thread(QThread):
    """造的轮子...可用于多线程中不同参数的输入"""

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
                print(self.args[0])
            elif len(self.args) == 2:
                self.action(self.args[0], self.args[1])
        else:
            self.action()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    roller = Splicing_shots()
    listen()
    roller.auto_roll((550, 50, 800, 750))
    sys.exit(app.exec_())
