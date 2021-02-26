import math
import operator
import time
from functools import reduce
from collections import Counter
from threading import Thread

from PIL import Image, ImageChops


class Splicing_shots(object):
    def __init__(self):
        self.img = []
        self.img_list = []
        self.images_data = []  # 每行数据列表
        self.images_data_list = []  # 每个图片数据列表

        self.images_data_line_list = []
        self.img_width = 0
        self.img_height = 0
        self.compare_row = 50
        self.cut_width = 0
        self.rate = 0.85
        self.left_border = 0
        self.min_head = 0
        self.min_left = 0
        self.min_right = 0
        self.right_border = 0
        self.head_pos = {}
        self.head_data = None

    def open_img(self):

        for i in self.img:
            img = Image.open(i)
            if self.img_width == 0:
                self.img_width, self.img_height = img.size
            self.img_list.append(img)
            # rotate_img = img.rotate(270, expand=1)
            # rotate_img_data = list(rotate_img.convert('L').getdata())
            img_data = list(img.convert('L').getdata())
            self.images_data_list.append(img_data)
            an_imgdata = []
            for line in range(img.height):
                an_imgdata.append(img_data[line * img.width:(line + 1) * img.width])
            self.images_data_line_list.append(an_imgdata)
            # with open('pn.txt','w+')as p:
            #     p.write(str(self.images_data_line_list))
            # an_image_line = []
            # for line in range(rotate_img.height - 1):
            #     # print(rotate_img.size)
            #     an_image_line.append(rotate_img_data[line * rotate_img.width:(line + 1) * rotate_img.width])
            # self.images_data_line_list.append(an_image_line)

    def find_left_side(self):
        images_data_list = []
        for img in self.img_list[:2]:
            rotate_img = img.rotate(270, expand=1)
            rotate_img_data = list(rotate_img.convert('L').getdata())
            an_imgdata = []
            for line in range(rotate_img.height - 1):
                an_imgdata.append(rotate_img_data[line * rotate_img.width:(line + 1) * rotate_img.width])
            images_data_list.append(an_imgdata)
        rotate_height = len(images_data_list[0])
        min_head = rotate_height
        for i in range(1):
            for j in range(1, rotate_height):
                img1 = images_data_list[i][:j]
                img2 = images_data_list[i + 1][:j]
                # print(img2)
                if img2 != img1:
                    if j == 1:
                        print('没有重复左边！')
                        # print(self.majority_color(self.images_data_line_list[0]))
                        return
                    elif j < (min_head + 1):
                        min_head = j - 1

                    break
        self.min_left = min_head
        print('minleft', min_head)

    def find_right_size(self):
        images_data_list = []
        for img in self.img_list[:2]:
            rotate_img = img.rotate(90, expand=1)
            rotate_img_data = list(rotate_img.convert('L').getdata())
            an_imgdata = []
            for line in range(rotate_img.height - 1):
                an_imgdata.append(rotate_img_data[line * rotate_img.width:(line + 1) * rotate_img.width])
            images_data_list.append(an_imgdata)
        rotate_height = len(images_data_list[0])
        min_head = rotate_height
        for i in range(1):
            for j in range(1, rotate_height):
                img1 = images_data_list[i][:j]
                img2 = images_data_list[i + 1][:j]
                # print(img2)
                if img2 != img1:
                    if j == 1:
                        print('没有重复右边！')
                        self.min_right = self.img_width
                        # print(self.majority_color(self.images_data_line_list[0]))
                        return
                    elif j < (min_head + 1):
                        min_head = j - 1
                    break
        self.min_right = self.img_width - min_head
        print('minright', min_head)

    def find_the_same_head_to_remove(self):
        # if self.images_data
        min_head = self.img_height
        for i in range(len(self.img) - 1):
            for j in range(1, self.img_height):
                img1 = self.images_data_line_list[i][:j]
                img2 = self.images_data_line_list[i + 1][:j]
                # print(img2)
                if img2 != img1:
                    if j == 1:
                        print('没有重复头！')
                        # print(self.majority_color(self.images_data_line_list[0]))
                        return
                    elif j < (min_head + 1):
                        min_head = j - 1

                    break
        self.min_head = min_head
        print('minhead', min_head)
        # print(self.images_data_list[0])
        # self.head_data = self.images_data_list[0][:self.img_width * min_head]
        # self.img_height = self.img_height - min_head
        # for i, imgdata in enumerate(self.images_data_list):
        #     self.images_data_list[i] = imgdata[self.img_width * min_head:]

        # self.img_list[i] = Image.new('RGB', (self.img_width, self.img_height))
        # self.img_list[i].putdata(self.images_data_list[i])
        # self.img_list[i].save('img{0}.png'.format(i))

        # print(len(self.head_data), self.img_width)

    def majority_color(self, classList):
        '''返回标签列表中最多的标签'''
        count_dict = {}
        for label in classList:
            if label not in count_dict.keys():
                count_dict[label] = 0
            count_dict[label] += 1
        # print(max(zip(count_dict.values(), count_dict.keys())))
        return max(zip(count_dict.values(), count_dict.keys()))

    def isthesameline(self, line1, line2):
        # print(line1)
        same = 0
        line1_majority_color = self.majority_color(line1)
        line2_majority_color = self.majority_color(line2)

        if line2_majority_color[1] != line1_majority_color[1]:
            # print(self.majority_color(line2),self.majority_color(line1))
            return 0
        elif abs(line1_majority_color[0] - line2_majority_color[0]) > self.img_width*0.05:
            # print(self.img_width,)
            return 0
        else:
            majority_color_count, majority_color = line2_majority_color
            # print(majority_color_count,majority_color)
        if majority_color_count > int(self.cut_width * 0.9):
            return 1
        for i in range(self.cut_width):
            if line1[i] == majority_color or line2[i] == majority_color:
                # print('maj')
                continue
            else:
                if abs(line1[i] - line2[i]) < 10:
                    same += 1
        if same >= (self.cut_width - majority_color_count) * self.rate:
            return 1
        else:
            return 0

    def find_the_pos(self):
        self.head_pos = {}
        min_head = self.min_head
        left = self.min_left
        right = self.min_right
        self.cut_width = right - left
        images_data_line_list = self.images_data_line_list
        compare_row = self.compare_row
        for i in range(len(self.img) - 1):
            img1 = images_data_line_list[i]
            img2 = images_data_line_list[i + 1]
            max_line = [0, 0]#测试
            for k in range(min_head, self.img_height - compare_row):
                # print(k)
                sameline = 0
                chance_count = 0
                chance = 0
                for j in range(min_head, min_head + compare_row):
                    st1 = k + sameline
                    dt2 = min_head + sameline
                    lin1 = img1[k + sameline][left:right]
                    lin2 = img2[min_head + sameline][left:right]
                    # print(len(lin2),len(lin1))
                    res = self.isthesameline(lin1, lin2)
                    # if res == -1:
                    #     break
                    if res:
                        sameline += 1
                        chance_count += 1
                        if chance_count >= 7:
                            chance_count = 0
                            chance += 1
                        if sameline > max_line[1]:
                            max_line[0] = k
                            max_line[1] = sameline#测试
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
                if max_line[1]>=1:
                    self.head_pos[i]=max_line[0]
                    print('max_line',i, max_line)#测试

    def merge_all(self):
        # self.images_data_line_list=[]
        try:
            majority_pos = self.majority_color(self.head_pos.values())
            for i in range(len(self.img) - 1):
                if i not in self.head_pos.keys():
                    self.head_pos[i] = majority_pos[1]
                    print(i, '丢失,补', majority_pos)
            img_width = self.img_width
            img_height = 0
            # head_pos = []
            # for i in len(self.head_pos)
            for i in self.head_pos.keys():
                img_height += self.head_pos[i] - self.min_head
                # print(img_height)
            img_height += self.img_height  # 加最后一张
            newpic = Image.new(self.img_list[0].mode, (img_width, img_height))
            height = 0
            if self.min_head:
                height += self.min_head
                newpic.paste(self.img_list[0].crop((0, 0, img_width, self.min_head)), (0, 0))
            for i in range(len(self.img_list) - 1):
                if self.min_head:
                    newpic.paste(self.img_list[i].crop((0, self.min_head, self.img_width, self.head_pos[i])),
                                 (0, height))
                    height += self.head_pos[i] - self.min_head
                else:
                    newpic.paste(self.img_list[i].crop((0, self.min_head, self.img_width, self.head_pos[i])),
                                 (0, height))
                    height += self.head_pos[i]
            if self.min_head:
                newpic.paste(self.img_list[-1].crop((0, self.min_head, img_width, img_height)), (0, height))
            else:
                newpic.paste(self.img_list[-1], (0, height))
            newpic.save('new.png')
        except:
            print('error')

            # self.merge_all()

    def splicing(self, imagePaths=[]):
        st = time.process_time()
        # f = Commen_Thread(self.find_left_side)
        # f.start()
        self.img = imagePaths
        self.open_img()
        st1 = time.process_time()
        self.find_the_same_head_to_remove()

        # f.join()
        self.find_left_side()
        self.find_right_size()
        st2 = time.process_time()
        # self.dt_()
        # self.remove_side()
        self.find_the_pos()
        # self.aefind_the_pos(2)
        st3 = time.process_time()
        self.merge_all()
        print(st1 - st)
        print(st2 - st1)
        print(st3 - st2)
        print(time.process_time() - st3)
        print('总时间：', time.process_time() - st)
        # if (imagePath != []):
        #     self.__imgPath = imagePath
        # self.__curr = 0
        # self.__openImages()  # 加载图片
        # newImgData, newHeight = self.__getNewImgData()
        # newImg = Image.new('RGB', (self.__width, newHeight))
        # newImg.putdata(newImgData)
        # print('拼图完成！')
        # return newImg


class Commen_Thread(Thread):
    def __init__(self, action, *args):
        super().__init__()
        self.action = action
        self.args = args
        # print(self.args)

    def run(self):
        if self.args:
            self.action(self.args)
        else:
            self.action()


ss = Splicing_shots()
pic = []
for i in range(24):
    s = 'j_temp/{0}.png'.format(i)
    pic.append(s)
ss.splicing(['j_temp/00001.png','j_temp/00002.png','j_temp/00003.png','j_temp/00004.png','j_temp/00005.png','j_temp/00006.png'])
# while 1:
#     time.sleep(1)
