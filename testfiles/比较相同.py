import time

from PIL import Image, ImageChops
# 使用第三方库：Pillow
import math
import operator
from functools import reduce

image1 = Image.open('j_temp/1.png')
image2 = Image.open('j_temp/2.png')


# 把图像对象转换为直方图数据，存在list h1、h2 中
def sdifferent(img1, img2):
    h1 = img1.histogram()
    h2 = img2.histogram()
    # b1=list(img1.getdata())
    # b2=list(img2.getdata())
    result = math.sqrt(reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, h1, h2))) / len(h1))
    return result


'''
sqrt:计算平方根，reduce函数：前一次调用的结果和sequence的下一个元素传递给operator.add
operator.add(x,y)对应表达式：x+y
这个函数是方差的数学公式：S^2= ∑(X-Y) ^2 / (n-1)
'''
# at=time.process_time()
print(sdifferent(image1, image2))
# print(time.process_time()-at)
# img=ImageChops.subtract_modulo(image1,image2)
# data=list(img.convert('L').getdata())
# # with open('img.txt','w+')as f:
# #     f.write(str(data))
# st = time.process_time()
# sero=0
# for i in data:
#     if i==0:
#         sero+=1
# print(sero)
# print(len(list(img.convert('L').getdata())),sero/len(list(img.convert('L').getdata())))
# print(time.process_time() - st)
#
#

# for i in range(10):
#     result=ImageChops.offset(image1,0,-15*i)
#     result.save('j_temp/areashot{0}.png'.format(i))
#     print(sdifferent(result,image2))
