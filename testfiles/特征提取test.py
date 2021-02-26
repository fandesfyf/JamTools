#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2020/11/8 14:13
# @Author  : Fandes
# @FileName: 特征提取test.py
# @Software: PyCharm

# coding=utf-8
import random
import sys
import time

import cv2
import numpy as np

# 读取图像
img1 = cv2.imread("j_temp/1.png")
img2 = cv2.imread("j_temp/2.png")

img3 = cv2.imread("j_temp/3.png")
img4 = cv2.imread("j_temp/4.png")


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
            if sorteddistance[0][1]<8:
                return 0,0 ,0
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


picmatcher = PicMatcher(draw=True)
picmatcher.match(img1, img2)
picmatcher.match(img2, img3)
picmatcher.match(img3, img4)

cv2.waitKey(0)
cv2.destroyAllWindows()