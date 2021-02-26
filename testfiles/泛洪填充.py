import cv2, sys
import numpy as np
import math
import os
import time

sys.setrecursionlimit(100000)
from PyQt5.QtGui import QImage

from jampublic import *
from jamroll_screenshot import Splicing_shots
import jamresourse


def image_fill(image, x, y, color: tuple = (0, 0, 255), d=0):
    src = image.copy()  # 先创建一个副本
    a=cv2.floodFill(src, None, (x, y), color, (d, d, d), (d, d, d), cv2.FLOODFILL_FIXED_RANGE)
    # （60,60）代表起始点；（0,0，255）代表填充颜色；loDiff=（50,50，50）代表只能填充比填充颜色小对应数值的点，upDiff同理
    cv2.circle(src, (x, y), 2, color=(0, 255, 0), thickness=4)
    cv2.imshow('flood_fill', src)
    return src


image1 = cv2.imread('screen_test.png')  # 原图
image_fill(image1, 502, 600, (2, 125, 255))
c = cv2.waitKey(0)
cv2.destroyAllWindows()
