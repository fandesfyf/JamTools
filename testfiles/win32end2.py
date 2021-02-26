import os
import sys
import time
from os import path
from threading import Thread
import win32con
import win32gui
import win32ui
import cv2

from PyQt5.QtWidgets import QApplication
from pynput import keyboard

ALT = False
Z = False
X = False
C = False


def listen():
    print("listen")

    def on_press(key):
        global ALT, Z, X, C, start_time, real_fps
        if key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            ALT = True
        if key == keyboard.KeyCode(char='z') or key == keyboard.KeyCode(char='Z'):
            Z = True
        if key == keyboard.KeyCode(char='x') or key == keyboard.KeyCode(char='X'):
            X = True
        if key == keyboard.KeyCode(char='c') or key == keyboard.KeyCode(char='C'):
            C = True
        # print(ALT, Z, X, C)

        if ALT and C:  # 识图
            ALT = C = False
            record.recording = not record.recording
            print(11)
            # startt = time.process_time()

            if record.recording:
                startt = time.process_time()
                startrecord = Startrecord()
                startrecord.start()
                # prossthread = FileThread()
                # prossthread.start()
                # prossthread2 = FileThread()
                # prossthread2.start()

                print(record.recording)
            else:
                print("录制时间" + str(time.process_time() - startt))
                print(i)
                rfps = i // (time.process_time() - startt)
                print("fps" + str(rfps))

                # size = (920, 880)
                # videoWriter = cv2.VideoWriter('t/TestVideo.mp4', cv2.VideoWriter_fourcc(*'mp4v'),
                #                               fps, size)# *'XVID'MPEG-4编码 *'mp4v' *'PIMI' MPEG-1编码  *'I420'（无损压缩avi）

        # if key == keyboard.Key.enter:
        #     print(112)
        #     try:
        #         jamtools.chat()
        #     except:
        #         print(122)
        # if any([key in COMBO for COMBO in COMMAND]):
        #     current_keys.add(key)
        #     if any(all(k in current_keys for k in COMBO) for COMBO in COMMAND):
        #         jamtools.show()
        #         jamtools.showNormal()
        #         print(11)

    def on_release(key):
        global ALT, Z, X, C
        if key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            ALT = False
        if key == keyboard.KeyCode(char='z') or key == keyboard.KeyCode(char='Z'):
            Z = False
        if key == keyboard.KeyCode(char='x') or key == keyboard.KeyCode(char='X'):
            X = False
        if key == keyboard.KeyCode(char='c') or key == keyboard.KeyCode(char='C'):
            C = False

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


class listenThread(Thread):

    def __init__(self):
        super().__init__()

    def run(self):
        listen()


class Startrecord(Thread):

    def __init__(self):
        super().__init__()

    def run(self):
        record.record()


class FileThread(Thread):

    def __init__(self):
        super().__init__()

    def run(self):

        while 1:
            if record.namelist:
                pross = record.namelist.pop(0)
                img2 = cv2.imread(pross)
                record.videoWriter.write(img2)
                os.remove(pross)
            if not record.namelist and record.recorded2:
                print("处理完毕")
                record.videoWriter.release()
                break


class Recordingthescreen():
    def __init__(self):

        # app = QApplication(sys.argv)
        self.screen = QApplication.primaryScreen()
        self.recording = False
        self.recorded = False
        self.recorded2 = False
        self.namelist = []
        self.fps = real_fps
        self.size = (1920, 1080)
        self.videoWriter = cv2.VideoWriter('t/TestVideo.avi', cv2.VideoWriter_fourcc(*'XVID'),
                                           self.fps,
                                           self.size)  # *'XVID'MPEG-4编码 *'mp4v' *'PIMI' MPEG-1编码  *'I420'（无损压缩avi

    def window_capture(self, filename):
        hwnd = 0  # 窗口的编号，0号表示当前活跃窗口
        # 根据窗口句柄获取窗口的设备上下文DC（Divice Context）
        hwndDC = win32gui.GetWindowDC(hwnd)
        # 根据窗口的DC获取mfcDC
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        # mfcDC创建可兼容的DC
        saveDC = mfcDC.CreateCompatibleDC()
        # 创建bigmap准备保存图片
        saveBitMap = win32ui.CreateBitmap()
        # 获取监控器信息
        # MoniterDev = win32api.EnumDisplayMonitors(None, None)
        # print(MoniterDev)
        w = self.size[0]
        h = self.size[1]
        # print w,h　　　#图片大小
        # 为bitmap开辟空间
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        # 高度saveDC，将截图保存到saveBitmap中
        saveDC.SelectObject(saveBitMap)
        # 截取从左上角（0，0）长宽为（w，h）的图片
        saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
        saveBitMap.SaveBitmapFile(saveDC, filename)
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

    def record(self):
        global i

        i = 0
        prossthread = FileThread()
        prossthread.start()

        if self.recording:
            self.videoWriter = cv2.VideoWriter('t/TestVideo.avi', cv2.VideoWriter_fourcc(*'XVID'),
                                               self.fps,
                                               self.size)  # *'XVID'MPEG-4编码 *'mp4v' *'PIMI' MPEG-1编码  *'I420'（无损压缩avi
            print("creatwriter")
            while self.recording:
                t1 = time.process_time()
                self.window_capture("t/haha{0}.png".format(i))
                self.namelist.append("t/haha{0}.png".format(i))
                i += 1

                self.recorded = True
                print(str(i) + '\t' + str(time.process_time() - t1))
            print("截屏完成进行处理")
        if not self.recording and self.recorded:
            self.recorded2 = True
            # prossthread.start()

            prossthread.join(200)
            self.videoWriter.release()
            # size = (920, 880)
            print("视频制作")
            print(real_fps)
            videoWriter2 = cv2.VideoWriter('t/TestVideo11.mp4', cv2.VideoWriter_fourcc(*'mp4v'),
                                           real_fps, self.size)  # *'XVID'MPEG-4编码 *'mp4v' *'PIMI' MPEG-1编码  *'I420'（无损压缩avi
            videoCapture = cv2.VideoCapture('t/TestVideo.avi')
            success, frame = videoCapture.read()
            while success:
                success, frame = videoCapture.read()

                videoWriter2.write(frame)
            videoWriter2.release()

            print("制作完成：" + str(time.process_time() - t1))
            self.recorded = False
            self.recorded2 = False
            i = 0

#
# class MyWindow():
#     def __init__(self):
#         # 注册一个窗口类
#         wc = win32gui.WNDCLASS()
#         wc.lpszClassName = '酱截屏'
#         wc.hbrBackground = win32con.COLOR_BTNFACE + 1  # 这里颜色用法有点特殊，必须+1才能得到正确的颜色
#         wc.lpfnWndProc = self.wndProc  # 可以用一个函数，也可以用一个字典
#         class_atom = win32gui.RegisterClass(wc)
#         # 创建窗口
#         self.hwnd = win32gui.CreateWindow(
#             class_atom, u'酱截屏', win32con.WS_OVERLAPPEDWINDOW,
#             800, 400,
#             300, 300,
#             0, 0, 0, None)
#         # 显示窗口
#         win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNORMAL)
#
#     # 消息处理
#     def wndProc(self, hwnd, msg, wParam, lParam):
#         if msg == win32con.WM_SIZE: print('message: WM_SIZE')
#         if msg == win32con.WM_PAINT: print('message: WM_PAINT')
#         if msg == win32con.WM_CLOSE: print('message: WM_CLOSE')
#         if msg == win32con.WM_DESTROY:
#             print('message: WM_DESTROY')
#             win32gui.PostQuitMessage(0)
#         return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)


if __name__ == "__main__":
    if not path.exists("t"):
        os.mkdir("t")
    start_time = time.process_time()
    real_fps = 10
    i = 0
    app = QApplication(sys.argv)
    record = Recordingthescreen()
    listenThread = listenThread()
    listenThread.start()
    # mw = MyWindow()
    # win32gui.PumpMessages()
    # record = Recordingthescreen()
    # record.record()
