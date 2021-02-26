import time

import cv2
import os
import numpy as np
import crc16


def find_samehead(s1, s2):
    line = 0
    for i in range(len(s1)):
        if s1[i] == s2[i]:
            line += 1
        else:
            break
    return line


def find_lcsubstr(s1, s2):
    # m = [[0 for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]
    mmax = 0
    p = (0, 0)
    sameline = find_samehead(s1, s2)
    for i in range(sameline, len(s1) - 50):
        t = 0
        for j in range(sameline, sameline + 50):
            if s2[j]-3000<= s1[i + j - sameline] <= s2[j]+3000:
                t += 1
                if t > mmax:
                    mmax = t
                    p = (mmax, i)

    return p,sameline


st = time.process_time()
image_list = os.listdir('j_temp')
dict = {}
all_crc16_list = []
for image in sorted(image_list):
    img = cv2.imread(os.path.join('j_temp', image))
    print(os.path.join('j_temp', image))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    crc16_list = []
    for l in gray:
        crc16_list.append(crc16.crc16xmodem(l))
    dict[image] = crc16_list
    all_crc16_list.append(crc16_list)

with open('testfilettt.txt', 'w+')as f:
    for i in dict.keys():
        f.write(str(i) + ':' + str(dict[i]) + '\n\n')

final_img = []
first_img = cv2.imread(os.path.join('j_temp', sorted(image_list)[0]))
final_img.extend(first_img)
for i in range(len(all_crc16_list) - 1):
    crc16_list_1 = all_crc16_list[i]
    crc16_list_2 = all_crc16_list[i + 1]
    r = find_lcsubstr(crc16_list_1, crc16_list_2)
    print(r, i)
    # image1=cv2.imread(os.path.join('j_temp', sorted(image_list)[i]))

    # if i == 0:
    #     print(len(longest_common_substring), img1_cut_length, length)
    #     print(longest_common_substring)
    #
    # if length == 0:
    #     continue
    # img1 = cv2.imread(os.path.join('j_temp', sorted(image_list)[i]))
    # new_image_1 = img1[:img1_cut_length, :, :]
    # img2 = cv2.imread(os.path.join('j_temp', sorted(image_list)[i + 1]))
    # idx = crc16_list_2.index(longest_common_substring[0])
    # new_image_2 = img2[crc16_list_2.index(longest_common_substring[0]) + length:, :, :]
    # final_img.extend(new_image_2)
cv2.imwrite('final.jpg', np.array(final_img))
print(time.process_time() - st)
