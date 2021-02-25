# import os
import subprocess
import time
from threading import Thread

from pynput import keyboard

# os.system('ffmpeg -f gdigrab -i desktop -vcodec libx264 out.mp4 -y')

# -offset_x 10 -offset_y 20 -video_size 640x480
# record = subprocess.Popen(
#     '"D:\python_work\Jamtools/bin/ffmpeg"  -thread_queue_size 16 -f dshow  -framerate 30 -rtbufsize 500M -i video="screen-capture-recorder" '+
#     ' -thread_queue_size 16 -f dshow -rtbufsize 50M -i audio="virtual-audio-capturer"  '+
#     ' -vf crop=1920:500:500:0  -profile:v  high444 -level 5.1   -pix_fmt yuv420p -preset:v ultrafast -preset:a  ultrafast  -vcodec libx264  D:/图片/视频/Jam_screenrecord/2020-05-30_00.05.19.mp4 -y'
# , shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
record = subprocess.Popen(
    '"D:\python_work\Jamtools/bin/ffmpeg"  -i  "D:\图片\视频\AR车载导航.mp4"'
    , shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
info = record.stderr.read().decode().lower()
print(info)
print("stream #0:1" in info, "audio" in info)

"""macos:"""
# ./ffmpeg -f avfoundation -i 0:1 -r 30 -vcodec libx264 11.mp4 -y 录屏
# ./ffmpeg -thread_queue_size 16 -f avfoundation -rtbufsize 50M -i 0:0  -vf crop=1078:556:632:142 -r 30 -vcodec libx264 11.mp4
"""macos"""

# '"D:\python_work\Jamtools/bin/ffmpeg"  -thread_queue_size 16 -f dshow -rtbufsize 500M  -framerate 25.0 -draw_mouse 1  -offset_x 0 -offset_y 0 '
# ' -i video="screen-capture-recorder"   -thread_queue_size 16 -f dshow -rtbufsize 50M -i audio="virtual-audio-capturer"  '
# '-qp 5  -vf scale=1920:-2 -profile:v  high444 -level 5.1   -pix_fmt yuv420p -preset:v ultrafast -preset:a  ultrafast  '
# '-vcodec libx264  D:/图片/视频/Jam_screenrecord/test.mp4 -y'

# record = subprocess.Popen('ffmpeg -list_devices true -f dshow -i dummy ', shell=True, stdin=subprocess.PIPE,
#                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
# ffmpeg -i a.mp4 -acodec copy -vf "movie=pic.png[watermark];[in][watermark]overlay=20:20" output.mp4 添加水印
# time.sleep(5)
# relog = record.stderr.read()
# print(relog)
# print("------------------------------------------")ffmpeg -i a.mp4 -b:v 548k -vf delogo=x=495:y=10:w=120:h=45:show=1 delogo.mp4
# audio_divice = []
# reloglist = relog.split('"')
# print(len(reloglist))
# for i in range(len(reloglist) // 2):
#     if reloglist[2 * i + 1][0] != '@' and reloglist[2 * i + 1].lower().find(r'audio') != -1:
#         audio_divice.append(reloglist[2 * i + 1])
#         print(reloglist[2 * i + 1])
# print("------------------------------------------")
#
# for i in audio_divice:
#     print(i.lower().find(r'audio'))
#     print(i)

def listen2():
    print("listen")

    def on_activate_screenshot():
        print('<ctrl>+<alt>+h pressed')
        record.stdin.write('q'.encode("GBK"))
        record.communicate()
        # jamtools.screensh()

    def on_activate_ocr():
        print('<ctrl>+<alt>+i pressed')
        # jamtools.BaiduOCR()

    def on_activate_screenrecord():
        print('alt+c')
        # recorder.recordchange()

    def on_activate_actionrun():
        print('z+x')
        # if jamtools.can_controll:
        #     jamtools.controller.running_change()

    def on_activate_actionrecord():
        print('x+c')
        # if jamtools.can_controll:
        #     jamtools.controller.listening_change()

    with keyboard.GlobalHotKeys({
        '<alt>+z': on_activate_screenshot,
        '<alt>+x': on_activate_ocr,
        '<alt>+c': on_activate_screenrecord,
        'z+x': on_activate_actionrun,
        'c+x': on_activate_actionrecord}) as h:
        h.join()


class Threads(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        listen()


listen2()
# t = Threads()
# t.start()
