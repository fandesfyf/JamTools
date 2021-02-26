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
        self.img_list = self.crc_list = []
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

    def find_left_side(self):
        """寻找相同的左边界"""
        img = self.img_list[0]
        img1 = self.img_list[1]
        for i in range(len(img[:, 0, 1])):
            line1 = img[:, i, 1]
            line2 = img1[:, i, 1]
            if not self.is_the_same_line(line1, line2):
                self.left_border = i
                print('leftboarder:', i)
                break

    def find_right_size(self):
        """寻找相同的右边界"""
        img = self.img_list[0]
        img1 = self.img_list[1]
        for i in range(len(img[:, 0, 1]),0, -1):
            print(i)
            line1 = img[:, i, 1]
            line2 = img1[:, i, 1]
            if not self.is_the_same_line(line1, line2):
                self.right_border = i
                print('rightboarder:', i)
                break

    def is_the_same_line(self, line1, line2):
        return not np.any(cv2.subtract(line2, line1))

    def find_the_same_head_to_remove(self):
        """寻找相同的头部(上边界)"""
        # if self.images_data
        img = self.img_list[0]
        img1 = self.img_list[1]
        for i in range(len(img[:, 0, 1])):
            line1 = img[i, :, 1]
            line2 = img1[i, :, 1]
            if not self.is_the_same_line(line1, line2):
                self.min_head = i
                print('minhead:', i)
                break

        # print(len(img[0,:,1]))

    def majority_color(self, classList):
        '''返回颜色列表中最多的颜色'''
        count_dict = {}
        for label in classList:
            if label not in count_dict.keys():
                count_dict[label] = 0
            count_dict[label] += 1
        # print(max(zip(count_dict.values(), count_dict.keys())))
        return max(zip(count_dict.values(), count_dict.keys()))

    def isthesameline(self, line1, line2):
        """判断是否两行是否相同"""
        same = 0
        rate = self.rate
        line1_majority_color = self.majority_color(line1)
        line2_majority_color = self.majority_color(line2)

        if line2_majority_color[1] != line1_majority_color[1]:
            # print(self.majority_color(line2),self.majority_color(line1))
            return 0
        elif abs(line1_majority_color[0] - line2_majority_color[0]) > self.img_width * (1 - rate) * 0.5:
            return 0
        else:
            majority_color_count, majority_color = line2_majority_color
            # print(majority_color_count,majority_color)
        if majority_color_count > int(self.cut_width * rate):
            return 1

        for i in range(self.cut_width):
            if line1[i] == majority_color or line2[i] == majority_color:
                # print('maj')
                continue
            else:
                if abs(line1[i] - line2[i]) < 10:
                    same += 1
        if same >= (self.cut_width - majority_color_count) * rate:
            return 1
        else:
            return 0

    def efind_the_pos(self):
        """在滚动的同时后台寻找拼接点"""
        while self.in_rolling or self.arrange < self.max_arrange:  # 如果正在截屏或截屏没有处理完
            print(self.arrange, '  max:', self.max_arrange)
            min_head = self.min_head
            left = self.left_border
            right = self.right_border
            self.cut_width = right - left
            images_data_line_list = self.img_list
            compare_row = self.compare_row
            i = self.arrange
            try:
                img1 = images_data_line_list[i]  # 前一张图片
                img2 = images_data_line_list[i + 1]  # 后一张图片
            except IndexError:
                time.sleep(0.1)  # 图片索引超出则等待下一张截屏
                continue
            max_line = [0, 0]
            for k in range(min_head, self.img_height - compare_row):  # 前一张图片从相同头部开始遍历到最后倒数compare_row行
                if self.in_rolling:  # 如果正在截屏则sleep一下避免过多占用主线程,也没什么用...
                    time.sleep(0.001)
                sameline = 0
                chance_count = 0
                chance = 0
                for j in range(min_head, min_head + compare_row):  # 后一张图片从相同头部开始逐行遍历compare_row行
                    lin1 = img1[k + sameline,left:right,1]
                    lin2 = img2[min_head + sameline,left:right,1]
                    if self.is_the_same_line(lin1, lin2):  # 如果是行相同,则sameline+1
                        sameline += 1
                        chance_count += 1
                        if chance_count >= 7:  # 每7行增加一个chance,避免误判
                            chance_count = 0
                            chance += 1
                        if sameline > max_line[1]:
                            max_line[0] = k
                            max_line[1] = sameline  # 记录最大行数备用
                    else:  # 否则chance-1直到退出
                        if chance <= 0:
                            break
                        else:
                            chance -= 1
                            sameline += 1

                if sameline >= compare_row - compare_row // 20:
                    self.head_pos[i] = k
                    print(i, k,sameline)
                    print(self.head_pos)
                    break
            if i not in self.head_pos.keys():  # 如果没有找到符合的拼接点,则取最大的配合点,并标记为可能出错的地方
                if max_line[1] >= 1:
                    self.head_pos[i] = max_line[0]
                    print(self.head_pos)
                    max_line.append(i)
                    self.maybe_errorlist.append(max_line)
                    print('max_line', i, max_line)  # 测试
            self.arrange += 1

    def find_the_pos(self):  # 和上面的efind_the_pos类似
        """寻找拼接点,当图片数少时可以直接截完屏调用"""
        min_head = self.min_head
        left = self.left_border
        right = self.right_border
        self.cut_width = right - left
        images_data_line_list = self.images_data_line_list
        compare_row = self.compare_row
        # print(min_head, self.img_height - compare_row)
        for i in range(len(self.img_list) - 1):
            # print(i)
            img1 = images_data_line_list[i]
            img2 = images_data_line_list[i + 1]
            max_line = [0, 0]  # 测试
            for k in range(min_head, self.img_height - compare_row):
                sameline = 0
                chance_count = 0
                chance = 0
                for j in range(min_head, min_head + compare_row):
                    lin1 = img1[k + sameline][left:right]
                    lin2 = img2[min_head + sameline][left:right]
                    # print(len(lin2),len(lin1))
                    res = self.isthesameline(lin1, lin2)
                    if res:
                        sameline += 1
                        chance_count += 1
                        if chance_count >= 5:
                            chance_count = 0
                            chance += 1
                        if sameline > max_line[1]:
                            max_line[0] = k
                            max_line[1] = sameline  # 测试
                        # print(i, j, k)
                    else:
                        # print(chance)
                        if chance <= 0:
                            break
                        else:
                            chance -= 1
                            sameline += 1

                if sameline >= compare_row - compare_row // 20:
                    self.head_pos[i] = k
                    print(i, k)
                    print(self.head_pos)
                    break
            if i not in self.head_pos.keys():
                if max_line[1] >= 1:
                    self.head_pos[i] = max_line[0]
                    print(self.head_pos)
                    max_line.append(i)
                    self.maybe_errorlist.append(max_line)
                    print('max_line', i, max_line)  # 测试

    def merge_all(self):
        """根据拼接点拼接所有图片"""

        for i in range(len(self.img_list) - 1):
            if i not in self.head_pos.keys():
                majority_pos = self.majority_color(self.head_pos.values())
                self.head_pos[i] = majority_pos[1]
                print(i, '丢失,补', majority_pos)  # 丢失则补为图片拼接点的众数,虽然没有什么用...
        print('图片数:', len(self.img_list), '界点:', len(self.head_pos.keys()))
        final_pic = []
        final_pic.extend(self.img_list[0])
        # print(self.pos_list,len(self.pos_list),len(self.img_list))
        h = 0
        for i in range(len(self.head_pos.keys())):
            head = self.head_pos[i]
            imgpart = self.img_list[i + 1]
            print(head, i)
            h += head
            imgpart = imgpart[head:, :, :]
            final_pic = final_pic[:h]
            final_pic.extend(imgpart)
        cv2.imwrite('final.png', np.array(final_pic))
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
        # print('相似度', n)
        if n < 1:
            return True
        else:
            return False

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

    def auto_roll(self, area):
        """自动滚动截屏,总函数"""
        x, y, w, h = area
        self.img_width = w
        self.img_height = h
        speed = round(1 / self.roll_speed, 2)
        screen = QApplication.primaryScreen()
        controler = MouseController()
        find_left = Commen_Thread(self.find_left_side)
        find_right = Commen_Thread(self.find_right_size)
        find_head = Commen_Thread(self.find_the_same_head_to_remove)
        find_pos = Commen_Thread(self.efind_the_pos)
        threads = [find_left, find_pos, find_right, find_head]
        self.in_rolling = True
        i = 0
        img_height = 0
        controler.position = (area[0] + int(area[2] / 2), area[1] + int(area[3] / 2))
        while self.in_rolling:
            pix = screen.grabWindow(QApplication.desktop().winId(), x, y, w, h)  # 区域截屏获取图像pixmap
            img = self.qpix_to_cv2(pix)
            # img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)# 将qt的pixmap转为pil模块的img对象
            self.img_list.append(img)  # 储存图片的列表
            if i >= 1:
                if self.is_same(self.img_list[i - 1], self.img_list[i]):  # 每帧检查是否停止(图片是否相同)
                    self.in_rolling = False
                    i += 1
                    break
                if img_height == 0:  # 图片有两张以上后,启动线程寻找图片边界点
                    img_height = 1
                    find_head.start()
                    find_left.start()
                    find_right.start()
                if i == 5:  # 图片大于5张才开始寻找拼接点
                    find_pos.start()
                    pass
            controler.scroll(dx=0, dy=-3)  # 滚动屏幕
            time.sleep(0.1)  # 速度控制
            cv2.imwrite('j_temp/{0}.png'.format(i), img)
            i += 1
        print('图片数', i)
        t = time.process_time()
        self.max_arrange = i - 1  # 获取图片序列用于控制寻找边界点的结束
        for thread in threads:  # 遍历并等待各线程结束
            thread.wait()
        #     # print(thread)
        # if i <= 2:
        #     print('过短！一张图还不如直接截呐')
        #     self.clear_timer.start(0)
        #     return
        # elif i <= 5:
        #     self.find_the_pos()  # 图片小于5张则截完屏在拼接
        # else:
        #     find_pos.wait()  # 等待拼接点寻找完成
        # # self.find_the_pos()
        # print('found_pos_done')
        # # try:
        #
        self.merge_all()  # 调用图片拼接函数
        # # except:
        # #     print('拼接出错错误!请重新截屏！')
        # #     self.clear_timer.start(10000)
        # #     return
        print('可能错误的地方:', self.maybe_errorlist, '用时:', time.process_time() - t)
        # self.clear_timer.start(10000)  # 10s后初始化内存


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
    roller.auto_roll((350, 50, 800, 750))
    sys.exit(app.exec_())
