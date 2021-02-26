import math

import numpy as np
import cv2


def cut_mutipic(img, pointlist):
    xlist = [i[0] for i in pointlist]
    ylist = [i[1] for i in pointlist]
    w = max(xlist) - min(xlist)
    h = max(ylist) - min(ylist)
    x0, y0 = min(xlist), min(ylist)
    for i, lis in enumerate(pointlist):
        pointlist[i] = [lis[0] - x0, lis[1] - y0]
    img = img[y0:y0 + h, x0:x0 + w]
    pts = np.array(pointlist)
    pts = np.array([pts])
    # 和原始图像一样大小的0矩阵，作为mask
    mask = np.zeros(img.shape[:2], np.uint8)
    # 在mask上将多边形区域填充为白色
    cv2.polylines(mask, pts, 1, 255)  # 描绘边缘
    cv2.fillPoly(mask, pts, 255)  # 填充
    # 逐位与，得到裁剪后图像，此时是黑色背景
    dstimg = cv2.bitwise_and(img, img, mask=mask)
    # cv2.imshow("dst", dst)
    tw = max(math.sqrt((pointlist[0][1] - pointlist[3][1]) ** 2 + (pointlist[0][0] - pointlist[3][0]) ** 2),
             math.sqrt((pointlist[1][1] - pointlist[2][1]) ** 2 + (pointlist[1][0] - pointlist[2][0]) ** 2))
    th = max(math.sqrt((pointlist[0][1] - pointlist[2][1]) ** 2 + (pointlist[0][0] - pointlist[2][0]) ** 2),
             math.sqrt((pointlist[3][1] - pointlist[1][1]) ** 2 + (pointlist[3][0] - pointlist[1][0]) ** 2))
    tw, th = int(tw), int(th)
    org = np.array(pointlist, np.float32)
    dst = np.array([[0, 0],
                    [tw, 0],
                    [tw, th],
                    [0, th]], np.float32)
    warpR = cv2.getPerspectiveTransform(org, dst)
    result = cv2.warpPerspective(dstimg, warpR, (tw, th), borderMode=cv2.BORDER_TRANSPARENT)
    # cv2.namedWindow("result",0)
    # cv2.imshow("result", result)
    # cv2.waitKey(0)
    return result


# 读取图像
p = [[714, 111], [1193, 77], [1261, 768], [641, 769]]
img = cv2.imread("screen_test.jpg")
cut_mutipic(img, p)
