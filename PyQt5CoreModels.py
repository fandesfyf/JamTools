#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Author  : Fandes
# @FileName: test.py
# @Software: PyCharm
# 项目地址:https://github.com/fandesfyf/JamTools
import hashlib
import json
import socket
import gc
import sys
import os, re
from  Logger import Logger
from jampublic import Commen_Thread, OcrimgThread, Transparent_windows, FramelessEnterSendQTextEdit, APP_ID, API_KEY, \
    SECRECT_KEY, PLATFORM_SYS, TrThread, mutilocr

import http.client

import random
import shutil
import subprocess

import time
from urllib.parse import quote

from PIL import Image

import qrcode
import requests
from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QStandardPaths, QTimer, QSettings, QFileInfo, \
    QUrl, QObject, QSize
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont, QImage, QTextCursor, QColor, QDesktopServices, QMovie
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QToolTip, QAction, QTextEdit, QLineEdit, \
    QMessageBox, QFileDialog, QMenu, QSystemTrayIcon, QGroupBox, QComboBox, QCheckBox, QSpinBox, QTabWidget, \
    QDoubleSpinBox, QLCDNumber, QScrollArea, QWidget, QToolBox, QRadioButton, QTimeEdit, QListWidget, QDialog, \
    QProgressBar
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from jamscreenshot import Slabel
from aip import AipOcr
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from pynput import keyboard, mouse
from jamcontroller import ActionController, ActionCondition
from WEBFilesTransmitter import WebFilesTransmitter, WebFilesTransmitterBox, apppath

# from voice_and_text import Text2voice
"""由于腾讯的api改为付费了,所以不显示播放声音(作者没钱了qaq),如需使用可以打开注释然后在voice_and_text和txpythonsdk中修改api即可"""
from clientFilesTransmitter import ClientFilesTransmitterGroupbox
import jamresourse

sys.stdout = Logger(os.path.join(os.path.expanduser('~'),"jamtools.log"))
if PLATFORM_SYS == "win32":
    import win32con
    import ctypes, ctypes.wintypes

    ctypes.windll.shcore.SetProcessDpiAwareness(2)
if PLATFORM_SYS == "darwin":
    import pynput.keyboard._darwin
    import pynput.mouse._darwin
elif PLATFORM_SYS == "linux":
    import pynput.keyboard._xorg
    import pynput.mouse._xorg
# APP_ID = QSettings('Fandes', 'jamtools').value('BaiduAI_APPID', '17302981', str)  # 获取的 ID，下同
# API_KEY = QSettings('Fandes', 'jamtools').value('BaiduAI_APPKEY', 'wuYjn1T9GxGIXvlNkPa9QWsw', str)
# SECRECT_KEY = QSettings('Fandes', 'jamtools').value('BaiduAI_SECRECT_KEY', '89wrg1oEiDzh5r0L63NmWeYNZEWUNqvG', str)

VERSON = "0.13.5A"


class JHotkey(QThread):
    ss_signal = pyqtSignal()
    ocr_signal = pyqtSignal()
    recordchange_signal = pyqtSignal()
    listening_change_signal = pyqtSignal()
    running_change_signal = pyqtSignal()
    showm_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        if PLATFORM_SYS == "win32":
            self.win32hotkey()
        else:
            self.pynputhotkey()

    def pynputhotkey(self):
        releaser = keyboard.Controller()

        def ssf():
            self.ss_signal.emit()
            releaser.release('z')
            releaser.release('Ω')

        def ocrf():
            self.ocr_signal.emit()
            releaser.release('x')
            releaser.release('≈')

        def srf():
            self.recordchange_signal.emit()
            releaser.release('c')
            releaser.release('ç')

        def a1f():
            self.listening_change_signal.emit()
            releaser.release('1')
            releaser.release('¡')

        def a2f():
            self.running_change_signal.emit()
            releaser.release('2')
            releaser.release('™')

        hotkey = keyboard.GlobalHotKeys({
            '<alt>+z': ssf,
            '<alt>+Ω': ssf,
            '<alt>+x': ocrf,
            '<alt>+≈': ocrf,
            '<alt>+c': srf,
            '<alt>+ç': srf,
            '<alt>+1': a1f,
            '<alt>+¡': a1f,
            '<alt>+2': a2f,
            '<alt>+™': a2f
        }
        )
        hotkey.start()
        print("hotkey start")
        hotkey.wait()
        hotkey.join()

    def win32hotkey(self):
        self.user32 = ctypes.windll.user32
        if not self.user32.RegisterHotKey(None, 100, win32con.MOD_ALT, 0x5A):
            print('RuntimeError')
            self.showm_signal.emit('无法注册截屏快捷键!Alt+z')
        if not self.user32.RegisterHotKey(None, 101, win32con.MOD_ALT, 0x58):
            print('RuntimeError')
            self.showm_signal.emit('无法注册文字识别快捷键!Alt+x')
        if not self.user32.RegisterHotKey(None, 102, win32con.MOD_ALT, 0x43):
            print('RuntimeError')
            self.showm_signal.emit('无法注册录屏快捷键!Alt+c')
        if not self.user32.RegisterHotKey(None, 103, win32con.MOD_ALT, 0x31):
            print('RuntimeError')
            self.showm_signal.emit('无法注册动作录制快捷键!Alt+1')
        if not self.user32.RegisterHotKey(None, 104, win32con.MOD_ALT, 0x32):
            print('RuntimeError')
            self.showm_signal.emit('无法注册动作播放快捷键!Alt+2')
        try:
            msg = ctypes.wintypes.MSG()
            while self.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:  # GetMessageA 堵塞
                print(msg.message, msg.wParam)
                if msg.message == win32con.WM_HOTKEY:
                    id = msg.wParam
                    if id == 100:
                        print('alt+z')
                        self.ss_signal.emit()
                    elif id == 101:
                        print('alt+x')
                        self.ocr_signal.emit()
                    elif id == 102:
                        print('alt+c')
                        self.recordchange_signal.emit()
                    elif id == 103:
                        print('Alt+1')
                        self.listening_change_signal.emit()
                    elif id == 104:
                        print('Alt+2')
                        self.running_change_signal.emit()

                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageA(ctypes.byref(msg))
        finally:
            # pass
            print('end hotkey')
            self.user32.UnregisterHotKey(None, 1)


class EnterSendQTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.action = self.show

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            try:
                if QApplication.keyboardModifiers() in (Qt.ShiftModifier, Qt.ControlModifier, Qt.AltModifier):
                    if QApplication.keyboardModifiers() in (Qt.ControlModifier, Qt.AltModifier):
                        self.insertPlainText('\n')
                    else:
                        # print('enter')
                        pass
                else:
                    # print('returnkey')
                    self.action()
            except:
                print('回车失败', sys.exc_info())
            return
        super().keyPressEvent(e)

    def keyenter_connect(self, action):
        self.action = action


class Recordingthescreen(QObject):
    showm_signal = pyqtSignal(str)

    def __init__(self, parent):
        super(Recordingthescreen, self).__init__()
        self.parent = parent
        self.init_arearecord_thread = Commen_Thread(self.init_arearecord)
        self.init_arearecord_thread.start()
        self.timer = QTimer()
        self.timer.timeout.connect(self.count)
        self.showrect = Transparent_windows()
        self.x = 0
        self.y = 0
        self.w = self.maxw = QApplication.desktop().width() // 2 * 2
        self.h = self.maxh = QApplication.desktop().height() // 2 * 2

    def init_arearecord(self):
        self.recording = False
        self.record = None
        self.time = None
        self.t_fps = 30
        self.gif = False
        self.waiting = False
        self.stop_wait = False
        self.name = '_'
        self.file_format = 'mp4'

        self.mouse = 1
        self.fps = 30
        self.codec = 'libx264 '
        self.preset = ' ultrafast '
        self.delay = 0
        self.Nondestructive = ' -qp 5 '
        self.scale = 1
        self.c = 0
        if not os.path.exists(QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + "/Jam_screenrecord"):
            os.mkdir(QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + "/Jam_screenrecord")

    def area_recording(self):
        self.codec = 'libx264 '
        profile = ' high444 -level 5.1 '
        try:
            self.mouse = int(self.parent.mouse_rec.isChecked())
            if self.parent.hide_rec.isChecked():
                self.parent.hide()
            self.scale = self.parent.scale.value()
            self.file_format = self.parent.file_format.currentText()
            au_divice = self.parent.soundsourse.currentText()
            vi_divice = self.parent.videosourse.currentText()
            if self.gif and self.file_format != 'gif':
                self.gif = False
                self.parent.comboBox_2.setValue(self.t_fps)
            self.fps = self.parent.comboBox_2.value()
            self.preset = self.parent.preset.currentText()
            qp = self.parent.qp_rec.value()
            if qp == -1:
                self.Nondestructive = ' '
            else:
                self.Nondestructive = ' -qp {0} '.format(qp)
            self.delay = self.parent.delay_t.value()
            if self.parent.sp_rec.isChecked():
                profile = ' baseline -level 3.0 '
            if self.parent.hardware_rec.isChecked() and PLATFORM_SYS == "win32":
                profile = ' high '
                self.codec = ' h264_nvenc '

        except:
            self.init_arearecord()
            profile = ' high444 -level 5.1 '
            au_divice = '无'
            vi_divice = '抓屏'
            if len(self.parent.audio_divice) != 0:
                au_divice = self.parent.audio_divice[0]
            print(sys.exc_info(), 273)
        self.recording = True
        print(self.x, self.y, self.w, self.h)
        if not (
                self.w >= self.maxw and self.h >= self.maxh) and "camera" not in vi_divice.lower() and "摄像头" not in vi_divice.lower():
            self.showrect.setGeometry(self.x, self.y, self.w, self.h)
            self.showrect.show()
        if self.delay != 0:
            print('delay')
            self.parent.pushButton.setStyleSheet("QPushButton{background-color:rgb(200,180,10)}")
            self.waiting = True
            self.wait_()
            self.waiting = False
            if self.stop_wait:
                self.stop_wait = False
                print('stopwait')
                self.recording = False
                try:
                    self.parent.pushButton.setStyleSheet("QPushButton{color:rgb(200,100,100)}"
                                                         "QPushButton:hover{background-color:rgb(200,10,10)}"
                                                         "QPushButton:!hover{background-color:rgb(200,200,200)}"
                                                         "QPushButton{background-color:rgb(239,239,239)}"
                                                         "QPushButton{border:6px solid rgb(50, 50, 50)}"
                                                         "QPushButton{border-radius:60px}")
                except:
                    print(sys.exc_info())
                self.showm_signal.emit('录屏等待中止！')
                self.showrect.hide()
                return
        try:
            self.parent.pushButton.setStyleSheet("QPushButton{background-color:rgb(200,10,10)}"
                                                 "QPushButton{color:rgb(200,100,100)}"
                                                 "QPushButton{border:6px solid rgb(50, 50, 50)}"
                                                 )
        except:
            print(sys.exc_info(), 308)
        self.c = 0
        self.parent.counter.display('00:00')
        self.timer.start(1000)
        f_path = '"' + ffmpeg_path + '/ffmpeg" '
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        w = str(int(self.w * self.scale // 2) * 2)

        area = ' -draw_mouse {}  -offset_x {} -offset_y {} -video_size {}x{} '.format(self.mouse,
                                                                                      self.x,
                                                                                      self.y,
                                                                                      self.w,
                                                                                      self.h)
        audio = ' '
        video = '  -thread_queue_size 16 -f gdigrab -rtbufsize 500M ' + area + ' -i desktop '

        if self.file_format == 'gif':
            if self.parent.comboBox_2.value() == 30:
                self.fps = 12
                self.gif = True
                f = self.parent.comboBox_2.value()
                if f != 30:
                    self.t_fps = f
                self.parent.comboBox_2.setValue(12)
                print('rearea')

            vf = ' -vf scale=' + w + ':-2 '
            if vi_divice == '抓屏':
                if PLATFORM_SYS == "win32":
                    area = '  -draw_mouse {}  -offset_x {} -offset_y {} -video_size {}x{} '.format(
                        self.mouse,
                        self.x,
                        self.y,
                        self.w,
                        self.h)
                    video = '  -thread_queue_size 16 -f gdigrab -rtbufsize 500M ' + area + ' -i desktop '
                else:
                    video = " -video_size {}x{} -f x11grab -draw_mouse {} -i :0.0+{},{} ".format(self.w, self.h,
                                                                                                 self.mouse, self.x,
                                                                                                 self.y)
            else:
                vf = ' -vf crop={}:{}:{}:{} '.format(self.w, self.h, self.x, self.y)
                if PLATFORM_SYS == "win32":
                    video = ' -thread_queue_size 16 -f dshow -rtbufsize 500M -i video="{}"  '.format(vi_divice)
                elif PLATFORM_SYS == "darwin":
                    video = ' -thread_queue_size 16 -f avfoundation -rtbufsize 500M -i {}:  '.format(
                        self.parent.video_divice.index(vi_divice))
                self.Nondestructive = ' '

            out_file = self.Nondestructive + vf + ' -r {} -profile:v '.format(
                self.fps) + profile + '  -pix_fmt yuv420p ' \
                                      '-preset:v  ultrafast  -vcodec libx264 ' + \
                       ' "' + temp_path + '/j_temp/temp_video.mp4"'

        elif self.file_format == 'mp3':  # 音频
            video = ' '
            if au_divice != '无':
                adv = au_divice
            else:
                adv = self.parent.audio_divice[0]
            if PLATFORM_SYS == "win32":
                audio += ' -thread_queue_size 16 -f dshow -rtbufsize 50M -i audio="{0}" '.format(adv)
            elif PLATFORM_SYS == "darwin":
                audio += ' -thread_queue_size 16 -f avfoundation -rtbufsize 50M -i :{} '.format(
                    self.parent.audio_divice.index(adv))
            out_file = ' -preset:a  ' + self.preset + ' ' + QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + "/Jam_screenrecord/" + self.name + '.mp3'


        else:  # 视频

            try:
                if au_divice != '无':
                    adv = au_divice
                    if PLATFORM_SYS == "win32":
                        audio += ' -thread_queue_size 16 -f dshow -rtbufsize 50M -i audio="{0}" '.format(adv)
                    # elif PLATFORM_SYS == "darwin":
                    #     audio += ' -thread_queue_size 16 -f avfoundation -rtbufsize 50M -i :{} '.format(
                    #         self.parent.audio_divice.index(adv))
                else:
                    adv = 0
                    video = " "

            except:
                print(sys.exc_info(), 408)
            vf = ' -vf scale=' + w + ':-2 '
            if vi_divice == '抓屏':
                if PLATFORM_SYS == "win32":
                    video = '  -thread_queue_size 16 -f gdigrab -rtbufsize 500M ' + area + ' -i desktop '
                else:
                    audio = " "  # linux 暂不支持录音
                    video = " -video_size {}x{} -f x11grab -draw_mouse {} -i :0.0+{},{} ".format(self.w, self.h,
                                                                                                 self.mouse, self.x,
                                                                                                 self.y)
            else:
                if "camera" in vi_divice.lower() or "摄像头" in vi_divice.lower():  # 摄像头
                    vf = ' '
                else:
                    vf = ' -vf crop={}:{}:{}:{} '.format(self.w, self.h, self.x, self.y)
                if PLATFORM_SYS == "win32":
                    video = ' -thread_queue_size 16 -f dshow -rtbufsize 500M -i video="{}"  '.format(vi_divice)
                elif PLATFORM_SYS == "darwin":
                    video = ' -thread_queue_size 16 -f avfoundation -rtbufsize 500M -i {}:{}  '.format(
                        self.parent.video_divice.index(vi_divice),
                        self.parent.audio_divice.index(adv) if au_divice != '无' else "")
                self.Nondestructive = ' '

            #     -vf crop=1920:500:500:0
            out_file = self.Nondestructive + vf + ' -r {} -profile:v '.format(
                self.fps) + profile + '  -pix_fmt yuv420p ' \
                                      '-preset:v ' + self.preset + \
                       ' -preset:a  ' + self.preset + '  -vcodec ' + \
                       self.codec + ' ' + QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + "/Jam_screenrecord/" + self.name + '.' + self.file_format

        self.record = subprocess.Popen(
            f_path + video
            + audio
            + out_file
            + ' -y',
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        print(f_path + video
              + audio
              + out_file
              + ' -y')

    # -framerate 5 -draw_mouse 1 -show_region 1 显示截取区域 -i title={窗口名称} 用-framerate在macos下报错 用-r代替
    def recordchange(self):
        if self.waiting:
            self.stop_wait = True
            self.recording_trayicon.setVisible(False)
        elif self.recording:
            self.recording_trayicon.setVisible(False)
            if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                self.parent.show()
            self.stop_recording()
            self.showrect.hide()
        else:
            self.recording_trayicon = Recording_trayicon()
            self.recording_trayicon.show()
            self.area_recording()

    def wait_(self):
        # self.parent.pushButton.setCheckable(False)
        # self.delay += 1
        while self.delay > 0 and not self.stop_wait:
            time_text = '%02d:%02d' % (int((self.delay + 0.9) // 60), int((self.delay + 0.9) % 60))
            self.parent.counter.display(time_text)
            QApplication.processEvents()
            time.sleep(0.1)
            # print(self.delay)
            self.delay -= 0.1
            self.parent.delay_t.setValue(self.delay)

    def count(self):
        self.c += 1
        time_text = '%02d:%02d' % (self.c // 60, self.c % 60)
        self.parent.counter.display(time_text)

    def stop_recording(self):
        self.timer.stop()
        self.recording = False
        self.stop_record()
        try:
            self.parent.pushButton.setStyleSheet("QPushButton{color:rgb(200,100,100)}"
                                                 "QPushButton:hover{background-color:rgb(200,10,10)}"
                                                 "QPushButton:!hover{background-color:rgb(200,200,200)}"
                                                 "QPushButton{background-color:rgb(239,239,239)}"
                                                 "QPushButton{border:6px solid rgb(50, 50, 50)}"
                                                 "QPushButton{border-radius:60px}")
        except:
            pass
        if self.file_format != 'gif':
            self.showm_signal.emit("录屏结束，文件保存于：视频/Jam_screenrecord/" + self.name + '文件夹中\n点击此处可打开')
            self.parent.trayicon.recorded_open = True
            self.time = time.time()
            if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                self.parent.statusBar().showMessage(
                    "录屏结束，文件保存于：视频/Jam_screenrecord/" + self.name + '.' + self.file_format)
        else:
            self.showm_signal.emit('录屏结束，正在生成gif文件，请耐心等待...')
            vds = [str(temp_path + '/j_temp/temp_video.mp4')]
            self.Tr = Commen_Thread(transformater.t_video, vds, True)
            self.Tr.start()
            QApplication.processEvents()
            # transformater.t_video(vds, recording=True)

    def stop_record(self):
        self.record.stdin.write('q'.encode("GBK"))
        self.record.communicate()
        self.record.kill()


# *'XVID'MPEG-4编码 *'mp4v' *'PIMI' MPEG-1编码  *'I420'（无损压缩avi

def Tulin(text):
    print("start chat")
    if len(text) == 0:
        text = "空文本"
    info = text.encode('utf-8')
    url = 'https://api.ownthink.com/bot'
    data = {u"appid": jamtools.botappid, "spoken": info, "userid": jamtools.userid}
    try:
        response = requests.get(url, data)
        print(response.text)
        res = response.json()
        s = res['data']['info']['text']
    except:
        print('聊天出错', sys.exc_info())
        s = "聊天出错！请确保网络畅通！"

    return s


# 百度翻译
class Transtalater():
    def __init__(self, parent=None):
        self.fromLang = 'auto'
        self.toLang = 'zh'
        self.parent = parent
        self.text = ' '
        self.thread = None

    def Bdtra(self):
        print('翻译开始')

        if self.parent.screenshoter.isVisible():
            self.text = self.parent.screenshoter.shower.toPlainText()
            print('screenshoter tra', self.text)
        elif not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False,
                                                       bool) and not self.parent.simplemodebox.isVisible():
            self.parent.tra_to_edit.clear()
            self.text = self.parent.tra_from_edit.toPlainText()
            self.parent.statusBar().showMessage("翻译中，请稍后...")
        else:
            self.text = self.parent.simplemodebox.toPlainText()
        # print(text)
        if not self.text:
            self.text = "Empty text"
            print('text is empty')

        QApplication.processEvents()
        self.get_lang()

        try:
            self.thread.quit()
            self.thread.wait()
        except:
            print(sys.exc_info())
        self.thread = TrThread(self.text, self.fromLang, self.toLang)
        try:
            self.thread.change_item_signal.connect(self.parent.tra_to.setCurrentText)
            self.thread.showm_singal.connect(self.parent.statusBar().showMessage)
        except:
            print(sys.exc_info(), 586)
        self.thread.resultsignal.connect(self.translate_signal)
        self.thread.start()
        QApplication.processEvents()

    def get_lang(self):
        try:
            dictl = {'自动检测': 'auto', '中文': 'zh', '英语': 'en', '文言文': 'wyw', '粤语': 'yue', '日语': 'jp', '德语': 'de',
                     '韩语': 'kor',
                     '法语': 'fra', '俄语': 'ru', '泰语': 'th', '意大利语': 'it', '葡萄牙语': 'pt', '西班牙语': 'spa'}
            self.fromLang = dictl[self.parent.tra_from.currentText()]
            self.toLang = dictl[self.parent.tra_to.currentText()]
        except:
            print('auto')

    def show_detal(self):
        self.get_lang()
        url = 'https://fanyi.baidu.com/#' + self.fromLang + '/' + self.toLang + '/' + self.text
        QDesktopServices.openUrl(QUrl(url))

    def translate_signal(self, text):
        if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False,
                                                     bool) and not self.parent.simplemodebox.isVisible():
            self.parent.tra_to_edit.moveCursor(QTextCursor.End)
            self.parent.tra_to_edit.insertPlainText(text)
            self.parent.statusBar().showMessage("翻译完成！")
        else:
            self.parent.simplemodebox.moveCursor(QTextCursor.End)
            self.parent.simplemodebox.get_tra_resultsignal(text)
        QApplication.processEvents()


class Recording_trayicon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super(Recording_trayicon, self).__init__(parent)
        self.activated.connect(self.iconClied)
        self.setToolTip('正在录屏,点击此处结束!')
        self.setIcon(QIcon(":/recording.png"))

    def iconClied(self, e):
        print('clicked')
        jamtools.recorder.recordchange()
        # print('change')


class TrayIcon(QSystemTrayIcon):  # 系统托盘
    def __init__(self, parent=None):
        super(TrayIcon, self).__init__(parent)
        self.parent = parent
        self.showMenu()
        self.init_trayicon_thread = Commen_Thread(self.init_trayicon)
        self.init_trayicon_thread.start()
        self.show()

    def init_trayicon(self):
        self.recorded_open = False
        self.tran_open = False
        self.small_windows=[]
        self.open_path = QStandardPaths.writableLocation(
            QStandardPaths.PicturesLocation)
        self.getscreen.triggered.connect(self.parent.screensh)
        self.recordscreen.triggered.connect(self.connect_record_fun)
        self.setarea.triggered.connect(self.parent.set_area)
        self.Tray_tra.triggered.connect(self.BaiduTRA)
        self.quitAction.triggered.connect(self.jquit)
        self.OCR.triggered.connect(self.parent.BaiduOCR)
        self.chatbot.triggered.connect(self.chat)
        self.mulocr.triggered.connect(self.parent.multiocr)
        self.changesimple.setCheckable(True)
        self.changesimple.triggered.connect(self.parent.changesimple)
        self.addsimplewin.triggered.connect(self.add_simple_window)

    def connect_record_fun(self):
        self.parent.recorder.recordchange()

    def showMenu(self):
        "设计托盘的菜单，这里实现了一个二级菜单"
        self.menu = QMenu()
        self.menu1 = QMenu()
        self.menu2 = QMenu()
        self.getscreen = QAction("酱截屏", self)
        self.recordscreen = QAction("录屏", self)
        self.setarea = QAction("设定区域", self)
        self.Tray_tra = QAction("酱翻译", self)
        # self.control = QAction("酱控制", self)
        self.quitAction = QAction("退出", self)
        # self.Bdcla = QAction("图像主体识别", self)
        self.screenrecord = QAction("酱录屏", self)
        # self.screenrecord.triggered.connect(self.parent.recordscreen)
        self.OCR = QAction("截屏文字识别", self)
        self.chatbot = QAction("酱聊天", self)
        self.mulocr = QAction("批量文字提取", self)
        self.changesimple = QAction("极简模式", self)
        self.addsimplewin=QAction("添加小窗",self)

        self.menu1.addAction(self.OCR)
        self.menu1.addAction(self.mulocr)
        # self.menu1.addAction(self.Bdcla)
        self.menu.addMenu(self.menu1)

        self.menu2.addAction(self.recordscreen)
        self.menu2.addAction(self.setarea)
        self.menu.addMenu(self.menu2)

        self.menu.addAction(self.chatbot)
        self.menu.addAction(self.Tray_tra)
        self.menu.addAction(self.getscreen)
        self.menu.addAction(self.changesimple)
        self.menu.addAction(self.addsimplewin)

        self.menu.addAction(self.quitAction)
        self.menu1.setTitle("酱识图")
        self.menu2.setTitle("酱录屏")

        self.setContextMenu(self.menu)

        self.activated.connect(self.iconClied)
        # # 把鼠标点击图标的信号和槽连接
        self.messageClicked.connect(self.open_file)
        # 把鼠标点击弹出消息的信号和槽连接xccxxzcx
        self.setIcon(QIcon(":/ico.png"))
        self.icon = self.MessageIcon()

        # 设置图标
    def add_simple_window(self):
        simplemodebox = FramelessEnterSendQTextEdit(enter_tra=True,autoresetid=len(self.small_windows)+1)
        simplemodebox.show()
        simplemodebox.del_myself_signal.connect(self.small_windows.pop)
        self.small_windows.append(simplemodebox)
    def iconClied(self, e):
        "鼠标点击icon传递的信号会带有一个整形的值，1是表示单击右键，2是双击，3是单击左键，4是用鼠标中键点击"
        if e == 3:
            self.parent.changesimple()

    def open_file(self):
        now = time.time()
        if self.tran_open and transformater.open_path is not None and (now - transformater.time) < 7:
            # print(transformater.time - now)
            self.tran_open = False
            p = transformater.open_path
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
            transformater.open_path = None
        if self.recorded_open and (now - self.parent.recorder.time) < 7:
            self.recorded_open = False
            record_name = QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + "/Jam_screenrecord/" + self.parent.recorder.name + '.' + self.parent.recorder.file_format
            QDesktopServices.openUrl(QUrl.fromLocalFile(record_name))

    def BaiduTRA(self):
        if QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
            self.parent.simplemodebox.show()
        else:
            self.parent.show()
            self.parent.BaiduTRA()

    def chat(self):
        if QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
            QSettings('Fandes', 'jamtools').setValue("S_SIMPLE_MODE", False)
            self.parent.show()
        self.parent.Tulinchat()

    def JP(self):
        self.showMessage("图像数据已复制到剪切板", "可在聊天界面或画板粘贴", self.NoIcon, )

    def showM(self, message):
        if self.parent.settings.value('close_notice', False, type=bool):
            return
        self.showMessage("JamTools", message, self.icon)

    def jquit(self):
        "保险起见，为了完整的退出"
        self.setVisible(False)
        try:
            if self.parent.recorder.recording:
                self.parent.recorder.stop_record()
            if transformater.transforma is not None:
                transformater.stop_transform()
        except:
            print('kill ffmpeg errer')
        try:
            if os.path.exists('video_mergelist.txt'):
                os.remove('video_mergelist.txt')
            shutil.rmtree("j_temp")
        except:
            print("Unexpected error:", sys.exc_info()[0])
        self.parent.settings.setValue("windowy", self.parent.y())
        self.parent.settings.setValue("windowx", self.parent.x())

        os._exit(0)
        sys.exit()  # 关闭窗口


class StraThread(QThread):  # 右键画屏翻译线程
    signal = pyqtSignal(float, str, str)

    def __init__(self, w):
        super(QThread, self).__init__()
        self.w = w
        self.signal.connect(jamtools.word_extraction)

    def run(self):
        self.signal.emit(self.w,'正在识别...', '正在翻译...')
        with open("j_temp/sdf.png", 'rb')as i:
            img = i.read()
        text0 = ''
        try:
            client = AipOcr(APP_ID, API_KEY, SECRECT_KEY)
            message = client.basicGeneral(img)  # 通用文字识别，每天 50 000 次免费
            print(message)
        # message = client.basicAccurate(img)   # 通用文字高精度识别，每天 800 次免费
        except:
            print("Unexpected error:", sys.exc_info()[0])
            self.signal.emit(self.w,'Unexpected error...', str(sys.exc_info()[0]))
            return
        else:
            if message is None:
                text0="没有文字!"
            else:
                for res in message.get('words_result'):
                    text0 += res.get('words')
            self.signal.emit( self.w,  text0, '正在翻译...')
        # appid = '20190928000337891'
        # secretKey = 'SiNITAufl_JCVpk7fAUS'
        salt = str(random.randint(32768, 65536))
        sign = QSettings('Fandes', 'jamtools').value('tran_appid', '20190928000337891', str) + text0 + salt + QSettings(
            'Fandes', 'jamtools').value('tran_secretKey', 'SiNITAufl_JCVpk7fAUS', str)
        m1 = hashlib.md5()
        m1.update(sign.encode(encoding='utf-8'))
        sign = m1.hexdigest()
        # print(text0)
        if text0 != '':
            text1 = None
            myurl = '/api/trans/vip/translate' + '?appid=' + QSettings('Fandes', 'jamtools').value('tran_appid',
                                                                                                   '20190928000337891',
                                                                                                   str) + '&q=' + quote(
                text0) + '&from=' + 'auto' + '&to=' + 'zh' + '&salt=' + str(
                salt) + '&sign=' + sign
            try:
                httpClient0 = http.client.HTTPConnection('api.fanyi.baidu.com')
                httpClient0.request('GET', myurl)
                response = httpClient0.getresponse()
                s = response.read().decode('utf-8')
                s = eval(s)
                print(s)
                if s['from'] == s['to'] or s['trans_result'][0]['dst'] == s['trans_result'][0]['src']:
                    print('redo')
                    salt = str(random.randint(32768, 65536))
                    sign = QSettings('Fandes', 'jamtools').value('tran_appid', '20190928000337891',
                                                                 str) + text0 + salt + QSettings('Fandes',
                                                                                                 'jamtools').value(
                        'tran_secretKey', 'SiNITAufl_JCVpk7fAUS', str)
                    m1 = hashlib.md5()
                    m1.update(sign.encode(encoding='utf-8'))
                    sign = m1.hexdigest()
                    if s['from'] == 'zh':
                        myurl = '/api/trans/vip/translate' + '?appid=' + QSettings('Fandes', 'jamtools').value(
                            'tran_appid', '20190928000337891', str) + '&q=' + quote(
                            text0) + '&from=' + 'zh' + '&to=' + 'en' + '&salt=' + str(
                            salt) + '&sign=' + sign
                    else:
                        myurl = '/api/trans/vip/translate' + '?appid=' + QSettings('Fandes', 'jamtools').value(
                            'tran_appid', '20190928000337891', str) + '&q=' + quote(
                            text0) + '&from=' + 'en' + '&to=' + 'zh' + '&salt=' + str(
                            salt) + '&sign=' + sign
                    httpClient0.request('GET', myurl)
                    response = httpClient0.getresponse()
                    s = response.read().decode('utf-8')
                    s = eval(s)
                    print(s)
                text1 = s['trans_result'][0]['dst']
                # text1 = line['dst']
            except:
                print("Unexpected error:", sys.exc_info()[0])
            self.signal.emit(self.w,  text0, text1)
        else:
            self.signal.emit( self.w, '没有检测到文字...', '请重新操作...')


class Draw_grab_width(QLabel):
    # 划屏提字设置界面
    def __init__(self, parent):
        super(Draw_grab_width, self).__init__(parent)
        self.h = 18
        self.painter = QPainter(self)


    def paintEvent(self, event):
        self.painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
        self.painter.drawLine(0, 0, self.width(), 0)
        self.painter.drawLine(0, self.h, self.width(), self.h)
        self.painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
        self.painter.drawLine(self.width() / 2, 0, self.width() / 2, self.h)
        self.painter.drawLine(0, self.h / 2, self.width(), self.h / 2)
        self.painter.end()
        super().paintEvent(event)



class Small_Ocr(QLabel):
    def __init__(self):
        super().__init__()
        self.small_show = QTextEdit(self)
        self.smalltra = QTextEdit(self)
        self.search_botton = QPushButton('', self)
        self.pix=QPixmap()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAlignment(Qt.AlignTop)
        self.init_small_ocr_thread = Commen_Thread(self.init_small_ocr)
        self.init_small_ocr_thread.start()
        self.h = QSettings('Fandes', 'jamtools').value('grab_height', 28)
        self.sx = self.sy = self.ex = self.ey = 0

    def init_small_ocr(self):
        time.sleep(1)
        self.small_show.setPlaceholderText('文字框...')
        self.smalltra.setPlaceholderText('翻译框...')
        self.setToolTip('显示不全可向下滚动...')
        self.search_botton.clicked.connect(self.baidusearch)
        self.search_botton.setIcon(QIcon(":/search.png"))
        self.search_botton.setToolTip('跳转百度搜索')
        self.setWindowOpacity(0.8)
        self.setStyleSheet("QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                           "QPushButton:hover{color:green;background-color:rgb(200,200,100);}"
                           """QTextEdit{border:1px solid gray;
                            width:300px;
                            border-radius:5px;
                            padding:2px 4px;
                            background-color:rgb(250,250,250);}"""
                           "QScrollBar{background-color:rgb(200,100,100);width: 4px;}")

    def baidusearch(self, a=1):
        url = """https://www.baidu.com/s?wd={0}&rsv_spt=1&rsv_iqid=0xe12177a6000c90b8&issp=1&f=8&rsv_
        bp=1&rsv_idx=2&ie=utf-8&tn=94819464_hao_pg&rsv_enter=1&rsv_dl=tb&rsv_sug3=4&rsv_sug1=3
        &rsv_sug7=101&rsv_sug2=0&inputT=1398&rsv_sug4=2340""".format(self.small_show.toPlainText())
        QDesktopServices.openUrl(QUrl(url))
    def show_extrat_res(self,w, text=None, text1=None):
        self.small_show.clear()
        self.smalltra.clear()
        self.smalltra.hide()
        grabheight = self.h
        self.setPixmap(self.pix)
        self.small_show.setText(text)
        self.smalltra.setText(text1)
        self.move(self.sx, self.sy - grabheight / 2)
        font = QFont('黑体' if PLATFORM_SYS == "win32" else "", )
        self.small_show.move(0, grabheight)
        self.smalltra.move(0, grabheight * 2)
        self.search_botton.move(w, 0)
        self.search_botton.resize(grabheight, grabheight)
        font.setBold(True)
        self.small_show.setFont(font)
        self.smalltra.setFont(font)
        self.adjustSize(w)
        if text1 is not None:
            self.smalltra.show()
        self.show()
        self.small_show.show()
        self.search_botton.show()
        QApplication.processEvents()
    def adjustSize(self,w) -> None:
        td=self.smalltra.document()
        td.adjustSize()
        sd=self.small_show.document()
        sd.adjustSize()
        trawidth=td.size().width()
        show_width=sd.size().width()
        maxw=max([w,trawidth,show_width])
        self.small_show.resize(maxw + self.h, self.h)
        self.smalltra.resize(maxw + self.h, self.h)
        self.resize(maxw + self.h, self.h * 3)
        self.small_show.setDocument(sd)
        self.smalltra.setDocument(td)
        # super(Small_Ocr, self).adjustSize()
class FuncBox(QGroupBox):
    def __init__(self, parent):
        super(FuncBox, self).__init__(parent)
        self.setGeometry(QRect(176, 30, 580, 500))
        self.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 7))
        self.hide()


class ImgShower(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.setWidget(self.label)
        # self.setWidgetResizable(True)
        if os.path.exists('j_temp/jam_outputfile.png'):
            self.pix = QPixmap('j_temp/jam_outputfile.png')
            self.pix.scaled(self.pix.size(), Qt.KeepAspectRatio)
            self.label.setPixmap(self.pix)
            self.label.resize(self.pix.width(), self.pix.height())

        self.verticalScrollBar().setFixedWidth(10)
        self.horizontalScrollBar().setFixedHeight(10)
        # self.verticalScrollBar=self.verticalScrollBar()#竖直滚动条
        # self.verticalScrollBar.setFixedWidth(5)
        # self.horizontalScrollBar=self.horizontalScrollBar()
        # self.horizontalScrollBar.setFixedWidth(5)
        self.scale = 1
        self.drag = False
        self.dpos = (0, 0)
        self.setStyleSheet('border:None')

    def setpic(self, pix):
        # if os.path.exists('j_temp/jam_outputfile.png'):
        self.pix = pix
        self.pix.scaled(self.pix.size(), Qt.KeepAspectRatio)
        self.label.resize(self.pix.width(), self.pix.height())
        self.label.setPixmap(self.pix)
        self.dpos = (0, 0)

    def mousePressEvent(self, e):
        if self.isVisible():
            self.setCursor(Qt.SizeAllCursor)
            if e.button() == Qt.LeftButton:
                self.drag = True
                self.dpos = (e.x(), e.y())

    def mouseReleaseEvent(self, e):
        if self.isVisible():
            self.setCursor(Qt.ArrowCursor)
            if e.button() == Qt.LeftButton:
                self.drag = False
                # self.epos = (e.x(), e.y())

    def mouseMoveEvent(self, event):
        if self.isVisible():
            if self.drag:
                dx = event.x() - self.dpos[0]
                dy = event.y() - self.dpos[1]
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
                self.dpos = (event.x(), event.y())
                self.update()

    def wheelEvent(self, e):
        if self.isVisible():
            angleDelta = e.angleDelta() / 8
            dy = angleDelta.y()
            if dy > 0:
                self.scale += 0.1
            else:
                if self.scale > 0.1:
                    self.scale -= 0.15
            # print(self.scale, 'scale')
            try:
                self.label.resize(self.pix.width() * self.scale, self.pix.height() * self.scale)
            except:
                print('not pix')

            self.update()

    # def paintEvent(self, e):
    #     super().paintEvent(e)
    # painter = QPainter(self)
    # if self.pix:
    #     pixw, pixh = self.imgpix.width(), self.imgpix.height()
    #     larger_pix = self.imgpix.copy(self.pos[0] - pixw // 2, self.pos[1] - pixh // 2,
    #                                   pixw, pixh).scaled(
    #         120 + self.scale * 10, 120 + self.scale * 10, Qt.KeepAspectRatio)
    #     self.pix = larger_pix.copy(larger_pix.width() // 2 - self.width() // 2,
    #                                larger_pix.height() // 2 - self.height() // 2, self.width(), self.height())
    #     painter.drawPixmap(0, 0, self.pix)
    # painter.end()


# 主窗口
class Swindow(QMainWindow):
    keboardchange_fucsignal = pyqtSignal()
    showm_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        groupfont = QFont('黑体' if PLATFORM_SYS == "win32" else "", 7)
        self.settings = QSettings('Fandes', 'jamtools')
        self.main_groupBox = QGroupBox(self)
        self.main_groupBox.setGeometry(QRect(10, 30, 160, 490))
        self.main_groupBox.setTitle("主要功能")
        self.main_groupBox.setFont(groupfont)

        self.main_scroll = QScrollArea(self)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_scroll.setGeometry(QRect(10, 38, 160, 490))
        self.main_scroll.setWidget(self.main_groupBox)
        self.view_groupBox = FuncBox(self)
        self.tra_groupBox = FuncBox(self)
        self.Transforma_groupBox = FuncBox(self)
        self.ocr_groupBox = FuncBox(self)
        self.cla_groupBox = FuncBox(self)
        self.rec_groupBox = FuncBox(self)
        self.chat_groupBox = FuncBox(self)
        self.controll_groupBox = FuncBox(self)
        self.transmitter_groupBox = FuncBox(self)
        self.about_groupBox = QGroupBox("About", self)
        self.about_groupBox.setGeometry(QRect(176, 30, 580, 500))
        self.about_groupBox.setFont(groupfont)
        self.show_items = [self.view_groupBox, self.tra_groupBox, self.Transforma_groupBox, self.ocr_groupBox,
                           self.cla_groupBox, self.rec_groupBox, self.chat_groupBox,
                           self.controll_groupBox, self.about_groupBox, self.transmitter_groupBox]
        self.chatthread = None
        self.help_text = QTextEdit(self.about_groupBox)
        self.help_text.setGeometry(35, 35, 500, 444)
        self.payimg = QLabel(self.help_text)
        self.payimg.hide()

        self.counter = QLCDNumber(self.rec_groupBox)

        self.on_top = self.settings.value('win_ontop', False, type=bool)
        self.initUI()
        self.init_other()
        self.help()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.on_top)
        self.activateWindow()
        self.show()
        self.simplemodebox = FramelessEnterSendQTextEdit(enter_tra=True)
        self.actioncontroller = ActionController()
        try:
            self.WebFilesTransmitter = WebFilesTransmitter()
        except:
            print(sys.exc_info(), "端口重置")
            self.WebFilesTransmitter = WebFilesTransmitter()
        self.screenshoter = Slabel(self)
        self.hotkey = JHotkey()
        self.hotkey.start()
        self.trayicon = TrayIcon(self)
        self.recorder = Recordingthescreen(self)  # 录屏
        self.connect_all()

        self.settings.setValue("S_SIMPLE_MODE", False)

        if self.settings.value('right_ocr', False, bool):
            self.openlistenmouse()


    def init_other(self):  # 后台初始化

        self.main_scroll.setStyleSheet('''QScrollBar:vertical { 
                    border: none; 
                    background-color: rgba(255,255,255,0); 
                    width: 10px; 
                    margin: 1px 1px 1px 1px; 
                } ''')
        self.help_text.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.help_text.setReadOnly(True)

        self.delay = 0
        self.stop_wait = self.waiting = False
        self.samplingingid = -1
        # self.control_initcount = 1
        # self.recordcount = 1
        self.mulocr = self.OCR = self.ssview = self.recview = False
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.flag = self.bdocr = self.setingarea = self.transfor_view = self.controlling = self.init_transmitter = False
        # self.can_controll = self.settings.value('can_controll', False, type=bool)
        self.freeze_imgs = []
        self.audio_divice = []
        self.video_divice = []

        first_distance = 25
        s_distance = 30
        d_distance = 58
        btn_font = QFont('黑体' if PLATFORM_SYS == "win32" else "", 10)
        QToolTip.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 8))
        self.ss_btn.setToolTip('截图功能Alt+Z')
        self.ss_btn.setStatusTip('截图功能Alt+Z')
        self.ss_btn.resize(110, 35)
        self.ss_btn.setFont(btn_font)
        self.ss_btn.move(first_distance, s_distance)
        self.ss_btn.clicked.connect(self.screenshot)
        self.ss_btn.setIcon(QIcon(":/screenshot.png"))

        self.ocr_btn.setToolTip('文字识别Alt+X')
        self.ocr_btn.setStatusTip('文字识别Alt+X')
        self.ocr_btn.setFont(btn_font)
        self.ocr_btn.move(first_distance, s_distance + 1 * d_distance)
        self.ocr_btn.resize(110, 35)
        self.ocr_btn.clicked.connect(self.ocr)
        self.ocr_btn.setIcon(QIcon(":/OCR.png"))

        self.translate_btn.setToolTip('翻译功能')
        self.translate_btn.setStatusTip('翻译功能')
        self.translate_btn.setFont(btn_font)
        self.translate_btn.move(first_distance, s_distance + 2 * d_distance)
        self.translate_btn.resize(110, 35)
        self.translate_btn.clicked.connect(self.BaiduTRA)
        self.translate_btn.setIcon(QIcon(":/tra.png"))

        self.screenrecord_btn.setToolTip('选定范围后按Alt+C开始/结束录制')
        self.screenrecord_btn.setStatusTip('选定范围后按Alt+C开始/结束录制')
        self.screenrecord_btn.setFont(btn_font)
        self.screenrecord_btn.setIcon(QIcon(":/record.png"))
        self.screenrecord_btn.move(first_distance, s_distance + 3 * d_distance)
        self.screenrecord_btn.resize(110, 35)
        self.screenrecord_btn.clicked.connect(self.record_screen)

        self.transform_btn.setToolTip('多媒体格式转换')
        self.transform_btn.setStatusTip('多媒体格式转换')
        self.transform_btn.setFont(btn_font)
        self.transform_btn.move(first_distance, s_distance + 4 * d_distance)
        self.transform_btn.resize(110, 35)
        self.transform_btn.clicked.connect(self.transforma)
        self.transform_btn.setIcon(QIcon(":/switch.png"))

        self.control_btn.setToolTip('按键动作录制功能!')
        self.control_btn.setStatusTip('录制并播放你的动作!')
        self.control_btn.setFont(btn_font)
        self.control_btn.move(first_distance, s_distance + 5 * d_distance)
        self.control_btn.resize(110, 35)
        self.control_btn.clicked.connect(self.control)
        self.control_btn.setIcon(QIcon(":/Control.png"))

        self.transmitter_btn.setToolTip('局域网传输功能')
        self.transmitter_btn.setStatusTip('局域网传输功能')
        self.transmitter_btn.setFont(btn_font)
        self.transmitter_btn.move(first_distance, s_distance + 6 * d_distance)
        self.transmitter_btn.resize(110, 35)
        self.transmitter_btn.clicked.connect(self.Filestransmitter)
        self.transmitter_btn.setIcon(QIcon(":/filestransmitter.png"))

        self.chatbot_btn.setToolTip('小酱酱机器人在等你哦！')
        self.chatbot_btn.setStatusTip('小酱酱机器人在等你哦！')
        self.chatbot_btn.setFont(btn_font)
        self.chatbot_btn.move(first_distance, s_distance + 7 * d_distance)
        self.chatbot_btn.resize(110, 35)
        self.chatbot_btn.clicked.connect(self.Tulinchat)
        self.chatbot_btn.setIcon(QIcon(":/chat.png"))

        self.ocr_textEdit.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.ocr_textEdit.move(40, 35)
        self.ocr_textEdit.resize(480, 350)
        self.cla_textEdit.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.cla_textEdit.move(170, 50)
        self.cla_textEdit.resize(211, 300)

        groupfont = QFont('黑体' if PLATFORM_SYS == "win32" else "", 7)
        self.view_groupBox.setTitle("view")
        self.tra_groupBox.setTitle("Translate")
        self.Transforma_groupBox.setTitle("Transformation")
        self.ocr_groupBox.setTitle("OCR")
        self.cla_groupBox.setTitle("Distinguish")
        self.rec_groupBox.setTitle("Record")
        self.chat_groupBox.setTitle("Chat bot")
        self.controll_groupBox.setTitle("Control")
        self.transmitter_groupBox.setTitle("Transmitter")

        self.counter.setGeometry(QRect(30, 100, 120, 35))
        self.counter.display('00:00')
        self.keyboard = QApplication.clipboard()
        self.keyboard.dataChanged.connect(self.keyboardchanged)  # 剪切板翻译/智能shift
        self.setStyleSheet("QPushButton{color:black;background-color:rgb(239,239,239);padding:0px 0px;}"
                           "QPushButton:hover{color:green;background-color:rgb(200,200,100);}"
                           "QScrollBar{border:none;width:10px; background-color:rgb(200,200,200);border-radius: 8px;}"
                           """QTextEdit{
                            border:1px solid gray;
                            width:300px;
                            border-radius:10px;
                            padding:2px 4px;
                            background-color:rgb(250,250,250);}"""
                           """QComboBox{combobox-popup: 0;padding:2px 4px;background-color:rgb(250,250,250);}"""

                           """QSpinBox{padding:2px 4px;background-color:rgb(250,250,250);
                                           border:2px solid rgb(140, 140, 140);}"""
                           """QDoubleSpinBox{padding:2px 6px;background-color:rgb(250,250,250);
                            border:2px solid rgb(140, 140, 140);}"""
                           """QTimeEdit{padding:2px 6px;background-color:rgb(250,250,250);
                           border:2px solid rgb(140, 140, 140);}
                           border-radius:10px"""
                           )

        self.ocr_groupBox.setStyleSheet(
            "QScrollBar{width:10px}")
        self.tra_groupBox.setStyleSheet(
            "QScrollBar{width:10px}"
            """QComboBox{padding:2px 4px;background-color:rgb(250,250,250);}"""
        )
        self.about_groupBox.setStyleSheet("QScrollBar{border:none; background-color:rgb(200,200,200); width:5px  }")
        self.keboardchange_fucsignal.connect(self.keboardchange_fuc)
        print('initothers')

    def initUI(self):
        x, y = self.settings.value("windowx", 300, type=int), self.settings.value("windowy", 300, type=int)
        if x < 50 or x>QApplication.desktop().width():
            self.settings.setValue("windowx", 50)
            x = 50
        if y < 50 or y>QApplication.desktop().availableGeometry(0).height():
            self.settings.setValue("windowy", 50)
            y = 50

        self.setGeometry(x, y, 800, 550)
        self.setWindowTitle('JamTools {} \t\t\t\t\t\t\t\t\t 本软件完全免费，严禁贩卖！！！'.format(VERSON))
        self.setWindowIcon(QIcon(":/ico.png"))
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.setAcceptDrops(True)
        self.setFixedSize(self.width(), self.height())
        self.ss_btn = QPushButton("酱截屏", self.main_groupBox)
        self.ocr_btn = QPushButton("酱识字", self.main_groupBox)
        self.translate_btn = QPushButton("酱翻译", self.main_groupBox)
        # self.plan_btn = QPushButton("酱计划", self.main_groupBox)
        self.screenrecord_btn = QPushButton("酱录屏", self.main_groupBox)
        self.transform_btn = QPushButton("酱转换", self.main_groupBox)
        self.control_btn = QPushButton("酱控制", self.main_groupBox)
        self.transmitter_btn = QPushButton("酱传输", self.main_groupBox)
        self.chatbot_btn = QPushButton("酱聊天", self.main_groupBox)
        self.ocr_textEdit = QTextEdit(self.ocr_groupBox)
        self.cla_textEdit = QTextEdit(self.cla_groupBox)

        # 菜单栏
        menubar = self.menuBar()
        option = menubar.addMenu("选项")
        other_act = QAction('其他功能', self)
        other_act.triggered.connect(self.others)
        simplemode = QAction('极简模式', self)
        simplemode.triggered.connect(lambda x:self.changesimple(show=True))
        simplemode.setStatusTip('极简模式下不显示主窗口，可以从系统托盘退出(双击图标也可以退出！)')
        if PLATFORM_SYS == "darwin":
            othermenu = menubar.addMenu("其他")
            othermenu.addActions([other_act, simplemode])
        else:
            menubar.addAction(other_act)
            menubar.addAction(simplemode)

        help_act = QAction('帮助', self)
        help_act.triggered.connect(self.help)
        about = QAction('关于作品', self)
        about.setStatusTip("Edit by 机械酱Fandes ")
        about.triggered.connect(self.about)
        loge = QAction('更新日志', self)
        loge.triggered.connect(self.logeshow)
        update = QAction('检查更新', self)
        update.triggered.connect(self.checkforupdate)

        change_top = QAction('窗口置顶', self)
        change_top.setCheckable(True)
        change_top.setChecked(self.on_top)
        change_top.triggered.connect(self.change_top)
        change_top.setStatusTip('窗口置顶与否')
        option.addAction(change_top)

        close_notice = QAction('关闭通知', self)
        close_notice.setCheckable(True)

        def change_notice():
            try:
                self.settings.setValue('close_notice', not self.settings.value('close_notice', False, type=bool))
            except:
                print('error to save close_notice')

        close_notice.setChecked(self.settings.value('close_notice', False, type=bool))
        close_notice.triggered.connect(change_notice)
        close_notice.setStatusTip('关闭所有提示性系统通知')
        option.addAction(close_notice)

        setting = QAction('设置中心', self)
        setting.triggered.connect(self.settings_show)
        setting.setStatusTip('设置...(这是一个设置..嗯..)')
        option.addAction(setting)

        clear_all_setting = QAction('重置设置', self)
        clear_all_setting.triggered.connect(self.settings.clear)
        clear_all_setting.setStatusTip('重置所有设置为默认值，重启生效！')
        option.addAction(clear_all_setting)

        fileMenu = menubar.addMenu('关于')
        fileMenu.setToolTip("Edit by Fandes&机械酱 \n联系作者：2861114322@qq.com")
        fileMenu.addActions([help_act, about, loge, update])
        self.statusBar().setStyleSheet("color:blue;")
        # self.settings.clear()

    def connect_all(self):
        self.hotkey.running_change_signal.connect(self.start_action_run)
        self.hotkey.listening_change_signal.connect(self.start_action_listen)
        self.hotkey.ss_signal.connect(self.screensh)
        self.hotkey.ocr_signal.connect(self.BaiduOCR)
        self.hotkey.showm_signal.connect(self.trayicon.showM)
        self.hotkey.recordchange_signal.connect(self.recorder.recordchange)
        self.recorder.showm_signal.connect(self.trayicon.showM)
        self.WebFilesTransmitter.showm_signal.connect(self.trayicon.showM)
        self.connectss()
        self.showm_signal.connect(self.trayicon.showM)
        self.actioncontroller.showm_signal.connect(self.trayicon.showM)
        self.actioncontroller.return_samrate_signal.connect(self.update_samrate)


    def settings_show(self):  # 设置
        self.settingspage = SettingPage(self)

    def change_show_item(self, item):
        for i in self.show_items:
            if i in item:
                i.show()
            else:
                i.hide()

    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False

    def keyboardchanged(self):
        print('keyboardchanged')
        try:
            self.kbtralistener.stop()
            del self.kbtralistener
        except:
            print(sys.exc_info())

        self.canstartkeyboardtra = False
        self.shifttime = time.time()

        def on_press(key):
            if key == keyboard.Key.shift and self.settings.value('smartShift', True, bool)and \
                    time.time() -  self.shifttime < self.settings.value("timeoutshift", 7, type=int):
                print('shift pressed', time.time() - self.shifttime)
                self.canstartkeyboardtra = True
                self.keboardchange_fucsignal.emit()
                stopall()

        def stopall():
            self.kbtralistenertimer.stop()
            self.kbtralistener.stop()

        self.kbtralistenertimer=QTimer()
        self.kbtralistener = keyboard.Listener(on_press=on_press)
        self.kbtralistener.start()
        self.kbtralistenertimer.start(self.settings.value("timeoutshift", 7, type=int)*1000)
        self.kbtralistenertimer.timeout.connect(stopall)

    def keboardchange_fuc(self):
        data = self.keyboard.mimeData()
        rtext = data.text()
        text = re.sub(r'[^\w]', '', rtext).replace('_', '')
        print('exlister', self.canstartkeyboardtra)
        if self.canstartkeyboardtra and data.hasText() and 3000 > len(text) > 2:
            fy = 1
            if self.settings.value("openhttp", True, bool):
                a = []
                if "http" in rtext:
                    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                else:
                    pattern = r'(?:(?:[a-zA-Z]|[0-9]|\.)+(?:\.com|\.cn|\.net|\.top))|(?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(?::[0-9]+)*)'
                if self.settings.value("openhttpOnce", False, bool):
                    mat = re.match(pattern, rtext)
                    if mat:
                        a = [mat.group()]
                else:
                    a = re.findall(pattern, rtext)

                if len(a):
                    fy = 0
                    for b in a:
                        if not b.startswith("http"):
                            b = "http:" + b
                        QDesktopServices.openUrl(QUrl(b))
                    if "pan.baidu.com" in b and "提取码" in rtext:
                        a = re.search(r'提取码[:： ]*((?:[a-zA-Z]|[0-9]){4})', rtext)
                        if a:
                            QApplication.clipboard().setText(a.groups()[0])
            if self.settings.value("shiftopendir",True,bool) and (re.match("C:|D:|E:|F:|G:|H:",rtext) or "\\" in rtext or "/"in rtext) and os.path.exists(rtext.replace("\"","")):
                rtext=rtext.replace("\"","")
                if os.path.isfile(rtext):
                    rtext=os.path.split(rtext)[0]
                print("打开文件(夹)",rtext)
                QDesktopServices.openUrl(QUrl.fromLocalFile(rtext))
                return

            if self.settings.value("shiftFY", True, bool) and fy and not re.match('http|https|file:/|C:|D:|E:|F:|G:|H:',
                                                                                  rtext):
                n = 0
                for i in text:
                    if self.is_alphabet(i):
                        n += 1
                if n / len(text) > 0.4 or self.settings.value("shiftFYzh", False, bool):
                    print('is en')
                    self.simplemodebox.show()
                    self.simplemodebox.clear()
                    self.simplemodebox.insertPlainText(rtext)
                    transtalater.Bdtra()

    def change_top(self):
        if self.on_top:
            self.on_top = False
            self.settings.setValue('win_ontop', False)
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)  # 取消置顶
            self.show()
        else:
            self.on_top = True
            self.settings.setValue('win_ontop', True)
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)  # 置顶
            self.show()

    def set_area(self):
        self.setingarea = True
        self.getandshow()

    def simple_show(self, text):
        self.simplemodebox.clear()
        self.simplemodebox.insertPlainText(text)
        # self.simplemodebox.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.simplemodebox.show()

    def simple_mode(self):
        self.simplemodebox.keyenter_connect(transtalater.Bdtra)
        self.simplemodebox.setToolTip('Ctrl+回车可快速翻译!')
        self.simplemodebox.resize(250, 250)
        self.simplemodebox.setWindowOpacity(0.8)
        self.hide()

    def changesimple(self,show=False):
        print('S_SIMPLE_MODE', QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool))
        if QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
            QSettings('Fandes', 'jamtools').setValue("S_SIMPLE_MODE", False)
            self.show()
            self.raise_()
            self.activateWindow()
            self.simplemodebox.hide()
        else:
            QSettings('Fandes', 'jamtools').setValue("S_SIMPLE_MODE", True)
            self.simple_mode()
            if show:
                self.simplemodebox.show()
        self.trayicon.changesimple.setChecked(QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool))

    def setting_save(self):
        self.set_saver = Settings_save()
        self.set_saver.start()
        print('save')

    def control(self):
        if not self.controlling:
            def opendi():
                try:
                    p = documents_path + '/jam_control'
                    QDesktopServices.openUrl(QUrl.fromLocalFile(p))
                except:
                    print(sys.exc_info())

            # def listening_change():
            #     self.actioncontroller.listening_change(self.controll_delayrecord.value(),self.controll_roller.value())
            self.controller_conditions = []
            reccontrol_tap = QTabWidget(self.controll_groupBox)
            reccontrol_tap.setGeometry(20, 20, 545, 300)
            reccontrol_tap.setTabShape(QTabWidget.Triangular)
            reccontrol_tap.setStyleSheet("""QTabBar::tab{min-height: 30px; min-width: 100px;
                        background-color:rgb(250, 250, 250);}""")
            recordbox = QWidget(self.controll_groupBox)
            recordbox.setStyleSheet('background-color:rgb(250, 250, 250);')
            recordbox.setGeometry(40, 90, 510, 300)
            controlbox = QWidget(self.controll_groupBox)
            controlbox.setGeometry(40, 180, 510, recordbox.height())
            controlbox.setStyleSheet('background-color:rgb(250, 250, 250);')
            reccontrol_tap.addTab(recordbox, '录制动作')
            reccontrol_tap.addTab(controlbox, '播放动作')
            self.controlrecord = QPushButton("录制/结束\n(Alt+1)", recordbox)
            self.controlrecord.setToolTip('快捷键Alt+1;开始/结束记录你的所有动作')
            self.controlrecord.setStatusTip('快捷键Alt+1;开始/结束记录你的所有动作')
            self.controlrecord.setGeometry(10, 15, 100, 50)
            self.controlrecord.clicked.connect(self.start_action_listen)
            self.controlrun = QPushButton("播放/结束\n(Alt+2)(F4)", controlbox)
            self.controlrun.setToolTip('快捷键Alt+2;播放已录制的动作,F4强制中断播放')
            self.controlrun.setStatusTip('快捷键Alt+2;播放已录制的动作,F4强制中断播放')
            self.controlrun.setGeometry(10, 15, 100, 50)
            self.controlrun.clicked.connect(self.start_action_run)

            open_pathbtn = QPushButton('', self.controll_groupBox)
            open_pathbtn.setGeometry(self.controll_groupBox.width() - 35, 10, 35, 35)
            open_pathbtn.setIcon(QIcon(":/wjj.png"))
            open_pathbtn.clicked.connect(opendi)
            open_pathbtn.setToolTip('打开存放动作文件的文件夹，复制/替换以分享/读取')
            open_pathbtn.setStatusTip('打开存放动作文件的文件夹，复制/替换以分享/读取')
            open_pathbtn.setStyleSheet("border:none;border-radius:6px;")

            def current_itemchange(item):
                self.controller_path_shower.setText(":/文档/jam_control/{}".format(item))

            self.control_list_widget = QListWidget(self.controll_groupBox)
            self.control_list_widget.setGeometry(reccontrol_tap.x(), reccontrol_tap.y() + reccontrol_tap.height() + 10,
                                                 reccontrol_tap.width(), self.controll_groupBox.height()
                                                 - (reccontrol_tap.y() + reccontrol_tap.height() + 20))
            self.control_list_widget.setToolTip("在:/文档/jam_control/目录下的脚本文件,双击播放")
            self.control_list_widget.currentTextChanged.connect(current_itemchange)
            self.control_list_widget.doubleClicked.connect(self.start_action_run)
            self.control_list_widget.setStyleSheet('''
                QListWidget::item{
                    color:rgb(100,100,100);
                    border-bottom:1px solid rgb(52,52,52);
                    border-width:1px;}
                QListWidget::item:hover{
                    background-color:rgb(230,230,250);
                    border-width:1px;}
                QListWidget::item:selected
                {   background-color:rgb(200,200,255);
                    border-bottom:1px solid rgb(121,112,52);
                    color:black;
                    border-width:1px;
                }
               ''')

            self.controll_roller = QSpinBox(recordbox)
            self.controll_roller.setGeometry(150, 15, 150, 25)
            self.controll_roller.setPrefix('滚轮速度修正')
            self.controll_roller.setStatusTip('由于每个鼠标都不一样，需要修正滚轮滚动的速度')
            self.controll_roller.setMaximum(9999)
            self.controll_roller.setValue(120)
            self.controll_delayrecord = QDoubleSpinBox(recordbox)
            self.controll_delayrecord.setGeometry(150, 45, 150, 25)
            self.controll_delayrecord.setPrefix('倒计时')
            self.controll_delayrecord.setSuffix('秒')
            self.controll_delayrecord.setStatusTip('设置倒计时开始录制')
            self.controll_delayrecord.setMaximum(99999)

            #
            # modelbox = QGroupBox("模式:", recordbox)
            # modelbox.setGeometry(self.controll_roller.x() + self.controll_roller.width() + 10,
            #                      self.controll_roller.y() - 7, 150, 60)
            # self.controll_model=QComboBox(modelbox)
            # self.controll_model.setGeometry(10,22,modelbox.width()-20,28)
            # self.controll_model.addItems(["常规","图像匹配"])

            def choice_jamfile_path():
                jp, l = QFileDialog.getOpenFileName(self, "选择.jam脚本", QStandardPaths.writableLocation(
                    QStandardPaths.DocumentsLocation) + "/jam_control", "jam Files (*.jam);;")
                if jp:
                    self.controller_path_shower.setText(str(jp))

            pathgroupbox = QGroupBox("脚本路径", controlbox)
            pathgroupbox.setGeometry(150, 10, 350, 50)
            self.controller_path_shower = QLineEdit(pathgroupbox)
            self.controller_path_shower.setPlaceholderText(":/文档/jam_control/current.jam")
            self.controller_path_shower.setGeometry(10, 18, 280, 25)
            choice_controller_path_bot = QPushButton("•••", pathgroupbox)
            # choice_controller_path_bot.setStyleSheet('border-image: url(:/choice_path.png);')
            choice_controller_path_bot.setGeometry(
                self.controller_path_shower.width() + self.controller_path_shower.x(),
                self.controller_path_shower.y() - 2, 30, 25)
            choice_controller_path_bot.clicked.connect(choice_jamfile_path)

            self.controll_count = QSpinBox(controlbox)
            self.controll_count.setGeometry(10, 75, 120, 25)
            self.controll_count.setPrefix('播放次数 ')
            self.controll_count.setMinimum(1)
            self.controll_count.setMaximum(999)
            self.controll_delayrun = QDoubleSpinBox(controlbox)
            self.controll_delayrun.setGeometry(self.controll_count.x(), self.controll_count.y() + 30, 120, 25)
            self.controll_delayrun.setPrefix('倒计时')
            self.controll_delayrun.setSuffix('秒')
            self.controll_delayrun.setStatusTip('设置播放倒计时')
            self.controll_delayrun.setMaximum(99999)
            self.controll_speed = QDoubleSpinBox(controlbox)
            self.controll_speed.setGeometry(self.controll_count.x(), self.controll_delayrun.y() + 30, 120, 25)
            self.controll_speed.setValue(1)
            self.controll_speed.setMinimum(0.01)
            self.controll_speed.setPrefix('速度')
            self.controll_speed.setSuffix('倍')
            self.controll_speed.setStatusTip('设置播放速度')
            self.controll_speed.setMaximum(100)

            def setarea(id):
                self.samplingingid = id
                self.set_area()

            def showpix():
                try:
                    p = "j_temp/triggerpix.png"
                    if os.path.exists(p):
                        QDesktopServices.openUrl(QUrl.fromLocalFile(p))
                    else:
                        self.showm_signal.emit('查看失败,请重新取样!')
                except:
                    print(sys.exc_info())
                    self.showm_signal.emit('查看失败,请重新取样!')

            conditions_groupbox = QGroupBox("触发条件", controlbox)
            conditions_groupbox.setGeometry(pathgroupbox.x(), pathgroupbox.y() + pathgroupbox.height() + 10,
                                            pathgroupbox.width(), 195)
            self.sampling_btn = QPushButton('取样', conditions_groupbox)
            self.sampling_btn.setToolTip('从截屏中取样,区域应尽量具有特征性')
            self.sampling_btn.move(350, 75)
            # self.sampling_btn.hide()
            self.sampling_btn.clicked.connect(setarea)
            self.showsampling_btn = QPushButton('查看', conditions_groupbox)
            self.showsampling_btn.setToolTip('查看取样文件')
            self.showsampling_btn.move(400, 75)
            # self.showsampling_btn.hide()
            self.showsampling_btn.clicked.connect(showpix)
            self.sampling_label = QLabel('无取样', conditions_groupbox)
            self.sampling_label.setGeometry(350, 90, 130, 80)
            self.sampling_label.setScaledContents(True)

            def add_condition():
                condition = ActionCondition(condition_scollarea_widget, len(self.controller_conditions))
                condition_scollarea_widget.resize(condition_scollarea_widget.width(),
                                                  (condition_scollarea.height() + 20) * (
                                                          1 + len(self.controller_conditions)))
                self.actioncontroller.showrect_signal.connect(condition.showrectornot)

                condition.showm_signal.connect(self.trayicon.showM)
                condition.clicked_signal.connect(setarea)
                self.controller_conditions.append(condition)
                QApplication.processEvents()

            def remove_condition():
                if len(self.controller_conditions) <= 0:
                    self.showm_signal.emit("没有条件可以移除!")
                    return
                condition = self.controller_conditions.pop()
                condition.hide()
                self.actioncontroller.showrect_signal.disconnect(condition.showrectornot)
                del condition
                condition_scollarea_widget.resize(condition_scollarea_widget.width(),
                                                  (condition_scollarea.height() + 20) * (
                                                          1 + len(self.controller_conditions)))
                self.showm_signal.emit("已移除条件{}".format(len(self.controller_conditions)))
                if os.path.exists("j_temp/triggerpix0{}.png".format(len(self.controller_conditions))):
                    os.remove("j_temp/triggerpix0{}.png".format(len(self.controller_conditions)))
                    print("已删除样本")

            def showsamplingrectchange(a):
                for condition in self.controller_conditions:
                    condition.canshowrect = a
                    self.settings.setValue("controller/canshowrect", a)

            self.sampling_same = QDoubleSpinBox(conditions_groupbox)
            self.sampling_same.setGeometry(10, 18, 150, 25)
            self.sampling_same.setPrefix('相似度')
            self.sampling_same.setStatusTip('设置识别的相似度,相似度高于阈值即开始播放动作')
            self.sampling_same.setToolTip('设置识别的相似度,相似度高于阈值即开始播放动作')
            self.sampling_same.setMaximum(1)
            self.sampling_same.setValue(0.85)
            self.sampling_same.setSingleStep(0.1)
            # self.sampling_same.hide()
            # self.sampling_same.valueChanged.connect(diff_change)
            self.sampling_interval = QSpinBox(conditions_groupbox)
            self.sampling_interval.setGeometry(self.sampling_same.x(), self.sampling_same.y() + 30, 150, 25)
            self.sampling_interval.setPrefix('识别间隔')
            self.sampling_interval.setSuffix('ms')
            self.sampling_interval.setStatusTip('设置识别的频率,单位为ms')
            self.sampling_interval.setToolTip('设置识别的频率,单位为ms')
            self.sampling_interval.setMaximum(99999)
            self.sampling_interval.setValue(500)
            self.sampling_interval.setSingleStep(50)
            showsamplingrect = QCheckBox("显示识别框", conditions_groupbox)
            showsamplingrect.move(self.sampling_same.x() + self.sampling_same.width() + 50, self.sampling_same.y())
            showsamplingrect.stateChanged.connect(showsamplingrectchange)
            showsamplingrect.setChecked(self.settings.value("controller/canshowrect", True, type=bool))

            add_condition_bot = QPushButton(QIcon(":/add.png"), "", conditions_groupbox)
            add_condition_bot.setToolTip("添加条件")
            remove_condition_bot = QPushButton(QIcon(":/remove.png"), "", conditions_groupbox)
            remove_condition_bot.setToolTip("移除条件")
            add_condition_bot.clicked.connect(add_condition)
            remove_condition_bot.clicked.connect(remove_condition)
            add_condition_bot.setGeometry(self.sampling_interval.x() + self.sampling_interval.width() + 100,
                                          self.sampling_interval.y() - 8, 30, 30)
            remove_condition_bot.setGeometry(add_condition_bot.x() + add_condition_bot.width() + 10,
                                             add_condition_bot.y(), add_condition_bot.width(),
                                             add_condition_bot.height())

            condition_scollarea = QScrollArea(conditions_groupbox)
            condition_scollarea.move(10, self.sampling_interval.y() + self.sampling_interval.height() + 5)
            condition_scollarea.resize(conditions_groupbox.width() - 20,
                                       conditions_groupbox.height() - condition_scollarea.y() - 5)

            condition_scollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            condition_scollarea.setFixedSize(condition_scollarea.width(), condition_scollarea.height())
            condition_scollarea_widget = QWidget()
            condition_scollarea_widget.setGeometry(0, 0, condition_scollarea.width() - 30, condition_scollarea.height())
            condition_scollarea.setWidget(condition_scollarea_widget)
            # condition_scollarea.setGeometry(0,)
            # self.sampling_interval.hide()

            # self.record_and_sampling = QCheckBox('开始时取样', recordbox)
            # self.record_and_sampling.setGeometry(350, 10, 150, 25)
            # self.record_and_sampling.hide()
            # self.record_and_sampling.setToolTip('开始录制动作时取样')
            # self.record_and_sampling_area = QSpinBox(recordbox)
            # self.record_and_sampling_area.setPrefix('取样大小:')
            # self.record_and_sampling_area.setSuffix('px')
            # self.record_and_sampling_area.setMaximum(9999)
            # self.record_and_sampling_area.setGeometry(350, 40, 150, 25)
            # self.record_and_sampling_area.hide()

            add_condition()
            self.actioncontroller.record_wait_tc_signal.connect(self.controll_delayrecord.setValue)
            self.actioncontroller.run_wait_tc_signal.connect(self.controll_delayrun.setValue)
            self.actioncontroller.controlrecord_bot_stylesheet_signal.connect(self.controlrecord.setStyleSheet)
            self.actioncontroller.controlrun_bot_stylesheet_signal.connect(self.controlrun.setStyleSheet)
            self.actioncontroller.updata_control_list_signal.connect(self.updata_control_list)

            print("control/-init")
        # if self.control_initcount:
        #     self.control_initcount -= 1
        #     return
        self.controlling = True
        self.updata_control_list()
        self.change_show_item([self.controll_groupBox])

    def updata_control_list(self):
        self.control_list_widget.clear()
        paths = sorted(os.listdir(documents_path + '/jam_control'), reverse=True)
        if 'current.jam' in paths:
            self.control_list_widget.addItem('current.jam')
        self.control_list_widget.setCurrentRow(0)
        for i in paths:
            if os.path.splitext(i)[1].lower() == '.jam' and i != 'current.jam':
                self.control_list_widget.addItem(i)

    def update_samrate(self, rates):
        # print(rates)
        for i, id in enumerate(self.controlling_id):
            condition = self.controller_conditions[id]
            condition.update_samerate(rates[i])

    def start_action_listen(self):
        try:
            self.actioncontroller.listening_change(self.controll_delayrecord.value(), self.controll_roller.value())
        except AttributeError:
            self.actioncontroller.listening_change()

    def start_action_run(self, path=False):
        # if self.controll_trigger.isChecked()
        print(path,"action")
        if type(path) == str and os.path.exists(path):
            print("检测到路径")
            self.actioncontroller.running_change(path=path)
        else:
            try:
                p = self.controller_path_shower.text()
                if p[:4] == ":/文档":
                    path = p.replace(":/文档/", QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) + "/")
                else:
                    path = p
                if not os.path.exists(path) or os.path.isdir(path):
                    print("路径不存在")
                    self.showm_signal.emit("路径不存在!")
                    return
                areas = []
                pixs = []
                self.controlling_id = []
                for id, condition in enumerate(self.controller_conditions):
                    if condition.area != (0, 0, 0, 0) and condition.pix is not None and os.path.exists(condition.pix):
                        areas.append(condition.area)
                        pixs.append(condition.pix)
                        self.controlling_id.append(id)
                if len(areas) > 0:
                    print("条件触发")
                    # comparison_info = (areas, pixs, self.sampling_same.value(), self.sampling_interval.value())
                    comparison_info = {"areas": areas, "pixs": pixs, "sampling_same": self.sampling_same.value(),
                                       "dtime": self.sampling_interval.value()}
                    self.actioncontroller.running_change(execute_count=self.controll_count.value(),
                                                         speed=self.controll_speed.value(),
                                                         comparison_info=comparison_info,
                                                         path=path)
                else:
                    self.actioncontroller.running_change(delay=self.controll_delayrun.value(),
                                                         execute_count=self.controll_count.value(),
                                                         speed=self.controll_speed.value(),
                                                         path=path)
            except AttributeError:
                if os.path.exists(QStandardPaths.writableLocation(
                        QStandardPaths.DocumentsLocation) + '/jam_control/current.jam'):
                    self.actioncontroller.running_change()
                else:
                    print("没有脚本!请先录制")
                    self.showm_signal.emit("没有脚本!请先录制")
        print("exit action")

    def ocr(self):
        if not self.OCR:
            btn2 = QPushButton("截屏提取", self.ocr_groupBox)
            btn2.setToolTip('文字识别Alt+X')
            btn2.setStatusTip('文字识别Alt+X')
            btn2.setGeometry(50, 420, 100, 50)
            btn2.clicked.connect(self.BaiduOCR)
            btn2.setIcon(QIcon(":/OCR.png"))

            btn6 = QPushButton("批量识别", self.ocr_groupBox)
            btn6.setToolTip('本地上传多个图像提取文字')
            btn6.setStatusTip('本地上传多个图像提取文字')
            btn6.setGeometry(180, 420, 100, 50)
            btn6.clicked.connect(self.multiocr)
            btn6.setIcon(QIcon(":/MOCR.png"))
            self.OCR = True

        self.change_show_item([self.ocr_groupBox])

    def init_ssview(self):
        def open_png():
            try:
                p = temp_path + "/j_temp/jam_outputfile.png"
                QDesktopServices.openUrl(QUrl.fromLocalFile(p))
                # if PLATFORM_SYS == "darwin":
                #     subprocess.call(["open", p])
                # elif PLATFORM_SYS == "win32":
                #     os.startfile(p)
                # else:
                #     subprocess.call(["xdg-open", p])
            except:
                print(sys.exc_info())
                self.statusBar().showMessage('找不到文件，请先截图！')

        def save_png():
            if os.path.exists("j_temp/jam_outputfile.png"):
                img = QImage("j_temp/jam_outputfile.png")  # 创建图片实例
                try:
                    file_path = QFileDialog.getSaveFileName(self, "save file", QStandardPaths.writableLocation(
                        QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP)"
                                                          ";;all files(*.*)")
                    img.save(file_path[0])
                except:
                    print(sys.exc_info())
                    self.statusBar().showMessage('找不到文件，请先截图！')

        def ocr_png():
            if os.path.exists("j_temp/jam_outputfile.png"):
                try:
                    self.bdocr = True
                    self.BaiduOCR()
                except:
                    print(sys.exc_info())
                    self.statusBar().showMessage('找不到文件，请先截图！')

        # def cla_png():
        #     if os.path.exists("j_temp/jam_outputfile.png"):
        #         try:
        #             self.bdcla = True
        #             self.BDimgcla()
        #         except:
        #             self.statusBar().showMessage('找不到文件，请先截图！')

        def open_path():
            p = QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + '/JamPicture/screenshot/'
            if not os.path.exists(p):
                os.mkdir(p)
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

        self.open_png = QCheckBox(self.view_groupBox)
        self.open_png.setChecked(self.settings.value('screenshot/open_png', False, type=bool))
        self.open_png.setText('截屏后打开')
        self.open_png.setToolTip('截屏后用默认软件打开/编辑')
        self.open_png.setStatusTip('截屏后用默认软件打开/编辑')
        self.open_png.setGeometry(150, 440, 125, 25)
        self.open_png.stateChanged.connect(self.setting_save)

        self.ss_timer = QDoubleSpinBox(self.view_groupBox)
        self.ss_timer.setToolTip('截屏倒计时')
        self.ss_timer.setPrefix('倒计时')
        self.ss_timer.setSuffix('s')
        self.ss_timer.setMaximum(99999)
        self.ss_timer.setStatusTip('截屏倒计时')
        self.ss_timer.setGeometry(150, 340, 125, 25)

        self.ss_areathreshold = QSpinBox(self.view_groupBox)
        self.ss_areathreshold.setToolTip('自动识别面积阈值,自动选择大于该值的内容')
        self.ss_areathreshold.setPrefix('识别阈值:')
        self.ss_areathreshold.setSuffix('px^2')
        self.ss_areathreshold.setMaximum(99999)
        self.ss_areathreshold.setValue(200)
        self.ss_areathreshold.setStatusTip('自动识别面积阈值,自动选择大于该值的内容')
        self.ss_areathreshold.setGeometry(150, 380, 125, 25)

        self.save_png = QCheckBox(self.view_groupBox)
        self.save_png.setChecked(self.settings.value('screenshot/save_png', False, type=bool))
        self.save_png.setText('自动保存文件')
        self.save_png.setToolTip('截屏后将自动保存文件')
        self.save_png.setStatusTip('截屏后将自动保存文件到系统图片文件夹中，点击右上角图标可以打开该文件夹')
        self.save_png.setGeometry(150, 460, 125, 25)
        self.save_png.stateChanged.connect(self.setting_save)

        self.hide_ss = QCheckBox(self.view_groupBox)
        # print(self.settings.value('screenshot/hide_ss', True, type=bool))
        self.hide_ss.setChecked(self.settings.value('screenshot/hide_ss', True, type=bool))
        self.hide_ss.setText('隐藏该窗口')
        self.hide_ss.setToolTip('点击截屏时窗口隐藏')
        self.hide_ss.setStatusTip('点击截屏时窗口隐藏')
        self.hide_ss.setGeometry(150, 420, 125, 25)
        self.hide_ss.stateChanged.connect(self.setting_save)

        copy_groupbox = QGroupBox(self.view_groupBox)
        copy_groupbox.setGeometry(30, 320, 100, 50)
        copy_groupbox.setTitle('截屏后复制:')
        self.copy_type_ss = QComboBox(copy_groupbox)
        self.copy_type_ss.move(10, 20)
        self.copy_type_ss.addItems(['图像数据', '图像文件', '无'])
        self.copy_type_ss.setCurrentText(self.settings.value('screenshot/copy_type_ss', '图像数据', type=str))
        self.copy_type_ss.currentTextChanged.connect(self.setting_save)
        self.copy_type_ss.setToolTip('设置截屏后剪切板可以直接粘贴的格式')
        self.copy_type_ss.setStatusTip('"图像数据"只能在聊天窗口/画板粘贴，"图像文件"则作为文件复制/移动/粘贴使用')

        open_pathbtn = QPushButton('', self.view_groupBox)
        open_pathbtn.setGeometry(self.view_groupBox.width() - 30, 10, 30, 30)
        open_pathbtn.setIcon(QIcon(":/wjj.png"))
        open_pathbtn.setStyleSheet("border:none;border-radius:6px;")
        open_pathbtn.clicked.connect(open_path)
        open_pathbtn.setToolTip('打开截图文件夹')
        open_pathbtn.setStatusTip('打开截图文件夹')

        # self.ss_scrollarea=QScrollArea(self.view_groupBox)
        # self.ss_scrollarea.setGeometry(30, 30, 420, 280)
        # self.ss_scrollarea.setAlignment(Qt.AlignCenter)
        self.ss_imgshower = ImgShower(self.view_groupBox)
        # self.ss_imgshower = QLabel(self.ss_scrollarea)
        # self.ss_scrollarea.setWidget(self.ss_scrollarea)
        self.ss_imgshower.setGeometry(30, 30, 430, 280)

        btn1 = QPushButton(" 截  屏\n(Alt+z)", self.view_groupBox)
        btn1.setToolTip('截图功能Alt+Z')
        btn1.setStatusTip('截图功能Alt+Z，滚动截屏下按左键或移走鼠标自动停止')
        btn1.setGeometry(30, 380, 100, 100)
        btn1.clicked.connect(self.screensh)
        # btn1.setShortcut('Alt+Z')
        btn1.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 10))
        btn1.setIcon(QIcon(":/screenshot.png"))
        btn1.setStyleSheet(
            "QPushButton:hover{background-color:rgb(200,200,50)}"
            "QPushButton:!hover{background-color:rgb(100,200,100)}"
        )

        roll_ss_box = QGroupBox(self.view_groupBox)
        roll_ss_box.setGeometry(300, 320, 250, 160)
        roll_ss_box.setTitle('滚动截屏参数')
        text = QLabel(roll_ss_box)
        self.roll_nfeatures = QSpinBox(roll_ss_box)
        self.roll_nfeatures.setGeometry(80, 30, 70, 20)
        self.roll_nfeatures.setMinimum(200)
        self.roll_nfeatures.setMaximum(99999)
        self.roll_nfeatures.setValue(self.settings.value('screenshot/roll_nfeatures', 500, type=int))
        self.roll_nfeatures.valueChanged.connect(self.setting_save)
        self.roll_nfeatures.setStatusTip('设置在寻找拼接位置时每张图片的最大特征点数，该值越大，拼接越慢，准确率越高！')
        self.roll_nfeatures.setToolTip('设置在寻找拼接位置时每张图片的最大特征点数，该值越大，拼接越慢，准确率越高！')
        text.move(10, self.roll_nfeatures.y())
        text.setText('特征点数')

        text = QLabel(roll_ss_box)
        self.roll_speed = QSpinBox(roll_ss_box)
        self.roll_speed.setGeometry(80, self.roll_nfeatures.y() + 30, 70, 20)
        self.roll_speed.setValue(self.settings.value('screenshot/roll_speed', 10, type=int))
        self.roll_speed.setMinimum(1)
        self.roll_speed.setMaximum(50)
        self.roll_speed.valueChanged.connect(self.setting_save)
        self.roll_speed.setStatusTip('设置自动滚动的速度，单位(行/滚轮单位)')
        text.move(10, self.roll_speed.y())
        text.setText('滚动速度')

        btn2 = QPushButton("另存为", self.view_groupBox)
        btn2.setToolTip('保存图片另存为文件')
        btn2.setStatusTip('另存为图片文件')
        btn2.setGeometry(475, 50, 80, 30)
        btn2.clicked.connect(save_png)
        btn2 = QPushButton("打开", self.view_groupBox)
        btn2.setToolTip('用默认软件打开')
        btn2.setStatusTip('打开以编辑图片')
        btn2.setGeometry(475, 80, 80, 30)
        btn2.clicked.connect(open_png)
        btn2 = QPushButton("OCR", self.view_groupBox)
        btn2.setToolTip('跳转文字识别功能')
        btn2.setStatusTip('提取图片中的文字')
        btn2.setGeometry(475, 110, 80, 30)
        btn2.clicked.connect(ocr_png)

    def screenshot(self, a=0):

        if not self.ssview:
            self.init_ssview()
            self.ssview = True

        self.change_show_item([self.view_groupBox])

    def transforma(self):

        if not self.transfor_view:

            def choice_pic():
                pic, l = QFileDialog.getOpenFileNames(self, "选择图片", QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                                      ";;all files(*.*)")

                if len(pic) != 0:
                    self.transforma_thread = Commen_Thread(transformater.piccut, pic)
                    self.transforma_thread.start()
                    # transforma_thread.wait()
                    QApplication.processEvents()

            def choice_pics():
                pics, l = QFileDialog.getOpenFileNames(self, "选择多张图片", QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                                      ";;all files(*.*)")
                if len(pics) != 0:
                    self.transforma_thread = Commen_Thread(transformater.picSplicing, pics)
                    self.transforma_thread.start()
                    QApplication.processEvents()

            def choice_vd():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    vd, l = QFileDialog.getOpenFileName(self, "选择视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation), "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                        ";;all files(*.*)")
                    if len(vd) != 0:
                        self.transforma_thread = Commen_Thread(transformater.video_cut, vd)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_vds():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    vds, l = QFileDialog.getOpenFileNames(self, "选择多个视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation),
                                                          "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                          ";;all files(*.*)")
                    if len(vds) != 0:
                        self.transforma_thread = Commen_Thread(transformater.video_merge, vds)
                        self.transforma_thread.start()
                        # transforma_thread.wait()
                        QApplication.processEvents()

            def choice_ad():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    ad, l = QFileDialog.getOpenFileName(self, "选择音频", QStandardPaths.writableLocation(
                        QStandardPaths.MusicLocation),
                                                        "video Files (*.MP3 *.WAV *.FLAC *.AAC *.Real Media *.MIDI *.OGG *.amr)"
                                                        ";;all files(*.*)")
                    if len(ad) != 0:
                        self.transforma_thread = Commen_Thread(transformater.audio_cut, ad)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_ads():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    ads, l = QFileDialog.getOpenFileNames(self, "选择多个音频", QStandardPaths.writableLocation(
                        QStandardPaths.MusicLocation),
                                                          "video Files (*.MP3 *.WAV *.FLAC *.AAC *.Real Media *.MIDI *.OGG *.amr)"
                                                          ";;all files(*.*)")
                    if len(ads) != 0:
                        self.transforma_thread = Commen_Thread(transformater.audio_Splicing, ads)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_t_ads():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    ads, l = QFileDialog.getOpenFileNames(self, "选择多个音频", QStandardPaths.writableLocation(
                        QStandardPaths.MusicLocation),
                                                          "video Files (*.MP3 *.WAV *.WMA *.FLAC *.AAC *.Real Media  *.OGG *.amr)"
                                                          ";;all files(*.*)")
                    if len(ads) != 0:
                        self.transforma_thread = Commen_Thread(transformater.t_audio, ads)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_t_vds():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    vds, l = QFileDialog.getOpenFileNames(self, "选择多个视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation),
                                                          "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                          ";;all files(*.*)")
                    if len(vds) != 0:
                        self.transforma_thread = Commen_Thread(transformater.t_video, vds)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_t_gifs():
                if transformater.gifzip_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('处理中，请耐心等待！')
                else:
                    gifs, l = QFileDialog.getOpenFileNames(self, "选择多个gif", QStandardPaths.writableLocation(
                        QStandardPaths.PicturesLocation), "gif Files (*.gif)"
                                                          ";;all files(*.*)")
                    if len(gifs) != 0:
                        self.transforma_thread = Commen_Thread(transformater.gifzip, gifs)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            self.traforma_tab = QTabWidget(self.Transforma_groupBox)
            # self.traforma_tab.setTabShape(QTabWidget.Triangular)
            self.traforma_tab.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
            self.traforma_tab.setStyleSheet("""QTabBar::tab{min-height: 30px; min-width: 100px;}""")
            self.tab1 = QWidget()
            self.tab1.setStyleSheet("background-color:rgb(240,240,240)")
            # self.tab1.setGeometry(QRect(30, 290, 120, 120))
            self.tab2 = QWidget()
            self.tab2.setStyleSheet("background-color:rgb(240,240,240)")
            # self.tab3 = QWidget()
            self.tab3 = QWidget()
            self.tab3.setStyleSheet("background-color:rgb(240,240,240)")

            self.traforma_tab.setGeometry(QRect(0, 25, 580, 475))
            self.traforma_tab.addTab(self.tab1, '裁剪/拼接')
            self.traforma_tab.addTab(self.tab2, '压缩/转码')
            # self.traforma_tab.addTab(self.tab3, '转码')
            self.traforma_tab.addTab(self.tab3, '提取/混合')
            toolbox = QToolBox(self.tab1)
            toolbox.setStyleSheet('background-color:rgb(240,240,240);')
            toolbox.setGeometry(10, 10, 550, 410)
            # layout.addWidget(toolbox, 0, 0)
            cut_pic = QWidget()

            # cut_pic.setLayout()
            toolbox.addItem(cut_pic, "图片裁剪")
            self.piccut_pushButton = QPushButton(cut_pic)
            self.piccut_pushButton.setGeometry(20, 20, 100, 30)
            self.piccut_pushButton.setText("裁剪图片")
            self.piccut_pushButton.setToolTip("根据右侧参数裁剪图片")
            self.piccut_pushButton.setStatusTip("根据右侧参数裁剪图片")
            self.piccut_pushButton.clicked.connect(choice_pic)
            self.picSplicing_pushButton = QPushButton(cut_pic)
            self.picSplicing_pushButton.setGeometry(20, 80, 100, 30)
            self.picSplicing_pushButton.setText("拼接图片")
            self.picSplicing_pushButton.setStatusTip("根据右侧参数拼接图片")
            self.picSplicing_pushButton.clicked.connect(choice_pics)
            self.piccut_spnu = QSpinBox(cut_pic)
            self.piccut_spnu.setPrefix('水平均分')
            self.piccut_spnu.setSuffix('份')
            self.piccut_spnu.setStatusTip('设置水平划分的份数')
            self.piccut_spnu.move(150, 20)
            self.piccut_spnu.setMinimum(1)
            self.piccut_spnu.setMaximum(9999)
            self.piccut_spnu.setValue(3)
            self.piccut_sznu = QSpinBox(cut_pic)
            self.piccut_sznu.setPrefix('竖直均分')
            self.piccut_sznu.setStatusTip('设置竖直划分的份数')
            self.piccut_sznu.setSuffix('份')
            self.piccut_sznu.move(300, 20)
            self.piccut_sznu.setMinimum(1)
            self.piccut_sznu.setMaximum(9999)
            self.piccut_sznu.setValue(3)
            self.hx = QRadioButton(cut_pic)
            self.zx = QRadioButton(cut_pic)
            self.hx.move(150, 85)
            self.zx.move(280, 85)
            self.hx.setText('横向拼接')
            self.zx.setText('纵向拼接')
            self.zx.setChecked(True)
            self.picgsh = QCheckBox(cut_pic)
            self.picgsh.setChecked(True)
            self.picgsh.move(400, 85)
            self.picgsh.setText('格式化宽度')
            self.picgsh.setStatusTip('自动等比例拉伸图片以适应长/宽')

            cut_vd = QWidget()
            toolbox.addItem(cut_vd, "视频裁剪")
            self.video_cut_pushButton = QPushButton(cut_vd)
            self.video_cut_pushButton.setGeometry(20, 20, 100, 30)
            self.video_cut_pushButton.setText("视频裁剪")
            self.video_cut_pushButton.setToolTip('根据右侧参数裁剪视频')
            self.video_cut_pushButton.setStatusTip('根据右侧参数裁剪视频')
            self.video_cut_pushButton.clicked.connect(choice_vd)
            self.vd_cutform = QTimeEdit(cut_vd)
            self.vd_cutform.move(150, 20)
            self.vd_cutform.setDisplayFormat("从HH:mm:ss")
            self.vd_cutto = QTimeEdit(cut_vd)
            self.vd_cutto.move(300, 20)
            self.vd_cutto.setDisplayFormat("到HH:mm:ss")
            self.vd_cutto.setStatusTip('设置为00:00:00时取原长')
            # self.vd_cutto.setMinimumTime(QTime(00, 00, 1))

            self.video_merge_pushButton = QPushButton(cut_vd)
            self.video_merge_pushButton.setGeometry(20, 80, 100, 30)
            self.video_merge_pushButton.setText("视频拼接")
            self.video_merge_pushButton.setToolTip('顺序输入多个视频并拼接')
            self.video_merge_pushButton.setStatusTip('顺序输入多个视频并拼接')
            self.video_merge_pushButton.clicked.connect(choice_vds)

            cut_au = QWidget()
            toolbox.addItem(cut_au, "音频裁剪")
            self.audio_cut_pushButton = QPushButton(cut_au)
            self.audio_cut_pushButton.setGeometry(20, 20, 100, 30)
            self.audio_cut_pushButton.setText("音频裁剪")
            self.audio_cut_pushButton.setStatusTip('裁剪音频')
            self.audio_cut_pushButton.clicked.connect(choice_ad)
            self.ad_cutform = QTimeEdit(cut_au)
            self.ad_cutform.move(150, 20)
            self.ad_cutform.setDisplayFormat("从HH:mm:ss")
            self.ad_cutto = QTimeEdit(cut_au)
            self.ad_cutto.move(300, 20)
            self.ad_cutto.setDisplayFormat("到HH:mm:ss")
            self.ad_cutto.setStatusTip('设置为00:00:00时取原长')
            # self.ad_cutto.setMinimumTime(QTime(00, 00, 1))
            self.audio_Splicing_pushButton = QPushButton(cut_au)
            self.audio_Splicing_pushButton.setGeometry(20, 80, 100, 30)
            self.audio_Splicing_pushButton.setText("音频拼接")
            self.audio_Splicing_pushButton.setToolTip('只能拼接相同格式的音频')
            self.audio_Splicing_pushButton.setStatusTip('只能拼接相同格式的音频')
            self.audio_Splicing_pushButton.clicked.connect(choice_ads)

            toolbox = QToolBox(self.tab2)
            toolbox.setStyleSheet('background-color:rgb(240,240,240);')
            toolbox.setGeometry(10, 10, 550, 420)
            # layout.addWidget(toolbox, 0, 0)
            self.t_pic = QWidget()
            toolbox.addItem(self.t_pic, "图片")
            self.t_video = QWidget()
            toolbox.addItem(self.t_video, "视频")
            self.t_audio = QWidget()
            toolbox.addItem(self.t_audio, "音频")
            self.t_gif = QWidget()
            toolbox.addItem(self.t_gif, "Gif")

            t_pic_box = QGroupBox("图片格式化", self.t_pic)
            t_pic_box.setGeometry(10, 0, 520, 120)
            self.t_pic_pushButton = QPushButton(t_pic_box)
            self.t_pic_pushButton.setGeometry(5, 18, 100, 30)
            self.t_pic_pushButton.setText("选择文件")
            self.t_pic_pushButton.setToolTip('可以选择多张，请先调整参数')
            self.t_pic_pushButton.setStatusTip('可以选择多张，请先调整参数')
            self.t_pic_pushButton.clicked.connect(choice_pics)
            self.t_pic_sp = QSpinBox(t_pic_box)
            self.t_pic_sp.setMaximum(999999)
            self.t_pic_sp.setPrefix('宽')
            self.t_pic_sp.setSuffix('px')
            self.t_pic_sp.setValue(1920)
            self.t_pic_sp.setGeometry(230, self.t_pic_pushButton.y(), 100, 25)
            self.t_pic_sz = QSpinBox(t_pic_box)
            self.t_pic_sz.setMaximum(999999)
            self.t_pic_sz.setPrefix('高')
            self.t_pic_sz.setSuffix('px')
            self.t_pic_sz.setGeometry(self.t_pic_sp.x(), self.t_pic_sp.y() + self.t_pic_sp.height(),
                                      self.t_pic_sp.width(), self.t_pic_sp.height())
            self.t_pic_sz.setValue(1080)
            self.t_pic_rotate = QSpinBox(t_pic_box)
            self.t_pic_rotate.setMaximum(360)
            self.t_pic_rotate.setPrefix('旋转')
            self.t_pic_rotate.setSuffix('°')
            self.t_pic_rotate.setGeometry(self.t_pic_sz.x(), self.t_pic_sz.y() + self.t_pic_sz.height(),
                                          self.t_pic_sp.width(), self.t_pic_sp.height())
            self.t_pic_rotate.setValue(0)

            pic_format_box = QGroupBox("输出格式", t_pic_box)
            pic_format_box.setGeometry(350, self.t_pic_sp.y() - 6, 100, 45)
            self.t_pic_format = QComboBox(pic_format_box)
            self.t_pic_format.addItems(["jpg", "png", "BMP", "ico"])
            self.t_pic_format.setGeometry(10, 15, pic_format_box.width() - 20, 25)
            # self.t_pic_format.currentText()

            self.t_pic_quality = QSpinBox(t_pic_box)
            self.t_pic_quality.setMaximum(360)
            self.t_pic_quality.setPrefix('质量:')
            self.t_pic_quality.setToolTip("设置输出的图片质量")
            self.t_pic_quality.setGeometry(pic_format_box.x() + 10, self.t_pic_rotate.y(),
                                           self.t_pic_sp.width() - 10, self.t_pic_sp.height())
            self.t_pic_quality.setValue(80)

            def change_resolution(a):
                self.t_pic_sp.setEnabled(bool(a))
                self.t_pic_sz.setEnabled(bool(a))
                self.t_pic_bc.setEnabled(bool(a))

            self.t_pic_changesize = QCheckBox(t_pic_box)
            self.t_pic_changesize.move(self.t_pic_sp.x() - 110, self.t_pic_sp.y())
            self.t_pic_changesize.setText('改变分辨率')
            self.t_pic_changesize.setToolTip('支持等比例缩放，选中则只需设置宽度大小')
            self.t_pic_changesize.setStatusTip('支持等比例缩放，选中则只需设置宽度大小')
            self.t_pic_changesize.stateChanged.connect(change_resolution)

            self.t_pic_bc = QCheckBox(t_pic_box)
            self.t_pic_bc.move(self.t_pic_changesize.x(), self.t_pic_changesize.y() + self.t_pic_changesize.height())
            self.t_pic_bc.setText('保持横纵比')
            self.t_pic_bc.setToolTip('支持等比例缩放，选中则只需设置宽度大小')
            self.t_pic_bc.setStatusTip('支持等比例缩放，选中则只需设置宽度大小')
            self.t_pic_bc.stateChanged.connect(lambda a: self.t_pic_sz.setEnabled(not bool(a)))
            self.t_pic_bc.setChecked(True)
            self.t_pic_changesize.setChecked(False)
            change_resolution(False)

            t_qr_groupbox = QGroupBox("二维码生成", self.t_pic)
            t_qr_groupbox.setGeometry(10, 120, 250, 180)
            self.t_qr_data = EnterSendQTextEdit(t_qr_groupbox)
            self.t_qr_data.keyenter_connect(transformater.qr_code)
            self.t_qr_data.setPlaceholderText('在此输入文本内容如网址等')
            self.t_qr_data.setGeometry(5, 18, 240, 120)
            self.t_qr_data.setToolTip('需要转化的数据，可以为文本或网址')
            self.t_qr_data.setStatusTip('需要转化的数据，可以为文本或网址')
            self.t_qr_pushButton = QPushButton(t_qr_groupbox)
            self.t_qr_pushButton.setGeometry(5, self.t_qr_data.height() + 18, 100, 26)
            self.t_qr_pushButton.setText("开始合成")
            self.t_qr_pushButton.setToolTip('生成二维码')
            self.t_qr_pushButton.setStatusTip('生成二维码')
            self.t_qr_pushButton.clicked.connect(transformater.qr_code)
            self.t_qr_version = QSpinBox(t_qr_groupbox)
            # self.t_videoscale.setMaximum(10)
            self.t_qr_version.setPrefix('大小级别')
            self.t_qr_version.setStatusTip('设置二维码的大小级别，0为自动大小；但数据量过大时也会自动增加二维码大小')
            self.t_qr_version.setGeometry(112, self.t_qr_pushButton.y(), 132, 26)
            self.t_qr_version.setMaximum(40)

            t_video_box = QGroupBox(self.t_video)
            t_video_box.setGeometry(15, 10, 510, 200)
            self.t_video_pushButton = QPushButton(self.t_video)
            self.t_video_pushButton.setGeometry(20, 20, 120, 120)
            self.t_video_pushButton.setText("开始/选择视频")
            self.t_video_pushButton.setToolTip('可以选择多个视频，请先调整好参数')
            self.t_video_pushButton.setStatusTip('可以选择多个视频，请先调整好参数')
            self.t_video_pushButton.clicked.connect(choice_t_vds)

            def choice_to_clear_logo():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    vd, l = QFileDialog.getOpenFileName(self, "选择视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation), "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                        ";;all files(*.*)")
                    if len(vd) != 0:
                        self.transforma_thread = Commen_Thread(transformater.clear_logo, vd)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_to_add_logo():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    if transformater.add_logo_path == '':
                        transformater.reset_style(jamtools.add_logo_pushbutton)
                        self.showm_signal.emit('请先选择水印文件！')
                        return
                    vd, l = QFileDialog.getOpenFileName(self, "选择视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation), "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                        ";;all files(*.*)")
                    if len(vd) != 0:
                        self.transforma_thread = Commen_Thread(transformater.add_logo, vd)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_logo():
                pic, l = QFileDialog.getOpenFileName(self, "选择多张图片", QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.gif *.JPEG *.BMP *.ICO)"
                                                      ";;all files(*.*)")
                if len(pic) != 0:
                    transformater.add_logo_path = pic
                    self.statusBar().showMessage('已选择水印文件为：' + pic)
                    # self.showm_signal.emit()

            logo_box = QGroupBox(self.t_video)
            logo_box.setGeometry(15, 223, 510, 65)
            self.clear_logo_pushbutton = QPushButton(self.t_video)
            self.clear_logo_pushbutton.setGeometry(20, 230, 70, 25)
            self.clear_logo_pushbutton.setText("去水印")
            self.clear_logo_pushbutton.setToolTip('去除视频水印,请先调整右侧参数！')
            self.clear_logo_pushbutton.setStatusTip('去除视频水印,请先调整右侧参数')
            self.clear_logo_pushbutton.clicked.connect(choice_to_clear_logo)
            self.add_logo_pushbutton = QPushButton(self.t_video)
            self.add_logo_pushbutton.setGeometry(20, 260, 70, 25)
            self.add_logo_pushbutton.setText("加水印")
            self.add_logo_pushbutton.setToolTip('添加视频水印,支持gif,请先调整右侧参数')
            self.add_logo_pushbutton.setStatusTip('添加视频水印，支持gif,请先调整右侧参数')
            self.add_logo_pushbutton.clicked.connect(choice_to_add_logo)
            add_logo = QPushButton(self.t_video)
            add_logo.setGeometry(160, 260, 110, 25)
            add_logo.setText("选择水印")
            add_logo.setToolTip('选择要添加到视频的水印，注意大小')
            add_logo.setStatusTip('选择要添加到视频的水印，注意大小！')
            add_logo.clicked.connect(choice_logo)
            self.clear_logo_test = QCheckBox(self.t_video)
            self.clear_logo_test.setText('调试框')
            self.clear_logo_test.setToolTip('开启调试绿框以定位水印')
            self.clear_logo_test.setStatusTip('开启调试绿框以定位水印')
            self.clear_logo_test.move(450, 230)
            # self.t_video.setStyleSheet('QTextEdit{border:1px solid gray;}')
            self.clear_logo_pos = QLineEdit(self.t_video)
            self.clear_logo_pos.setGeometry(160, 230, 110, 23)
            self.clear_logo_pos.setPlaceholderText('坐标:如20x40')
            self.clear_logo_pos.setStatusTip('视频中要去除的水印的位置(左上角为原点)')
            self.clear_logo_size = QLineEdit(self.t_video)
            self.clear_logo_size.setGeometry(330, 230, 110, 23)
            self.clear_logo_size.setPlaceholderText('大小:如200X50')
            self.clear_logo_size.setStatusTip('视频中要去除的水印的大小')
            self.add_logo_pos = QLineEdit(self.t_video)
            self.add_logo_pos.setGeometry(330, 260, 110, 23)
            self.add_logo_pos.setPlaceholderText('坐标:如20x40')
            self.add_logo_pos.setStatusTip('设置水印添加到的位置(大小已由选择的水印图片决定)')

            groupBox_2 = QGroupBox(self.t_video)
            groupBox_2.setGeometry(QRect(320, 20, 120, 51))
            groupBox_2.setTitle("输出容器")
            groupBox_2.setStatusTip('设定输出文件格式，注意与支持的编码相对应。')
            self.t_videofile_format = QComboBox(groupBox_2)
            self.t_videofile_format.setGeometry(QRect(10, 20, 100, 22))
            items_format = ['mp4', 'flv', 'gif', 'mkv', 'TS', 'wmv', 'mov', 'm4v', 'avi']
            self.t_videofile_format.addItems(items_format)
            groupBox_3 = QGroupBox(self.t_video)
            groupBox_3.setGeometry(QRect(150, 20, 120, 51))
            groupBox_3.setTitle("压缩编码")
            groupBox_3.setStatusTip('设定压缩编码，注意与支持的容器格式相对应')
            self.t_code_format = QComboBox(groupBox_3)
            self.t_code_format.setGeometry(QRect(10, 20, 100, 22))
            items_format = ['自动选择', 'H.264', 'H.265', 'MPEG-4', 'WMV1', 'WMV2']
            self.t_code_format.addItems(items_format)
            groupBox_4 = QGroupBox(self.t_video)
            groupBox_4.setGeometry(QRect(320, 70, 120, 51))
            groupBox_4.setTitle("编码速率")
            groupBox_4.setStatusTip('影响文件压缩比，编码速率越快文件体积越大，压缩比越小，处理越快，空间占用越大')
            self.t_preset_format = QComboBox(groupBox_4)
            self.t_preset_format.setGeometry(QRect(10, 20, 100, 22))
            items_format = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower',
                            'veryslow',
                            'placebo']
            self.t_preset_format.addItems(items_format)
            self.t_preset_format.setCurrentText('medium')
            self.t_videoscale = QSpinBox(self.t_video)
            # self.t_videoscale.setMaximum(10)
            self.t_videoscale.setPrefix('视频宽度')
            self.t_videoscale.setStatusTip('设置可等比例缩放视频画面大小,0为原宽度')
            self.t_videoscale.setGeometry(160, 90, 110, 22)
            self.t_videoscale.setMaximum(9999)

            self.t_nondestructive = QCheckBox(self.t_video)
            self.t_nondestructive.setText('无损转换')
            self.t_nondestructive.setToolTip('仅用于将其他格式编码转为H.264编码，其他情况无效！')
            self.t_nondestructive.setStatusTip('强制保持无损转换，可能占用大量CPU资源和时间！可能导致体积变大！'
                                               '仅用于转为H.264编码的过程...')
            self.t_nondestructive.setGeometry(20, 160, 110, 22)

            self.t_videofps = QDoubleSpinBox(self.t_video)
            self.t_videofps.setPrefix('帧率')
            self.t_videofps.setStatusTip('设置视频输出帧率，不改变时长，可有效改变码率，0为原视频帧率')
            self.t_videofps.setGeometry(160, 180, 110, 22)

            self.t_form = QTimeEdit(self.t_video)
            self.t_form.setGeometry(160, 135, 110, 22)
            self.t_form.setDisplayFormat("从HH:mm:ss")
            self.t_to = QTimeEdit(self.t_video)
            self.t_to.setGeometry(330, 135, 110, 22)
            self.t_to.setDisplayFormat("到HH:mm:ss")
            self.t_to.setStatusTip('设置为00:00:00时取原长')
            self.t_vd_speed = QDoubleSpinBox(self.t_video)
            self.t_vd_speed.setGeometry(330, 180, 110, 22)
            self.t_vd_speed.setValue(1)
            self.t_vd_speed.setSingleStep(0.1)
            self.t_vd_speed.setMinimum(0.01)
            self.t_vd_speed.setPrefix('速度')
            self.t_vd_speed.setSuffix('倍')
            self.t_vd_speed.setStatusTip('设置输出视频的速度')
            self.t_vd_speed.setToolTip('设置输出视频的速度')

            self.t_audio_pushButton = QPushButton(self.t_audio)
            self.t_audio_pushButton.setGeometry(20, 20, 120, 120)
            self.t_audio_pushButton.setText("开始/选择音频")
            self.t_audio_pushButton.setToolTip('可以选择多个音频，请先调整好参数')
            self.t_audio_pushButton.setStatusTip('可以选择多个音频，请先调整好参数')
            self.t_audio_pushButton.clicked.connect(choice_t_ads)
            groupBox_2 = QGroupBox(self.t_audio)
            groupBox_2.setGeometry(QRect(320, 20, 120, 51))
            groupBox_2.setTitle("输出格式")
            groupBox_2.setStatusTip('设定输出文件格式')
            self.t_audiofile_format = QComboBox(groupBox_2)
            self.t_audiofile_format.setGeometry(QRect(10, 20, 100, 22))
            items_format = ['MP3', 'WAV', 'WMA', 'FLAC', 'AAC', 'OGG']
            self.t_audiofile_format.addItems(items_format)
            groupBox_3 = QGroupBox(self.t_audio)
            groupBox_3.setGeometry(QRect(150, 20, 120, 51))
            groupBox_3.setTitle("采样率/Hz")
            groupBox_3.setStatusTip('常用音频采样率切换，0为原采样率，注意与受支持的文件格式相对应')
            self.t_aar = QComboBox(groupBox_3)
            self.t_aar.setGeometry(QRect(10, 20, 100, 22))
            items_format = ['0', '8000', '11025', '22050', '16000', '32000', '44100', '47250', '48000', '50000',
                            '50400',
                            '96000', '192000']
            self.t_aar.addItems(items_format)
            self.t_aar.setCurrentText('0')
            self.t_ac = QSpinBox(self.t_audio)
            self.t_ac.setMaximum(10)
            self.t_ac.setPrefix('声道数')
            self.t_ac.setStatusTip('设置声道数，0为原文件声道数')
            self.t_ac.setGeometry(160, 90, 110, 22)

            self.t_aform = QTimeEdit(self.t_audio)
            self.t_aform.setGeometry(160, 140, 110, 22)
            self.t_aform.setDisplayFormat("从HH:mm:ss")
            self.t_ato = QTimeEdit(self.t_audio)
            self.t_ato.setGeometry(330, 140, 110, 22)
            self.t_ato.setDisplayFormat("到HH:mm:ss")
            self.t_ato.setStatusTip('设置为00:00:00时取原长')
            # self.t_ato.setMinimumTime(QTime(00, 00, 1))

            self.gifzip_pushButton = QPushButton(self.t_gif)
            self.gifzip_pushButton.setGeometry(20, 20, 120, 120)
            self.gifzip_pushButton.setText("开始/选择gif")
            self.gifzip_pushButton.setStatusTip('可以选择多个gif，请先调整好参数')
            self.gifzip_pushButton.clicked.connect(choice_t_gifs)
            self.gifscale = QDoubleSpinBox(self.t_gif)
            self.gifscale.setGeometry(210, 90, 110, 22)
            self.gifscale.setPrefix('比例')
            self.gifscale.setStatusTip('适当减少比例能有效减少文件大小')
            self.gifscale.setValue(0.7)
            self.gifscale.setSingleStep(0.1)

            groupBox_2 = QGroupBox(self.t_gif)
            groupBox_2.setGeometry(QRect(200, 20, 120, 51))
            groupBox_2.setTitle("颜色数")
            groupBox_2.setStatusTip('设定gif的颜色数，0为原图颜色数，可以减少体积')
            self.gifcolor = QComboBox(groupBox_2)
            self.gifcolor.setGeometry(QRect(10, 20, 100, 22))
            items_format = ['0', '2', '4', '8', '16', '32', '64', '128', '256']
            self.gifcolor.addItems(items_format)

            def choice_for_extract_ad_form_vd():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    vd, l = QFileDialog.getOpenFileName(self, "选择视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation), "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                        ";;all files(*.*)")
                    if len(vd) != 0:
                        self.transforma_thread = Commen_Thread(transformater.extract_ad_form_vd, vd)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_for_extract_vd_form_vd():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    vd, l = QFileDialog.getOpenFileName(self, "选择视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation), "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                        ";;all files(*.*)")
                    if len(vd) != 0:
                        self.transforma_thread = Commen_Thread(transformater.extract_vd_form_vd, vd)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_for_extract_pic_form_vd():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    vd, l = QFileDialog.getOpenFileNames(self, "选择视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation),
                                                         "video Files (*.mp4 *.mkv *.gif *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                         ";;all files(*.*)")
                    if len(vd) != 0:
                        self.transforma_thread = Commen_Thread(transformater.extract_pic_form_vd, vd)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_for_synthesis_ad_vd():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    mix = []
                    vd, l = QFileDialog.getOpenFileName(self, "选择视频", QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation), "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi)"
                                                        ";;all files(*.*)")
                    if len(vd) != 0:
                        mix.append(vd)
                    ad, l = QFileDialog.getOpenFileName(self, "选择音频", QStandardPaths.writableLocation(
                        QStandardPaths.MusicLocation),
                                                        "audio Files (*.MP3 *.WAV *.FLAC *.AAC *.Real Media *.MIDI *.OGG "
                                                        "*.amr) "
                                                        ";;all files(*.*)")

                    if len(ad) != 0:
                        mix.append(ad)
                    if len(mix) != 2:
                        self.showm_signal.emit('请分别选择一个视频文件和一个音频文件')
                    else:
                        self.transforma_thread = Commen_Thread(transformater.synthesis_ad_vd, mix)
                        self.transforma_thread.start()
                        QApplication.processEvents()
                        # transformater.synthesis_ad_vd(mix)

            def t_rename():
                files, l = QFileDialog.getOpenFileNames(self, "选择重命名文件", QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation), "all files(*.*);;"
                                                      "video Files (*.mp4 *.mkv *.flv *.wmv *.rmvb *.mov *.m4v *.avi);;"
                                                      "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP);;"
                                                      "audio Files (*.MP3 *.WAV *.FLAC *.AAC *.Real Media *.MIDI *.OGG *.amr)"
                                                        )
                if len(files) != 0:
                    self.transforma_thread = Commen_Thread(transformater.rename, files)
                    self.transforma_thread.start()
                    QApplication.processEvents()

            def t_rerename():
                file, l = QFileDialog.getOpenFileName(self, "选择恢复重命名文件", QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation),
                                                      "jambackup(*.jambak *.bak)"
                                                      )
                if len(file):
                    self.transforma_thread = Commen_Thread(transformater.rerename, file)
                    self.transforma_thread.start()
                    QApplication.processEvents()

            def choice_pics_for_vd():
                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    pics, l = QFileDialog.getOpenFileNames(self, "选择图片", QStandardPaths.writableLocation(
                        QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                                          ";;all files(*.*)")
                    if len(pics) != 0:
                        self.transforma_thread = Commen_Thread(transformater.pic_to_vd, pics)
                        self.transforma_thread.start()
                        QApplication.processEvents()

            def choice_ads_for_mix():  # 混音

                if transformater.ffmpeg_running and not self.mutil_transforma.isChecked():
                    self.showm_signal.emit('正在中止操作！')
                    transformater.stop_transform()
                else:
                    ads, l = QFileDialog.getOpenFileNames(self, "选择音频", QStandardPaths.writableLocation(
                        QStandardPaths.MusicLocation),
                                                          "audio Files (*.MP3 *.WAV *.FLAC *.AAC *.Real Media *.MIDI "
                                                          "*.OGG *.amr) "
                                                          ";;all files(*.*)")
                    if len(ads) > 1:
                        self.transforma_thread = Commen_Thread(transformater.mix_ads, ads)
                        self.transforma_thread.start()
                        QApplication.processEvents()
                    elif len(ads) == 1:
                        self.showm_signal.emit('请选择两个以上音频文件！')

            # toolbox = QWidget(self.tab3)
            # toolbox.setGeometry(20, 20, 540, 400)
            extractvd = QWidget(self.tab3)
            extractvd.setStyleSheet("background-color:rgb(240,240,240)")
            extractvd.setGeometry(20, 20, 540, 400)
            # toolbox.addItem(extractvd, "")
            ex_box = QGroupBox(extractvd)
            ex_box.setGeometry(15, 15, 300, 300)
            self.extract_ad_form_vd_pushButton = QPushButton(extractvd)
            self.extract_ad_form_vd_pushButton.setGeometry(20, 20, 120, 50)
            self.extract_ad_form_vd_pushButton.setText("提取音频")
            self.extract_ad_form_vd_pushButton.setStatusTip('从视频视频中提取音频')
            self.extract_ad_form_vd_pushButton.clicked.connect(choice_for_extract_ad_form_vd)
            self.extract_vd_form_vd_pushButton = QPushButton(extractvd)
            self.extract_vd_form_vd_pushButton.setGeometry(20, 80, 120, 50)
            self.extract_vd_form_vd_pushButton.setText("去除音频")
            self.extract_vd_form_vd_pushButton.setStatusTip('从视频中提取视频（去除声音）')
            self.extract_vd_form_vd_pushButton.clicked.connect(choice_for_extract_vd_form_vd)
            self.extract_pic_form_vd_pushButton = QPushButton(extractvd)
            self.extract_pic_form_vd_pushButton.setGeometry(20, 200, 120, 50)
            self.extract_pic_form_vd_pushButton.setText("提取帧")
            self.extract_pic_form_vd_pushButton.setStatusTip('从视频中提取帧')
            self.extract_pic_form_vd_pushButton.clicked.connect(choice_for_extract_pic_form_vd)
            self.synthesis_ad_vd_pushButton = QPushButton(extractvd)
            self.synthesis_ad_vd_pushButton.setGeometry(20, 140, 120, 50)
            self.synthesis_ad_vd_pushButton.setText("音视频混合")
            self.synthesis_ad_vd_pushButton.setStatusTip('混合你的视频和音乐')
            self.synthesis_ad_vd_pushButton.clicked.connect(choice_for_synthesis_ad_vd)
            self.extract_pic_fps = QDoubleSpinBox(extractvd)
            self.extract_pic_fps.setValue(5)
            self.extract_pic_fps.setPrefix('每秒取')
            self.extract_pic_fps.setSuffix('张')
            self.extract_pic_fps.setStatusTip('设置每秒钟抽取图片的数量')
            self.extract_pic_fps.setGeometry(160, 215, 140, 22)

            self.pic_to_vd_pushButton = QPushButton(extractvd)
            self.pic_to_vd_pushButton.setGeometry(20, 260, 120, 50)
            self.pic_to_vd_pushButton.setText("图片转视频")
            self.pic_to_vd_pushButton.setStatusTip('由图片文件生成视频文件,如需生成gif可在压缩转码中把生成的视频转为gif')
            self.pic_to_vd_pushButton.clicked.connect(choice_pics_for_vd)
            self.pic_to_vd_fps = QDoubleSpinBox(extractvd)
            self.pic_to_vd_fps.setGeometry(160, 275, 140, 25)
            self.pic_to_vd_fps.setValue(25)
            self.pic_to_vd_fps.setMinimum(0.01)
            self.pic_to_vd_fps.setPrefix('帧率')
            self.pic_to_vd_fps.setToolTip('设置视频帧率')
            self.pic_to_vd_fps.setStatusTip('设置视频帧率')

            self.mix_ads_pushButton = QPushButton(extractvd)
            self.mix_ads_pushButton.setGeometry(160, 20, 120, 50)
            self.mix_ads_pushButton.setText("混合音频")
            self.mix_ads_pushButton.setStatusTip('简单混合多个音频')
            self.mix_ads_pushButton.clicked.connect(choice_ads_for_mix)

            rename_groupbox = QGroupBox("重命名", extractvd)
            rename_groupbox.setGeometry(320, 10, 220, 300)
            self.rename_pushButton = QPushButton("开始/选择文件", rename_groupbox)
            self.rename_pushButton.setGeometry(15, 18, 110, 50)
            self.rename_pushButton.setStatusTip('选择多个文件')
            self.rename_pushButton.clicked.connect(t_rename)
            self.rename_backup_check_bot = QCheckBox("备份快照", rename_groupbox)
            self.rename_backup_check_bot.move(self.rename_pushButton.x() + self.rename_pushButton.width() + 10,
                                              self.rename_pushButton.y())
            self.rename_backup_check_bot.setToolTip("每次重命名文件都生成以jambak为后缀的文件名备份文件,当想恢复文件重命名时可以依次逆序选择该备份文件恢复")
            self.rename_backup_check_bot.setStatusTip("生成以jambak为后缀的文件名备份文件,当想恢复文件重命名时可以逆序恢复")
            self.rename_backup_check_bot.setChecked(True)
            self.rerename_btn = QPushButton("恢复", rename_groupbox)
            self.rerename_btn.setGeometry(self.rename_backup_check_bot.x(),
                                          self.rename_backup_check_bot.y() + self.rename_backup_check_bot.height(),
                                          50, 25)
            self.rerename_btn.setToolTip("根据备份文件恢复重命名,可能需要恢复多次才能恢复到原来的文件列表")
            self.rerename_btn.setStatusTip("根据备份文件恢复重命名")
            self.rerename_btn.clicked.connect(t_rerename)

            def change_rename_style():
                text = self.rename_style.currentText()
                self.renameform.clear()
                self.rename_randlen.hide()
                if text == "序列":
                    self.renameform.setEnabled(True)
                    self.renameform.setPlaceholderText('格式如:%04d、xx%04dxxx。。。')
                    self.renameform.setToolTip('设置命名格式，如:name%04dname则为name0000name.xxx，不设置则默认为0、1、2、3...')
                    self.renameform.setStatusTip('设置命名格式，不设置则默认追加为0000、0001、0002、0003...')
                elif text == "随机字符":
                    self.renameform.setEnabled(True)
                    self.renameform.setPlaceholderText("qwert61ybnm72uio45dfgpas89hjklzxcv3_")
                    self.renameform.setToolTip('随机字符，默认是所有字母+数字，可自行填写，若不够则自动扩充')
                    self.renameform.setStatusTip('随机字符，默认是所有字母+数字，可自行填写，若不够则自动扩充')
                    self.rename_randlen.show()
                elif text == "原名+S":
                    self.renameform.setEnabled(True)
                    self.renameform.setPlaceholderText("附加字符串S")
                    self.renameform.setToolTip('原名+字符串的形式,字符串的位置可以用{N}指定,如xxx{10}表示放在第十个字符后,不写则默认是最后')
                    self.renameform.setStatusTip("原名+字符串的形式,字符串的位置可以用{N}指定,如xxx{10}表示放在第十个字符后")
                else:
                    self.renameform.setPlaceholderText("文件的创建日期")
                    self.renameform.setEnabled(False)
                    self.renameform.setToolTip('以文件的创建日期命名文件')
                    self.renameform.setStatusTip('以文件的创建日期命名文件')

            rename_detailbox = QGroupBox("命名内容", rename_groupbox)
            rename_detailbox.setGeometry(self.rename_pushButton.x() - 10,
                                         self.rename_pushButton.y() + self.rename_pushButton.height() + 10, 180, 80)
            self.rename_style = QComboBox(rename_detailbox)
            self.rename_style.setGeometry(10, 20, 88, 25)
            self.rename_style.addItems(['序列', '随机字符', "修改时间", "原名+S"])
            self.rename_style.currentTextChanged.connect(change_rename_style)
            self.rename_randlen = QSpinBox(rename_detailbox)
            self.rename_randlen.setMinimum(1)
            self.rename_randlen.setValue(4)
            self.rename_randlen.setPrefix("长度")
            self.rename_randlen.setGeometry(self.rename_style.x() + self.rename_style.width() + 5,
                                            self.rename_style.y(), 75, 25)
            self.rename_randlen.hide()
            self.renameform = QLineEdit(rename_detailbox)
            self.renameform.setGeometry(self.rename_style.x(), self.rename_style.y() + self.rename_style.height() + 5,
                                        160, 25)
            change_rename_style()

            rename_sortbox = QGroupBox("命名顺序", rename_groupbox)
            rename_sortbox.setGeometry(rename_detailbox.x(), rename_detailbox.y() + rename_detailbox.height() + 10, 180,
                                       80)
            self.rename_sort = QComboBox(rename_sortbox)
            self.rename_sort.setGeometry(10, 18, 120, 25)
            self.rename_sort.addItems(["文件名称", "文件大小", "修改时间"])
            self.rename_sort.setToolTip("文件的命名顺序,在根据序列命名中有效")
            self.rename_sort.setStatusTip("文件的命名顺序,在根据序列命名中有效")
            self.rename_sort_reverse = QCheckBox("倒序", rename_sortbox)
            self.rename_sort_reverse.setToolTip("命名倒序")
            self.rename_sort_reverse.setStatusTip("命名倒序")
            self.rename_sort_reverse.setGeometry(self.rename_sort.x(),
                                                 self.rename_sort.y() + self.rename_sort.height() + 2, 80, 25)

            self.mutil_transforma = QCheckBox(self.Transforma_groupBox)
            self.mutil_transforma.move(465, 30)
            self.mutil_transforma.setText('多任务处理')
            self.mutil_transforma.setToolTip('勾选后将允许多个转换任务同时处理，可能占用巨量系统资源！且原按键将不可中止！')
            self.mutil_transforma.setStatusTip('勾选后将允许多个转换任务同时处理，可能占用巨量系统资源！且原按键将不可中止！')

            def change_hardware_transforma():
                if self.hardware_transforma.isChecked():
                    items_format = ['default', 'fast', 'medium', 'slow', 'hp', 'hq', 'lossless', 'losslesshp']
                    self.t_preset_format.clear()
                    self.t_preset_format.addItems(items_format)
                else:
                    items_format = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower',
                                    'veryslow',
                                    'placebo']
                    self.t_preset_format.clear()
                    self.t_preset_format.addItems(items_format)
                    self.t_preset_format.setCurrentText('medium')

            #     self.hardware_rec.setChecked(not self.hardware_rec.isChecked())
            #     self.setting_save()

            self.hardware_transforma = QCheckBox(self.Transforma_groupBox)
            self.hardware_transforma.move(365, 30)
            if PLATFORM_SYS == "win32":
                self.hardware_transforma.setText('硬件加速')
                self.hardware_transforma.setChecked(self.settings.value('rec_settings/hardware_rec', False, type=bool))
                self.hardware_transforma.stateChanged.connect(
                    lambda: self.settings.setValue('rec_settings/hardware_rec', self.hardware_transforma.isChecked()))
                self.hardware_transforma.setToolTip(
                    '启用独立显卡的为视频处理加速,可极大提高处理速度,仅适配H.264编码和NVIDIA显卡\n需要把显卡驱动更新到最新版!进入设备管理器-显示适配器-NVIDIA XXX-更新驱动程序')
                self.hardware_transforma.setStatusTip('启用独立显卡的为视频处理加速,可极大提高处理速度,仅适配H.264编码和NVIDIA显卡,请把显卡驱动更新到最新版!')
                self.hardware_transforma.stateChanged.connect(change_hardware_transforma)
                if self.hardware_transforma.isChecked():
                    items_format = ['default', 'fast', 'medium', 'slow', 'hp', 'hq', 'lossless', 'losslesshp']
                    self.t_preset_format.clear()
                    self.t_preset_format.addItems(items_format)
            else:
                self.hardware_transforma.hide()

            self.transforma_stop = QPushButton(self.Transforma_groupBox)
            self.transforma_stop.setGeometry(420 if PLATFORM_SYS == "darwin" else 330, 30, 18, 18)
            self.transforma_stop.setText('X')
            self.transforma_stop.setToolTip('停止所有处理！')
            self.transforma_stop.setStatusTip('停止所有处理！')
            self.transforma_stop.setStyleSheet('QPushButton{background-color:rgb(239,10,10)}')
            self.transforma_stop.clicked.connect(transformater.stop_transform)

            self.transfor_view = True

        self.change_show_item([self.Transforma_groupBox])

    def record_screen_deviceinit(self):
        if PLATFORM_SYS == "win32":
            f = "-list_devices true -f dshow -i dummy "
        elif PLATFORM_SYS == "darwin":
            f = '-f avfoundation -list_devices true -i ""'
        else:
            f = ' -hide_banner -devices '
        if not (os.path.exists(ffmpeg_path+"/ffmpeg")or os.path.exists(ffmpeg_path+"/ffmpeg.exe")):
            print("找不到ffmpeg,请自行到ffmpeg官网下载可执行文件或源码,编译后将ffmpeg可执行文件放于{}下".format(ffmpeg_path))
            self.showm_signal.emit("找不到ffmpeg,请自行到ffmpeg官网下载可执行文件或源码,编译后将ffmpeg可执行文件放于{}下".format(ffmpeg_path))
            relog=" "
        else:
            record = subprocess.Popen('"' + ffmpeg_path + '/ffmpeg" {}'.format(f), shell=True,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            relog = record.stderr.read()
            # print(relog)
            record.terminate()
        audio_divice = []
        video_divice = []
        if PLATFORM_SYS == "win32":
            reloglist = relog.split('"')[1:]
            # print(reloglist)
            for i in range(len(reloglist)):
                stri = reloglist[i].lower()
                if 'directshow' not in stri:
                    if 'audio' in stri:
                        audio_divice.append(reloglist[i])
                    elif 'camera' in stri or 'video' in stri or 'recorder' in stri:
                        video_divice.append(reloglist[i])

            if 'virtual-audio-capturer' in audio_divice:
                audio_divice.insert(0, audio_divice.pop(audio_divice.index('virtual-audio-capturer')))
        elif PLATFORM_SYS == "darwin":
            relog = relog.split("AVFoundation video devices:")[1]
            linelist = [i.split("] [")[1] for i in relog.split("\n") if
                        "@" in i and "avfoundation audio devices" not in i.lower()]
            print(linelist)
            v = -1
            for line in linelist:
                n = line[0]
                if n.isdigit():
                    if int(n) == 0: v += 1
                    if v == 0:
                        if "screen" in line.lower():
                            video_divice.insert(0, line[3:])
                        else:
                            video_divice.append(line[3:])
                    else:
                        audio_divice.append(line[3:])
            print(video_divice, audio_divice)
        else:
            video_divice = ["尚未支持"]

        self.audio_divice = audio_divice
        self.video_divice = video_divice
        print('audiolist', audio_divice, '\nvideolist', video_divice)

    def record_screen(self):
        self.record_screen_deviceinit()
        if not self.recview:
            self.pushButton = QPushButton(self.rec_groupBox)
            self.pushButton.setGeometry(QRect(30, 290, 120, 120))
            self.pushButton.setText("开始/结束\n(Alt+c)")
            self.pushButton.setToolTip('开始/结束,也可以用快捷键Alt+c')
            self.pushButton.setStatusTip('开始/结束,也可以用快捷键Alt+c')
            self.pushButton.clicked.connect(self.recorder.recordchange)
            self.pushButton.setStyleSheet("QPushButton{color:rgb(200,100,100)}"
                                          # "QPushButton:hover{color:green}"
                                          "QPushButton:hover{background-color:rgb(200,10,10)}"
                                          "QPushButton:!hover{background-color:rgb(200,200,200)}"
                                          "QPushButton{background-color:rgb(239,239,239)}"
                                          "QPushButton{border:6px solid rgb(50, 50, 50)}"
                                          "QPushButton{border-radius:60px}"
                                          )
            self.mouse_rec = QCheckBox(self.rec_groupBox)
            self.mouse_rec.setGeometry(QRect(390, 320, 91, 19))
            if PLATFORM_SYS == "darwin":
                self.mouse_rec.hide()
            else:
                self.mouse_rec.setText("录制鼠标")
                self.mouse_rec.setToolTip('是否录制鼠标')
                self.mouse_rec.setStatusTip('是否录制鼠标,仅在抓屏下可以使用')
                self.mouse_rec.setChecked(self.settings.value('rec_settings/mouse_rec', True, type=bool))
                self.mouse_rec.stateChanged.connect(self.setting_save)

            self.sp_rec = QCheckBox(self.rec_groupBox)
            self.sp_rec.setGeometry(QRect(390, 260, 91, 19))
            self.sp_rec.setText("画质适配")
            self.sp_rec.setToolTip('由于默认采用的是H.264的high级别画质以增加压缩比，某些设备可能无法播放，勾选以使用Baseline画质以适配所有设备！')
            self.sp_rec.setStatusTip('由于默认采用的是H.264的high级别画质以增加压缩比，勾选以使用Baseline画质以适配所有设备！')

            self.hide_rec = QCheckBox(self.rec_groupBox)
            self.hide_rec.setGeometry(QRect(390, 290, 91, 19))
            self.hide_rec.setText("隐藏窗口")
            self.hide_rec.setToolTip('开始录屏后隐藏本窗口,可用快捷键或系统托盘结束')
            self.hide_rec.setStatusTip('开始录屏后隐藏本窗口,可用快捷键或系统托盘结束')
            self.hide_rec.setChecked(self.settings.value('rec_settings/hide_rec', False, type=bool))
            self.hide_rec.stateChanged.connect(self.setting_save)

            def change_hardware_rec():
                if self.hardware_rec.isChecked():
                    items_rate = ['default', 'fast', 'medium', 'slow', 'hp', 'hq', 'lossless', 'losslesshp']
                    self.preset.clear()
                    self.preset.addItems(items_rate)
                else:
                    items_rate = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower',
                                  'veryslow',
                                  'placebo']
                    self.preset.clear()
                    self.preset.addItems(items_rate)
                self.setting_save()

            self.hardware_rec = QCheckBox(self.rec_groupBox)
            self.hardware_rec.setGeometry(QRect(390, 350, 91, 19))
            if PLATFORM_SYS == "win32":
                self.hardware_rec.setText("硬件编码")
                self.hardware_rec.setToolTip(
                    '可使用独立显卡进行编码,能有效降低CPU占用,目前仅适配了NVIDIA的显卡;\n需要把显卡驱动更新到最新版!进入设备管理器-显示适配器-NVIDIA XXX-更新驱动程序')
                self.hardware_rec.setStatusTip('可使用独立显卡进行编码,能有效降低CPU占用,目前仅适配了NVIDIA的显卡,请把显卡驱动更新到最新版!')
                self.hardware_rec.setChecked(self.settings.value('rec_settings/hardware_rec', False, type=bool))
                self.hardware_rec.stateChanged.connect(change_hardware_rec)
            else:
                self.hardware_rec.hide()

            self.pushButton_2 = QPushButton(self.rec_groupBox)
            self.pushButton_2.setStyleSheet(
                "QPushButton:hover{background-color:rgb(120,50,10)}"
                "QPushButton:!hover{background-color:rgb(200,200,200)}"
                "QPushButton{background-color:rgb(239,239,239)}"
                "QPushButton{border:1px solid rgb(100, 100, 100)}"
                "QPushButton{border-radius:6px}")
            self.pushButton_2.setGeometry(QRect(30, 240, 120, 30))
            self.pushButton_2.setText("选区")
            self.pushButton_2.setToolTip('选定视频/gif录制区域')
            self.pushButton_2.setStatusTip('选定视频/gif录制区域')
            self.pushButton_2.clicked.connect(self.set_area)

            def open_record_path():
                p = QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + "/Jam_screenrecord/"
                QDesktopServices.openUrl(QUrl.fromLocalFile(p))

            open_pathbtn = QPushButton('', self.rec_groupBox)
            open_pathbtn.setGeometry(self.rec_groupBox.width() - 35, 10, 35, 35)
            open_pathbtn.setIcon(QIcon(":/videowjj.png"))
            open_pathbtn.setStyleSheet("border:none;border-radius:6px;")
            open_pathbtn.clicked.connect(open_record_path)
            open_pathbtn.setToolTip('打开存放录屏文件的文件夹')
            open_pathbtn.setStatusTip('打开存放录屏文件的文件夹')

            self.groupBox_2 = QGroupBox(self.rec_groupBox)
            self.groupBox_2.setGeometry(QRect(200, 150, 120, 51))
            self.groupBox_2.setTitle("文件格式")
            self.groupBox_2.setToolTip('设定输出文件格式(视频/gif等),选择mp3格式则只录音频')
            self.groupBox_2.setStatusTip('设定输出文件格式(视频/gif等),选择mp3格式则只录音频')
            self.file_format = QComboBox(self.groupBox_2)
            self.file_format.setGeometry(QRect(10, 20, 100, 22))
            items_format = ['mp4', 'gif', 'flv', 'mkv', 'TS']
            if PLATFORM_SYS != "linux":
                items_format.append('mp3')
            self.file_format.addItems(items_format)
            self.file_format.setToolTip('选择gif格式则只录视频;选择mp3格式则只录音频')
            self.file_format.setStatusTip('选择gif格式则只录视频;选择mp3格式则只录音频')
            # self.comboBox.setObjectName("comboBox")
            self.groupBox_3 = QGroupBox(self.rec_groupBox)
            self.groupBox_3.setGeometry(QRect(200, 290, 120, 51))
            self.groupBox_3.setTitle("帧率")
            self.comboBox_2 = QDoubleSpinBox(self.groupBox_3)
            self.comboBox_2.setGeometry(QRect(10, 20, 100, 22))
            self.comboBox_2.setValue(30)

            self.delay_time = QGroupBox(self.rec_groupBox)
            self.delay_time.setGeometry(QRect(30, 150, 120, 51))
            self.delay_time.setTitle("延时/s")
            self.delay_t = QDoubleSpinBox(self.delay_time)
            self.delay_t.setGeometry(QRect(10, 20, 100, 22))
            self.delay_t.setValue(0)
            self.delay_t.setMaximum(99999)
            self.groupBox_4 = QGroupBox(self.rec_groupBox)
            self.groupBox_4.setGeometry(QRect(200, 360, 120, 51))
            self.groupBox_4.setTitle("视频质量")
            self.groupBox_4.setToolTip('强制控制视频帧质量,-1为自动,0为近无损,99为全损...')
            self.groupBox_4.setStatusTip('强制控制视频帧质量,-1为自动,0为无损,99为全损...设置该值会导致编码速率等不可用!')
            self.qp_rec = QSpinBox(self.groupBox_4)
            self.qp_rec.setGeometry(QRect(10, 20, 100, 22))
            self.qp_rec.setValue(5)
            self.qp_rec.setMinimum(-1)
            # self.comboBox_3.setObjectName("comboBox_3")
            self.groupBox_6 = QGroupBox(self.rec_groupBox)
            self.groupBox_6.setGeometry(QRect(200, 220, 120, 51))
            self.groupBox_6.setTitle("编码速率")
            self.groupBox_6.setToolTip('设置码率,编码速率越快占用越小,文件体积越大')
            self.groupBox_6.setStatusTip('设置码率,编码速率越快占用越小,文件体积越大')
            self.preset = QComboBox(self.groupBox_6)
            self.preset.setGeometry(QRect(10, 20, 100, 22))
            if self.hardware_rec.isChecked():
                items_rate = ['default', 'fast', 'medium', 'slow', 'hp', 'hq', 'lossless', 'losslesshp']
                # self.preset.clear()
                self.preset.addItems(items_rate)
            else:
                items_rate = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower',
                              'veryslow',
                              'placebo']
                # self.preset.clear()
                self.preset.addItems(items_rate)
            self.groupBox_5 = QGroupBox("声音来源", self.rec_groupBox)
            self.groupBox_5.setGeometry(QRect(350, 150, 220, 50))
            self.groupBox_5.setToolTip('设置录制的声音来源')
            self.groupBox_5.setStatusTip('设置录制的声音来源')
            self.soundsourse = QComboBox(self.groupBox_5)
            self.soundsourse.setGeometry(10, 20, 200, 25)
            videosoursegroub = QGroupBox('图像来源', self.rec_groupBox)
            videosoursegroub.setGeometry(350, 90, 220, 50)
            videosoursegroub.setToolTip('设置图像来源,可以为屏幕(抓屏或者串流方式),也可以是相机!')
            videosoursegroub.setStatusTip('设置图像来源,可以为屏幕(抓屏或者串流方式),也可以是相机!')
            self.videosourse = QComboBox(videosoursegroub)
            self.videosourse.setGeometry(10, 20, 200, 25)

            def change_videosourse(video):
                print(video)
                if video == '抓屏':

                    self.mouse_rec.setEnabled(True)
                else:
                    self.mouse_rec.setChecked(True)
                    self.mouse_rec.setEnabled(False)

            self.videosourse.currentTextChanged.connect(change_videosourse)

            self.scale_box = QGroupBox(self.rec_groupBox)
            self.scale_box.setGeometry(QRect(200, 80, 120, 51))
            self.scale_box.setTitle("缩放比例")
            self.scale_box.setToolTip('设置分辨率的缩放比例(多用于gif录制)')
            self.scale_box.setStatusTip('设置分辨率的缩放比例(多用于gif录制)')
            self.scale = QDoubleSpinBox(self.scale_box)
            self.scale.setGeometry(QRect(10, 20, 100, 22))
            self.scale.setValue(1)
            self.scale.setSingleStep(0.1)
            self.scale.setMaximum(2)
            self.scale.setMinimum(0.10)

            # time.sleep(2)
            print('rec_init')

        self.recview = True
        self.soundsourse.clear()
        self.soundsourse.addItems(self.audio_divice)
        self.soundsourse.addItem('无')
        self.videosourse.clear()
        if PLATFORM_SYS != "darwin":
            self.videosourse.addItem('抓屏')
        self.videosourse.addItems(self.video_divice)
        if len(self.audio_divice) == 0 and PLATFORM_SYS != "linux":
            self.showm_signal.emit('找不到你的音频设备,请尝试重装本软件!')
        self.change_show_item([self.rec_groupBox])

    def openlistenmouse(self):  # 监听鼠标右键划屏提字
        print("mouse listen start")
        self.simg = Small_Ocr()  # 划屏提字

        def on_click(x, y, button, pressed):
            if button == mouse.Button.left:
                if not pressed:
                    try:
                        if self.simg.isVisible():
                            le = self.simg.h
                            if x < self.simg.sx - le or x > self.simg.ex + le * 3 or y > self.simg.sy + le * 3 or y < self.simg.sy - le * 2:
                                self.simg.clear()
                                self.simg.hide()
                    except:
                        print(sys.exc_info())
                        pass
            elif button == mouse.Button.right:
                if jamtools.settings.value('right_ocr', False, bool):
                    if pressed:
                        self.simg.sx = x
                        self.simg.sy = y
                    else:
                        self.simg.ex = x
                        self.simg.ey = y
                        dx = self.simg.ex - self.simg.sx
                        dy = self.simg.ey - self.simg.sy
                        lef = self.simg.h / 2
                        if dx > 20 and abs(dy) <= lef:
                            print(self.simg.h / 2)
                            screen = QApplication.primaryScreen()

                            pix = screen.grabWindow(QApplication.desktop().winId(), self.simg.sx, self.simg.sy - lef,
                                                    dx, self.simg.h)
                            pix.save("j_temp/sdf.png")
                            self.simg.pix=pix
                            jamtools.start_thread = StraThread(dx)
                            jamtools.start_thread.start()
                            QApplication.processEvents()

        self.jam_mouselisten = mouse.Listener(on_click=on_click)
        self.jam_mouselisten.start()

    def closelistenmouse(self):
        self.jam_mouselisten.stop()

    def multiocr(self):  # 批量识别
        files, types = QFileDialog.getOpenFileNames(self,
                                                    "批量识别",
                                                    QStandardPaths.writableLocation(QStandardPaths.PicturesLocation),
                                                    "img Files (*.jpg *.PNG *.JPG *.JPEG *.BMP)")
        if files != []:
            print(files)
            self.ocr_textEdit.clear()
            if not self.OCR:
                self.ocr()
            if QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                #     S_SIMPLE_MODE=False
                self.show()
                self.hide()  # 删除闪退
            QApplication.processEvents()

            def mutil_cla_signalhandle(filename, text):
                print("mutil_cla_signalhandle active")
                if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                    self.ocr_textEdit.insertPlainText("\n>>>>识别图片:{}<<<<\n".format(filename))
                    self.ocr_textEdit.insertPlainText(text + '\n' * 2)
                    self.statusBar().showMessage('识别{}完成！'.format(filename))

            self.mutiocrthread = mutilocr(files)
            self.mutiocrthread.ocr_signal.connect(mutil_cla_signalhandle)
            self.mutiocrthread.statusbarsignal.connect(self.statusBar().showMessage)
            self.mutiocrthread.start()

            self.change_show_item([self.ocr_groupBox])
        else:
            if QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                self.show()
                self.hide()
            # self.ocr_textEdit.show()

    def word_extraction(self,w,text=None, text1=None):  # 画词提取接收信号函数
        self.simg.show_extrat_res(w, text, text1)

    def help(self):
        # self.help_text.setReadOnly(True)
        self.help_text.clear()

        # def init_help():
        self.payimg.hide()
        self.change_show_item([self.about_groupBox])
        text = """>>>功能简介:
1.酱截屏：截图功能.快捷键Alt+z；支持选区截图、多边形截图、滚动截屏等、支持复制截屏文件或图像数据到剪切板、支持截图中文字识别(翻译)、图像识别等，左侧工具栏提供画笔橡皮擦等；支持滚动截屏，滚动过程中支持自动和手动滚动。

2.酱识字：文字识别功能；截屏提取.快捷键Alt+x：截屏并提取文字；批量识别：可上传一张或多张图片进行文字提取

3.酱翻译：多语言翻译功能.无快捷键(极简模式下可通过浮窗使用)；输入文字翻译，支持多种语言互译！已集成到截屏等界面下。

4.酱录屏：录屏功能.快捷键Alt+c;屏幕录制功能，支持gif等多种格式录制；可以选定录制区，不选则为全屏录制；支持自定义编码速率、帧率、视频质量、声音源鼠标等；录屏结束后点击通知将直接播放！

5.酱转换：各种多媒体文件的裁剪拼接、压缩转码、提取混合功能...这个的功能太多自行探索...

6.酱控制：鼠标键盘所有动作的录制和重放，支持将录制的动作作为教程发送给你的小伙伴萌，支持快捷键启动Alt+1录制，Alt+2播放,F4强制中断播放。注意是不是九宫格的数字1！是字母区上面的数字！动作文件(.jam)可以直接双击打开或拖入打开！

7.酱传输：提供快速的局域网传输功能,有客户端点对点连接传输和网页端共享两种方式。均支持数据双向传输。客户端连接需要通过连接码自动搜索并连接主机，建立连接之后即可互相发送文件或文件夹。网页端传输相当于共享文件夹，支持共享一个文件夹或文件夹下的某几个文件，通过选择对应网络适配器即可生成共享链接，连入该与适配器同一网络的其他设备即可通过链接或扫码访问共享文件，网页端勾选允许上传后支持文件上传。

8.酱聊天：。。。。彩蛋功能。。傻d机器人在线陪聊！！来自思知人工智能平台的机器人（别问为什么不用图灵机器人，因为没q啊！），填写用户ID后支持多轮对话，服务器有点慢。。。。毕竟思知也是免费提供的，还提供支持知识库训练，不能过多要求哈；默认保留50000字节的聊天记录。。

$其他功能：划屏提字：打开软件后可以在任何界面(图片也可)，用鼠标右键水平右划，即可提取出鼠标滑过的文字上下设定像素内的文字(并翻译)，可以在设置中心设置详细内容！
剪贴板翻译：监控剪贴板内容，剪切板内容变化7s内按下shift触发,支持英语自动翻译,网页自动打开,百度云链接提取码自动复制等！可在设置中心设置详细内容！
极简模式：极简模式下不会显示主界面，截屏(Alt+z)、文字识别(Alt+x)、录屏(Alt+c)、键鼠动作录制(Alt+1)播放(Alt+2)均可以用(用快捷键/系统托盘)调用，所有功能显示均在小窗显示，小窗可以(回车)翻译(英-中),双击系统托盘可以进入/退出极简模式
##大部分功能可以在系统托盘调用！

留意软件内状态栏和悬浮提示。。。enjoy it！
hhh(o゜▽゜)o☆）
"""
        self.help_text.insertPlainText(text)

        # self.inin_help = Commen_Thread(init_help)
        # self.inin_help.start()
        self.help_text.moveCursor(QTextCursor.Start)

    def checkforupdate(self):
        try:
            if self.updatedialog.active:
                self.updatedialog.show()
                return
        except:
            print(sys.exc_info())
        self.updatedialog = ChildUpdateWindow(self)
        self.updatedialog.raise_()

    def logeshow(self):
        self.help_text.clear()
        self.payimg.hide()
        self.change_show_item([self.about_groupBox])
        text = ""
        with open(os.path.join(apppath, "log.log"), "r", encoding="utf-8")as f:
            text = f.read()
        self.help_text.insertPlainText(text)
        self.help_text.moveCursor(QTextCursor.Start)

    def about(self):
        icon = QPixmap(":/p.png")
        self.payimg.setPixmap(icon)
        self.payimg.setScaledContents(True)
        self.payimg.resize(150, 150)
        self.payimg.move(20, 270)
        self.payimg.show()
        self.help_text.clear()
        self.change_show_item([self.about_groupBox])

        text = 'Edit by Fandes&机械酱 build for 深圳大学帮帮酱\n\n' \
               '感谢以下个人/团队提供接口支持：\n' \
               '   百度AI开放平台http:/ai.baidu.com\n' \
               '   百度翻译开放平台https:/api.fanyi.baidu.com\n' \
               '   思知人工智能AI开放平台https:/console.ownthink.com\n' \
               '   本软件完全免费、开源，拒绝商业用途！严禁贩卖！如有疑问，请联系作者 2861114322@qq.com\n\n' \
               '本软件安装文件的唯一正常来源为Github项目地址:https://github.com/fandesfyf/JamTools和个人CSDN博客\n'\
               '建议从Github的release中下载最新版本，从其他地址下载的安装文件有可能已被更改，本作者不负任何责任！！'\
               '欢迎给该软件提出任何宝贵意见/建议(说不定下一个版本就出现了呢)\n' \
               '欢迎关注,<<机械酱的小黑屋>>(ˇ∀ˇ),虽然什么都没有...(真的)'
        self.help_text.insertPlainText(text)

    def others(self):
        self.payimg.hide()
        self.help_text.clear()

        text = """1.右键划屏识字(翻译)\n    用法:任意界面按住右键水平右划过屏幕上文字的中间即可提取出文字并翻译,支持一键跳转百度搜索;如不需要,可以在设置中心关闭这个功能...\n   
2.剪切板监听:\n    用法:复制文字后n秒(默认为7s)内按下shift键触发，检测到复制的内容为英文时直接弹窗并翻译;检测到网址时直接在浏览器打开;可在设置中心设置更加详细的内容...(由于权限原因,macos用户需要复制内容后点击程序后按下shift才可触发弹窗..)
               """

        self.help_text.insertPlainText(text)

        self.change_show_item([self.about_groupBox])

    def dragEnterEvent(self, e):
        print(e.mimeData().urls())
        if len(e.mimeData().urls()) != 0:
            file0 = e.mimeData().urls()[0].toLocalFile()
            print(os.path.splitext(file0)[-1])
            if os.path.splitext(file0.lower())[-1] in ['.jam']:
                e.acceptProposedAction()

    def dropEvent(self, e):
        print("drop", e.mimeData().urls())
        data = []
        for i in range(len(e.mimeData().urls())):
            data.append(e.mimeData().urls()[i].toLocalFile())

        if os.path.splitext(data[0].lower())[-1] == '.jam':
            jamtools.start_action_run(data[0])
            print('start')
            jamtools.hide()
        # else:
        #     for path in data:
        #         if os.path.isdir(path):
        #             pass

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        # if e.key() == Qt.Key_Alt + Qt.Key_Z:
        #     self.getandshow()
        # if e.key() == Qt.Key_Alt + Qt.Key_X:
        #     self.BaiduOCR()
        # if e.key() == Qt.Key_Alt + Qt.Key_C:
        #     self.BDimgcla()

        # if e.key()==Qt.K

    def chat(self):
        sendtime = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        text = self.chat_send_textEdit.toPlainText()
        self.chat_send_textEdit.clear()
        self.statusBar().showMessage("小酱酱正在输入...")
        self.chat_view_textEdit.moveCursor(QTextCursor.End)
        self.chat_view_textEdit.setTextColor(QColor(10, 100, 222))
        me = self.userid + ' ' + sendtime + ':\n'
        self.chat_view_textEdit.insertPlainText(me)
        self.chat_view_textEdit.setTextColor(QColor(0, 0, 0))
        self.chat_view_textEdit.insertPlainText(text + '\n')
        # bot=QPushButton("测试",self.chat_view_textEdit)
        # bot.move(50,self.chat_view_textEdit.document().size().height())
        # bot.show()
        # print(self.chat_view_textEdit.document().size(),bot.isVisible(),50,self.chat_view_textEdit.document().size().height()-50)
        with open(documents_path + '/chat_record.txt', 'a')as file:
            file.write(me + text + '\n')
            file.flush()
        self.chatthread = Chat_Thread(Tulin, text)
        self.chatthread.start()

        QApplication.processEvents()

    def recieve_chat(self, mess):
        sendtime = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        jj = '小酱酱 ' + sendtime + ':\n'
        self.chat_view_textEdit.moveCursor(QTextCursor.End)
        self.chat_view_textEdit.setTextColor(QColor(10, 100, 222))
        self.chat_view_textEdit.insertPlainText(jj)
        self.chat_view_textEdit.setTextColor(QColor(0, 0, 0))
        self.chat_view_textEdit.insertPlainText(mess + '\n')
        self.statusBar().showMessage("小酱酱回复完成！")
        QApplication.processEvents()
        with open(documents_path + '/chat_record.txt', 'a')as file:
            file.write(jj + mess + '\n')
            file.flush()

    def Filestransmitter(self, a=0):
        if not self.init_transmitter:
            self.apptransmitterbox = ClientFilesTransmitterGroupbox("通过客户端传输", self.transmitter_groupBox)
            self.apptransmitterbox.showm_signal.connect(self.trayicon.showM)
            self.apptransmitterbox.setGeometry(10, 25, self.transmitter_groupBox.width() - 20, 222)
            self.webtransmitterbox = WebFilesTransmitterBox(self.WebFilesTransmitter, "通过网页传输",
                                                            self.transmitter_groupBox)
            self.webtransmitterbox.showm_signal.connect(self.trayicon.showM)
            self.webtransmitterbox.move(self.apptransmitterbox.x(),
                                        self.apptransmitterbox.y() + self.apptransmitterbox.height() + 10)
            self.webtransmitterbox.resize(self.apptransmitterbox.width(),
                                          self.transmitter_groupBox.height() - self.webtransmitterbox.y() - 8)

        self.webtransmitterbox.updatedevice()
        self.init_transmitter = True

        self.change_show_item([self.transmitter_groupBox])

    def Tulinchat(self):
        # self.charing = True
        self.botappid = "d1139cde1c88a8ecf5af1337fbebace8"
        self.userid = self.settings.value('chat_userid', 'USER', type=str)
        self.chat_userid_edit = QTextEdit(self.chat_groupBox)
        self.chat_userid_edit.setGeometry(460, 30, 100, 32)
        self.chat_userid_edit.setText(self.userid)
        self.chat_userid_edit.setStatusTip('设置你的昵称')
        clearchatrecordbtn = QPushButton("清除聊天记录", self.chat_groupBox)
        clearchatrecordbtn.setGeometry(460, 70, 100, 30)

        def clearchat():
            if os.path.exists(documents_path + '/chat_record.txt'):
                os.remove(documents_path + '/chat_record.txt')
                self.chat_view_textEdit.clear()
                self.chat_view_textEdit.insertPlainText("-----已清除聊天记录-----")
                self.showm_signal.emit("已清除聊天记录")

        clearchatrecordbtn.clicked.connect(clearchat)

        def save_setting():
            self.userid = self.chat_userid_edit.toPlainText()
            self.settings.setValue('chat_userid', self.userid)

        self.chat_userid_edit.textChanged.connect(save_setting)
        self.chat_view_textEdit = QTextEdit(self.chat_groupBox)

        def move_to_end():
            self.chat_view_textEdit.moveCursor(QTextCursor.End)

        self.chat_view_textEdit.textChanged.connect(move_to_end)
        self.chat_view_textEdit.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.chat_view_textEdit.setReadOnly(True)
        if os.path.exists(documents_path + '/chat_record.txt'):
            with open(documents_path + '/chat_record.txt', 'r+')as file:
                text = file.read()
                if len(text) > 100000:
                    text = text[50000:]
                    file.seek(0)
                    file.truncate()
                    file.write('-----前面的聊天记录已清空!-----\n' + text)
                self.chat_view_textEdit.insertPlainText(text + '\n-----------以上为历史消息-----------\n')

        self.chat_view_textEdit.setGeometry(100, 30, 350, 350)
        self.chat_send_textEdit = EnterSendQTextEdit(self.chat_groupBox)
        self.chat_send_textEdit.keyenter_connect(self.chat)
        self.chat_send_textEdit.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.chat_send_textEdit.clear()
        self.chat_send_textEdit.setGeometry(100, 390, 350, 90)
        self.chatbt = QPushButton("发送>>", self.chat_groupBox)
        self.chatbt.setToolTip('发送消息(回车Enter)')
        self.chatbt.setStyleSheet('background-color:rgb(50,150,200)')
        self.chatbt.setGeometry(393, 452, 55, 26)
        self.chatbt.clicked.connect(self.chat)
        """由于腾讯的api改为付费了,所以不显示播放声音(作者没钱啊qaq),如需使用可以打开注释然后在txpythonsdk中修改api即可"""
        # voicebtn = QPushButton("", self.chat_groupBox)
        # if self.settings.value("chater/playvoice", False, type=bool):
        #     voicebtn.setStyleSheet('border-image: url(:/sound3.png);')
        # else:
        #     voicebtn.setStyleSheet('border-image: url(:/sound0.png);')
        # voicebtn.setGeometry(self.chat_send_textEdit.x() + self.chat_send_textEdit.width() + 5,
        #                      self.chat_send_textEdit.y() - 65,
        #                      25, 25)
        #
        # def viocebtnclick():
        #     if self.settings.value("chater/playvoice", False, type=bool):
        #         voicebtn.setStyleSheet('border-image: url(:/sound0.png);')
        #     else:
        #         voicebtn.setStyleSheet('border-image: url(:/sound3.png);')
        #     self.settings.setValue("chater/playvoice", not self.settings.value("chater/playvoice", False, type=bool))
        #
        # voicebtn.clicked.connect(viocebtnclick)
        # # voicebtn.setToolTip("是否播放声音")
        # voicebtn.setStatusTip("是否播放声音")
        # voicetypedict = {"默认": 7, "智侠|情感": 101000, "智瑜|情感": 101001, "智聆|通用": 101002, "智美|客服": 101003,
        #                  "智云|通用": 101004, "智莉|通用": 101005, "智言|助手": 101006, "智娜|客服": 101007, "智琪|客服": 101008,
        #                  "智芸|知性": 101009, "智华|通用": 101010, "WeJack|英文": 101050, "WeRose|英文": 101051,
        #                  "贝蕾|客服": 102000, "贝果|客服": 102001, "贝紫|粤语": 102002, "贝雪|新闻": 102003}
        # voicetype = QComboBox(self.chat_groupBox)
        # voicetype.addItems(voicetypedict.keys())
        #
        # def voicetypechange(t):
        #     self.settings.setValue("chater/voicetype", voicetypedict[t])
        #
        # voicetype.currentTextChanged.connect(voicetypechange)
        # voicetype.setGeometry(voicebtn.x(), voicebtn.y() + voicebtn.height() + 5, 100, 25)
        # voicetype.setCurrentText(list(voicetypedict.keys())[list(voicetypedict.values()).index(
        #     self.settings.value("chater/voicetype", 7, type=int))])
        # voicetype.setStatusTip("设置音色")
        # voicetype.setToolTip("设置音色")
        """由于腾讯的api改为付费了,所以不显示播放声音(作者没钱啊qaq),如需使用可以打开注释然后在txpythonsdk中修改api即可"""

        self.change_show_item([self.chat_groupBox])

    def BaiduTRA(self):
        items = ['自动检测', '中文', '英语', '文言文', '粤语', '日语', '德语', '韩语', '法语', '俄语', '泰语', '意大利语', '葡萄牙语', '西班牙语']
        self.tra_from = QComboBox(self.tra_groupBox)
        self.tra_from.addItems(items)
        self.tra_from.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.tra_to = QComboBox(self.tra_groupBox)
        self.tra_to.addItems(items[1:])
        self.tra_to.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.tra_from.move(465, 48)
        self.tra_to.move(465, 282)

        self.tra_to_edit = QTextEdit(self.tra_groupBox)
        # self.tra_to_edit.hide()
        self.tra_to_edit.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.tra_to_edit.setGeometry(30, 274, 420, 210)
        self.tra_from_edit = EnterSendQTextEdit(self.tra_groupBox)
        self.tra_from_edit.keyenter_connect(transtalater.Bdtra)
        self.tra_from_edit.setPlaceholderText('在此输入文字')

        self.tra_from_edit.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 9))
        self.tra_from_edit.setGeometry(30, 40, 420, 210)

        self.tra_detal = QPushButton("详细释义", self.tra_groupBox)
        self.tra_detal.setGeometry(465, 230, 86, 20)
        self.tra_detal.setStatusTip('跳转百度翻译网页版查看详细解析...')
        self.tra_detal.clicked.connect(transtalater.show_detal)
        self.trabot = QPushButton("翻译", self.tra_groupBox)
        self.trabot.setStatusTip('开始翻译')
        self.trabot.setGeometry(465, 180, 86, 40)
        self.trabot.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 10))
        self.trabot.clicked.connect(transtalater.Bdtra)

        self.change_show_item([self.tra_groupBox])

    def BaiduOCR(self):
        """利用百度api识别文本"""
        if self.bdocr == True:
            picfile = "j_temp/jam_outputfile.png"
            filename = os.path.basename(picfile)

            with open(picfile, 'rb')as i:
                img = i.read()
            self.ocrthread = OcrimgThread(filename, img, 1)
            if not QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
                self.statusBar().showMessage('正在识别: ' + filename)
                self.ocr_textEdit.clear()
                if not self.OCR:
                    self.ocr()
                self.change_show_item([self.ocr_groupBox])
                self.ocrthread.result_show_signal.connect(self.ocr_textEdit.insertPlainText)
            else:
                self.ocrthread.result_show_signal.connect(self.simplemodebox.insertPlainText)
            self.ocrthread.start()
            QApplication.processEvents()
            self.bdocr = False
        else:
            self.bdocr = True
            self.getandshow()

    def screensh(self):
        # s=time.process_time()
        if self.waiting:
            self.stop_wait = True
            return

        # time.sleep(0.2)
        self.getandshow(ss=True)

    def wait_(self):
        self.waiting = True
        while self.delay > 0 and not self.stop_wait:
            QApplication.processEvents()
            time.sleep(0.1)
            print(self.delay)
            self.delay -= 0.1
            self.ss_timer.setValue(self.delay)
            # QApplication.processEvents()
        self.waiting = False

    def getandshow(self, ss=False):
        if ss:
            try:
                if self.hide_ss.isChecked():
                    self.sshide()
            except:
                self.sshide()
            try:
                self.delay = self.ss_timer.value()
                if self.delay > 0:
                    self.wait_()
                    if self.stop_wait:
                        self.stop_wait = False
                        return
            except:
                print(sys.exc_info(), 3970)
        else:
            self.sshide()
        # self.screenshoter = Slabel(self)
        # self.connectss()
        self.screenshoter.screen_shot()
        # self.setWindowOpacity(1)
        print("截屏")

    def sshide(self):
        # def reshow():
        #     self.setWindowOpacity(1)
        #     self.ssreshowtimer.stop()
        self.setWindowOpacity(0)
        self.settings.setValue("windowx", self.x())
        self.settings.setValue("windowy", self.y())
        self.move(QApplication.desktop().width(),QApplication.desktop().height())
        self.setWindowOpacity(1)
        # self.setWindowOpacity(0)
        # self.hide()

    def connectss(self):
        self.screenshoter.showm_signal.connect(self.trayicon.showM)
        self.screenshoter.recorder_recordchange_signal.connect(self.recorder.recordchange)
        self.screenshoter.close_signal.connect(self.screenshoterinit)

    def screenshoterinit(self):
        print("重置slabel")
        # self.setWindowOpacity(0)
        self.move(self.settings.value("windowx",500,int),self.settings.value("windowy",100,int))
        if PLATFORM_SYS == "darwin":  # macos使用,不然会有切屏
            self.setWindowOpacity(0)
            self.show()
        del self.screenshoter
        time.sleep(0.01)
        print(gc.isenabled(), gc.get_count(), gc.get_freeze_count())
        gc.collect()
        print(gc.isenabled(), gc.get_count(), gc.get_freeze_count())
        print('cleard')

        self.screenshoter = Slabel(self)
        self.connectss()
        if QSettings('Fandes', 'jamtools').value("S_SIMPLE_MODE", False, bool):
            self.hide()
        else:

            self.setWindowOpacity(1)
            self.show()
        # self.setWindowOpacity(1)
        # self.activateWindow()

    def closeEvent(self, event):  # 函数名固定不可变
        # event.ignore()
        self.settings.setValue("windowx", self.x())
        self.settings.setValue("windowy", self.y())
        neverask = self.settings.value('neverask', 'default', type=str)
        if neverask == 'yes':
            self.trayicon.setVisible(False)
            # import shutil
            try:
                if self.recorder.recording:
                    self.recorder.stop_record()
                if transformater.transforma is not None:
                    transformater.stop_transform()
            except:
                print('kill ffmpeg errer')
            try:
                if os.path.exists('video_mergelist.txt'):
                    os.remove('video_mergelist.txt')
                shutil.rmtree("j_temp")
            except:
                print("Unexpected error:", sys.exc_info()[0])
            os._exit(0)
            sys.exit()  # 关闭窗口
        elif neverask == 'hide':
            print("隐藏()")
            self.changesimple()
            event.ignore()
            return
        box = QMessageBox(QMessageBox.Question, u'退出？', u'蒸的要退出吗？(￣y▽,￣)╭ ?\n\n')
        box.setWindowFlags(Qt.WindowStaysOnTopHint)
        box.resize(150, 500)

        checkbox1 = QCheckBox("不再提示", box)
        box.setCheckBox(checkbox1)

        YES = box.addButton('确定', QMessageBox.AcceptRole)
        NO = box.addButton('隐藏', QMessageBox.RejectRole)
        box.setDefaultButton(NO)

        def neveraskchange(text):
            self.settings.setValue('neverask', text)

        reply = box.exec()
        if reply == QMessageBox.AcceptRole:
            try:
                if self.recorder.recording:
                    self.recorder.stop_record()
                if transformater.transforma is not None:
                    transformater.stop_transform()
            except:
                print('kill ffmpeg errer')
            try:
                if os.path.exists('video_mergelist.txt'):
                    os.remove('video_mergelist.txt')
                shutil.rmtree("j_temp")
            except:
                print("Unexpected error:", sys.exc_info()[0])
            if checkbox1.isChecked():
                neveraskchange('yes')

            os._exit(0)
            sys.exit()  # 关闭窗口
        else:
            print("隐藏()")
            self.changesimple()
            if checkbox1.isChecked():
                neveraskchange('hide')
            event.ignore()
        # self.hide()

    def hide(self):
        self.setWindowOpacity(0)
        super().hide()
        # self.setWindowOpacity(1)

    def showEvent(self, e) -> None:
        self.setWindowOpacity(1)
        super(Swindow, self).showEvent(e)


class SettingPage(QScrollArea):
    def __init__(self, parent):
        super(SettingPage, self).__init__()
        self.parent = parent
        self.parent.setEnabled(False)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('设置')
        self.settings = QSettings('Fandes', 'jamtools')
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.move(parent.x() + parent.width() // 3, parent.y() + 50)
        self.setFixedSize(500, 500)
        self.setWindowFlags(Qt.Tool)
        self.settings_widget = QWidget()
        self.settings_widget.setGeometry(0, 0, 500, 1100)
        self.setWidget(self.settings_widget)
        self.setFont(QFont('黑体' if PLATFORM_SYS == "win32" else "", 10))
        self.setStyleSheet("QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                           "QPushButton:hover{color:green;background-color:rgb(200,200,100);}"

                           "QGroupBox{border:1px solid gray;background-color:rgb(250,250,250);}"
                           """QLineEdit{
                            border:1px solid gray;
                            width:300px;
                            border-radius:10px;
                            padding:2px 4px;
                            background-color:rgb(250,250,250);}"""
                           """QComboBox{padding:2px 4px;}"""
                           """QComboBox QAbstractItemView::item{
                            height:36px;
                            color:#666666;
                            padding-left:9px;
                            background-color:#FFFFFF;
                            }
                            QComboBox QAbstractItemView::item:hover{ //悬浮
                              background-color:#409CE1;
                              color:#ffffff;
                            }
                            QComboBox QAbstractItemView::item:selected{//选中
                              background-color:#409CE1;
                              color:#ffffff;
                            }"""
                           "QScrollBar{background-color:rgb(200,200,200);width: 8px;}")

        self.close_dict = {0: 'hide', 1: 'yes', 2: 'default'}
        groub = QGroupBox(self.settings_widget)
        groub.setGeometry(70, 30, 350, 150)
        auto_run = QCheckBox('开机启动', groub)
        auto_run.setToolTip('开机启动')
        close_note = QCheckBox('关闭通知', groub)
        close_note.setToolTip('关闭一些功能性通知')

        ocr_rightbtton = QCheckBox('右键划屏提字', groub)
        ocr_rightbtton.setToolTip('右键水平右划时识别划过的文字并翻译')
        close_box = QGroupBox('关闭窗口时:', groub)
        close_box.setToolTip('关闭窗口时的动作')
        self.closechoise = QComboBox(close_box)
        self.closechoise.addItems(['开启极简模式', '直接关闭!', '提示选择'])
        clo = self.settings.value('neverask', 'default', str)
        if clo == 'yes':
            self.closechoise.setCurrentIndex(1)
        elif clo == 'default':
            self.closechoise.setCurrentIndex(2)

        auto_run.move(10, 10)
        close_note.move(auto_run.x(), auto_run.y() + 30)

        ocr_rightbtton.move(close_note.x(), close_note.y() + 30)
        close_box.setGeometry(180, 15, 150, 50)
        self.closechoise.setGeometry(10, 18, 130, 20)
        self.closechoise.currentTextChanged.connect(self.change_close)

        auto_run.setChecked(self.settings.value('auto_run', False, type=bool))
        auto_run.stateChanged.connect(self.auto_run_change)

        ocr_rightbtton.setChecked(self.settings.value('right_ocr', False, bool))
        ocr_rightbtton.stateChanged.connect(self.right_ocr_setting_save)

        close_note.setChecked(self.settings.value('close_notice', False, type=bool))
        close_note.stateChanged.connect(lambda a: self.settings.setValue("close_notice", bool(a)))

        # 智能shift键
        shiftbox = QGroupBox("智能剪切板", self.settings_widget)
        shiftbox.setGeometry(groub.x(), groub.y() + groub.height() + 10, 350, 150)
        self.smartShift = QCheckBox('智能shift键', shiftbox)
        self.smartShift.setToolTip('复制文本后按shift键显示并翻译,占用极低')
        self.smartShift.move(10, 20)
        self.smartShift.setChecked(self.settings.value('smartShift', True, bool))

        self.timeoutshift = QSpinBox(shiftbox)
        self.timeoutshift.setSuffix("s内触发")
        self.timeoutshift.setToolTip("剪切板改变n秒内按下shift键才触发")
        self.timeoutshift.move(self.smartShift.x() + self.smartShift.width() + 20, self.smartShift.y())
        self.timeoutshift.valueChanged.connect(lambda a: self.settings.setValue("timeoutshift", a))
        self.timeoutshift.setValue(self.settings.value("timeoutshift", 7, type=int))

        self.shiftFY = QCheckBox("翻译", shiftbox)
        self.shiftFY.move(self.smartShift.x(), self.smartShift.y() + self.smartShift.height())
        self.shiftFY.stateChanged.connect(lambda a: self.settings.setValue("shiftFY", bool(a)))
        self.shiftFY.setToolTip("剪切板内容改变n秒内按下shift键为则翻译")
        self.shiftFY.setChecked(self.settings.value("shiftFY", True, bool))
        self.shiftFYzh = QCheckBox("翻译中文", shiftbox)
        self.shiftFYzh.move(self.timeoutshift.x(), self.shiftFY.y())
        self.shiftFYzh.stateChanged.connect(lambda a: self.settings.setValue("shiftFYzh", bool(a)))
        self.shiftFYzh.setToolTip("剪切板内容为中文时按下shift键翻译为英文")
        self.shiftFYzh.setChecked(self.settings.value("shiftFYzh", False, bool))

        self.openhtmlbtn = QCheckBox('识别网址', shiftbox)
        self.openhtmlbtn.setToolTip("识别到复制网址时7s内按下shift直接在浏览器打开网址")
        self.openhtmlbtn.stateChanged.connect(lambda a: self.settings.setValue("openhttp", bool(a)))
        self.openhtmlbtn.setChecked(self.settings.value("openhttp", True, bool))
        self.openhtmlbtn.move(self.shiftFY.x(), self.shiftFY.y() + self.shiftFY.height())
        self.openhtmlonce = QCheckBox("整段匹配", shiftbox)
        self.openhtmlonce.setToolTip("当复制到的文本为纯网址时才打开,取消选中将从文字中提取网址")
        self.openhtmlonce.stateChanged.connect(lambda a: self.settings.setValue("openhttpOnce", bool(a)))
        self.openhtmlonce.setChecked(self.settings.value("openhttpOnce", False, bool))
        self.openhtmlonce.setEnabled(self.openhtmlbtn.isChecked())
        self.openhtmlonce.move(self.timeoutshift.x(), self.openhtmlbtn.y())
        self.shiftopendir = QCheckBox("打开文件夹路径", shiftbox)
        self.shiftopendir.move(self.openhtmlbtn.x() , self.openhtmlbtn.y()+ self.openhtmlbtn.height())
        self.shiftopendir.stateChanged.connect(lambda a: self.settings.setValue("shiftopendir", bool(a)))
        self.shiftopendir.setChecked(self.settings.value("shiftopendir", True, bool))
        self.shiftopendir.setToolTip("剪切板内容改变n秒内按下shift键,识别到剪切板复制有文件路径则直接打开文件(夹)所在位置")
        self.smartShift.stateChanged.connect(self.smartShiftsetting_save)
        self.smartShiftsetting_save(self.smartShift.isChecked())
        # 快捷键
        groub1 = QGroupBox('快捷键', self.settings_widget)
        groub1.setGeometry(shiftbox.x(), shiftbox.y() + shiftbox.height() + 10, 350, 150)
        # control_kjj = QCheckBox('控制快捷键', groub1)
        # control_kjj.setToolTip('酱控制的快捷键开关,打开后将可以用快捷键Alt+1录制,Alt+2播放鼠标键盘动作!')
        # control_kjj.setChecked(self.settings.value('can_controll', False, type=bool))
        # control_kjj.stateChanged.connect(setting_save)
        # control_kjj.move(10, 30)

        # 百度ai api
        api_groub = QGroupBox('百度AI API', self.settings_widget)
        api_groub.setToolTip('可以自己申请百度的api用于文字识别、图像识别，作者的调用量有限。。，申请网址见主菜单“关于作品描述”')
        api_groub.setGeometry(groub1.x(), groub1.y() + groub1.height() + 20, 350, 110)
        self.appid = QLineEdit(api_groub)
        self.appid.setPlaceholderText('APP_ID填在这里')
        self.appid.setGeometry(10, 18, 160, 20)
        self.apikey = QLineEdit(api_groub)
        self.apikey.setPlaceholderText('API_KEY填在这里')
        self.apikey.setGeometry(self.appid.x(), self.appid.y() + self.appid.height(), 160, 20)
        self.secrectkey = QLineEdit(api_groub)
        self.secrectkey.setPlaceholderText('SECRECT_KEY填在这里')
        self.secrectkey.setGeometry(self.apikey.x(), self.apikey.y() + self.apikey.height(), 160, 20)

        ok_apibutton = QPushButton('验证', api_groub)
        ok_apibutton.move(self.secrectkey.x(), self.secrectkey.y() + self.secrectkey.height())
        ok_apibutton.clicked.connect(self.apichange)

        # 翻译api
        fyapi_groub = QGroupBox('百度翻译 API', self.settings_widget)
        fyapi_groub.setToolTip('可以自己申请百度翻译api用于翻译，作者也没多少调用量了。。免费申请网址见“关于作品”')
        fyapi_groub.setGeometry(api_groub.x(), api_groub.y() + api_groub.height() + 20, 350, 95)
        self.fyappid = QLineEdit(fyapi_groub)
        self.fyappid.setPlaceholderText('APP_ID填在这里')
        self.fyappid.setGeometry(10, 18, 160, 20)
        self.fyapikey = QLineEdit(fyapi_groub)
        self.fyapikey.setPlaceholderText('API_KEY填在这里')
        self.fyapikey.setGeometry(self.fyappid.x(), self.fyappid.y() + self.fyappid.height(), 160, 20)

        ok_button = QPushButton('验证', fyapi_groub)
        ok_button.move(self.fyapikey.x(), self.fyapikey.y() + self.fyapikey.height())
        ok_button.clicked.connect(self.fyapichange)

        self.grab_widthbox = QGroupBox('划屏提字', self.settings_widget)
        self.grab_widthbox.setGeometry(fyapi_groub.x(), fyapi_groub.y() + fyapi_groub.height() + 20, 200, 150)
        self.grab_widthbox.setEnabled(self.settings.value('right_ocr', False, bool))
        grab_label = QLabel('大概和这个框↓一样高', self.grab_widthbox)
        grab_label.setGeometry(10, 20, 200, 20)
        self.grab_setedit = QSpinBox(self.grab_widthbox)
        self.grab_setedit.setPrefix('高度:')
        self.grab_setedit.setToolTip('设置划屏时截取鼠标附近的屏幕高度')
        self.grab_setedit.setSuffix('px')
        self.grab_setedit.setGeometry(grab_label.x(), grab_label.y() + grab_label.height() + 10, 100, self.settings.value('grab_height', 28))
        self.grab_setedit.setValue(self.settings.value('grab_height', 28))
        self.grab_setedit.valueChanged.connect(self.grab_height_change)
        self.grab_setedit.setMinimum(20)
        self.grab_setedit.setMaximum(100)



        self.settings_widget.show()
        self.show()
        self.raise_()
        self.setFocus()
        self.activateWindow()

    def right_ocr_setting_save(self):
        if self.settings.value('right_ocr', False, bool):
            self.parent.closelistenmouse()
        else:
            self.parent.openlistenmouse()
        self.settings.setValue('right_ocr', not self.settings.value('right_ocr', False, bool))
        self.grab_widthbox.setEnabled(self.settings.value('right_ocr', False, bool))

    # 自启动
    def auto_run_change(self):
        appPath = QApplication.applicationFilePath().replace("/", "\\")
        appName = QApplication.applicationName()
        setting = QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                            QSettings.NativeFormat)
        if not self.settings.value('auto_run', False, type=bool):
            try:
                setting.setValue(appName, '"' + appPath + '"')
                self.settings.setValue('auto_run', True)
                print('setrun')
            except:
                print('设置自启动失败')
        else:
            try:
                setting.remove(appName)
                self.settings.setValue('auto_run', False)
                print('removerun')
            except:
                print('移除自启动失败')

    # 关闭动作
    def change_close(self, a):
        print(self.close_dict[self.closechoise.currentIndex()])
        self.settings.setValue('neverask', self.close_dict[self.closechoise.currentIndex()])

    # 划屏提字宽度
    def grab_height_change(self, value):
        self.settings.setValue('grab_height', value)
        self.parent.simg.h = value
        self.grab_setedit.resize(self.grab_setedit.width(),value)

    def smartShiftsetting_save(self, a):
        self.settings.setValue("smartShift", bool(a))
        self.openhtmlbtn.setEnabled(a)
        self.openhtmlonce.setEnabled(a)
        self.shiftFY.setEnabled(a)
        self.timeoutshift.setEnabled(a)

    def apichange(self):
        global API_KEY, APP_ID, SECRECT_KEY
        try:
            if len(self.appid.text()) > 5 and len(self.apikey.text()) > 5 and len(self.secrectkey.text()) > 5:
                tAPP_ID = self.appid.text()
                tAPI_KEY = self.apikey.text()
                tSECRECT_KEY = self.secrectkey.text()
                QPixmap(':/OCR.png').save('ocr.png')
                with open('ocr.png', 'rb')as file:
                    img = file.read()
                client = AipOcr(tAPP_ID, tAPI_KEY, tSECRECT_KEY)
                message = client.basicGeneral(img)  # 通用文字识别，每天 50 000 次免费
                print(message)
                if 'error_code' in message.keys():
                    print('appid错误!')
                    raise ConnectionError
                else:
                    print('appid 正确')
                    APP_ID = self.appid.text()
                    API_KEY = self.apikey.text()
                    SECRECT_KEY = self.secrectkey.text()
                    self.settings.setValue('BaiduAI_APPID', APP_ID)
                    self.settings.setValue('BaiduAI_APPKEY', API_KEY)
                    self.settings.setValue('BaiduAI_SECRECT_KEY', SECRECT_KEY)
            else:
                raise ConnectionError
        except:
            QMessageBox.warning(self, "设置失败", "验证失败!", QMessageBox.Yes)
            self.showm_signal.emit('无效账号!')
        else:
            QMessageBox.information(self, "设置成功",
                                    "设置成功\n请自行留意api的调用量!感谢你的支持!\n(可通过重置设置重置api为作者的测试api)", QMessageBox.Yes)
            self.appid.setPlaceholderText(self.appid.text())

    def fyapichange(self):
        try:
            if len(self.fyappid.text()) > 5 and len(self.fyapikey.text()) > 5:
                tAPP_ID = self.fyappid.text()  # 20190928000337891
                tAPI_KEY = self.fyapikey.text()  # SiNITAufl_JCVpk7fAUS
                salt = str(random.randint(32768, 65536))
                text0 = 'text'
                sign = tAPP_ID + text0 + salt + tAPI_KEY
                m1 = hashlib.md5()
                m1.update(sign.encode(encoding='utf-8'))
                sign = m1.hexdigest()
                myurl = '/api/trans/vip/translate' + '?appid=' + tAPP_ID + '&q=' + quote(
                    text0) + '&from=' + 'auto' + '&to=' + 'zh' + '&salt=' + str(
                    salt) + '&sign=' + sign
                httpClient0 = http.client.HTTPConnection('api.fanyi.baidu.com')
                httpClient0.request('GET', myurl)
                response = httpClient0.getresponse()
                s = response.read().decode('utf-8')
                s = eval(s)
                print(s)
                if 'error_code' in s.keys():
                    print('appid错误!')
                    raise ConnectionError
                else:
                    print('appid 正确')
                    self.settings.setValue('tran_appid', self.fyappid.text())
                    self.settings.setValue('tran_secretKey', self.fyapikey.text())
            else:
                raise ConnectionError
        except:
            QMessageBox.warning(self, "设置失败", "验证失败!", QMessageBox.Yes)
        else:
            QMessageBox.information(self, "设置成功",
                                    "设置成功\n请自行留意api的调用量!感谢你的支持!\n(可通过重置设置重置api为作者的测试api)", QMessageBox.Yes)

    def closeEvent(self, e) -> None:
        super(SettingPage, self).closeEvent(e)
        self.parent.setEnabled(True)


class Transforma(QObject):
    showm_signal = pyqtSignal(str)

    def __init__(self, parent: Swindow):
        super(Transforma, self).__init__()
        self.parent = parent
        self.init_transforma_thread = Commen_Thread(self.init_transforma)
        self.init_transforma_thread.start()
        self.showm_signal.connect(self.parent.trayicon.showM)

    def init_transforma(self):
        self.stoper = False
        self.name = None
        self.transforma = None
        self.open_path = None
        self.time = None
        self.gifzip_running = False
        self.ffmpeg_running = False
        self.add_logo_path = ''
        self.f_path = '"' + ffmpeg_path + '/ffmpeg" '
        self.g_path = '"' + ffmpeg_path + '/gifsicle" '
        if not os.path.exists(QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + "/JamPicture"):
            os.mkdir(QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + "/JamPicture")

        if not os.path.exists(QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video'):
            os.mkdir(QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video')
        if not os.path.exists(QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio'):
            os.mkdir(QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio')
        if not os.path.exists(temp_path + '/pictovd/'):
            os.mkdir(temp_path + '/pictovd/')

    def piccut(self, pic_paths):
        self.set_style(self.parent.piccut_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        try:
            for pic_path in pic_paths:
                img = Image.open(pic_path)
                sp = self.parent.piccut_spnu.value()
                sz = self.parent.piccut_sznu.value()
                filepath = QFileInfo(pic_path).path()
                createpath = QFileInfo(pic_path).completeBaseName().replace(' ', '') + '/'
                if not os.path.exists(filepath + '/cut_' + createpath):
                    os.mkdir(filepath + '/cut_' + createpath)

                xw, yw = img.size[0] / sp, img.size[1] / sz
                for i in range(sp):
                    for j in range(sz):
                        img_get = img.crop((xw * i, yw * j, xw * (i + 1), yw * (j + 1)))

                        img_get.save(filepath + '/cut_' + createpath + self.name + 'part' + str(
                            j) + str(
                            i) + '.png')
        except:
            self.showm_signal.emit('裁剪失败，注意裁剪份数不能超出图片尺寸')
        else:
            self.showm_signal.emit("裁剪完成，文件保存于：原目录\n点击此处可打开")
            self.parent.statusBar().showMessage("处理完成，文件保存于：原目录")
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QFileInfo(pic_paths[0]).path()
        self.reset_style(self.parent.piccut_pushButton)

    def picSplicing(self, pics):
        if not self.parent.t_pic.isVisible():
            # 图片拼接
            self.set_style(self.parent.picSplicing_pushButton)
            im_list = [Image.open(fn) for fn in pics]
            self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
            if self.parent.hx.isChecked():
                w = 0
                maxH = 0
                for i in im_list:
                    w += i.size[0]
                    maxH = max(maxH, i.size[1])
                if self.parent.picgsh.isChecked():
                    for j, i in enumerate(im_list):
                        s = maxH / i.size[1]
                        im_list[j] = i.resize((int(i.size[0] * s), int(i.size[1] * s)), Image.BILINEAR)
                    w = 0
                    for i in im_list:
                        w += i.size[0]
                        maxH = max(maxH, i.size[1])
                newpic = Image.new(im_list[0].mode, (w, maxH))
                ew = 0
                for i in im_list:
                    newpic.paste(i, (ew, 0))
                    ew += i.size[0]
                newpic.save(QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation) + '/JamPicture/' + self.name + 'Splicing.png')

            else:
                h = 0
                maxW = 0
                for i in im_list:
                    h += i.size[1]
                    maxW = max(maxW, i.size[0])
                if self.parent.picgsh.isChecked():
                    for j, i in enumerate(im_list):
                        s = maxW / i.size[0]
                        im_list[j] = i.resize((int(i.size[0] * s), int(i.size[1] * s)), Image.BILINEAR)
                    h = 0
                    for i in im_list:
                        h += i.size[1]
                        maxW = max(maxW, i.size[0])
                newpic = Image.new(im_list[0].mode, (maxW, h))
                eh = 0
                for i in im_list:
                    newpic.paste(i, (0, eh))
                    eh += i.size[1]
                newpic.save(QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation) + '/JamPicture/' + self.name + 'Splicing.png')
            self.showm_signal.emit("图片拼接完成，文件保存于：\n图片/JamPicture/" + self.name + '.png\n点击此处可打开')
            self.parent.statusBar().showMessage("图片拼接完成，文件保存于：图片/JamPicture/" + self.name + '.png')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            print(111)
            self.open_path = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation) + '/JamPicture/'
            self.reset_style(self.parent.picSplicing_pushButton)

        else:
            # 调整分辨率
            def reorient_image(im):
                """相机图片旋转数据获取并修正"""
                try:
                    image_exif = im._getexif()
                    image_orientation = image_exif[274]
                    if image_orientation in (2, '2'):
                        return im.transpose(Image.FLIP_LEFT_RIGHT)
                    elif image_orientation in (3, '3'):
                        return im.transpose(Image.ROTATE_180)
                    elif image_orientation in (4, '4'):
                        return im.transpose(Image.FLIP_TOP_BOTTOM)
                    elif image_orientation in (5, '5'):
                        return im.transpose(Image.ROTATE_90).transpose(Image.FLIP_TOP_BOTTOM)
                    elif image_orientation in (6, '6'):
                        return im.transpose(Image.ROTATE_270)
                    elif image_orientation in (7, '7'):
                        return im.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)
                    elif image_orientation in (8, '8'):
                        return im.transpose(Image.ROTATE_90)
                    else:
                        return im
                except (KeyError, AttributeError, TypeError, IndexError):
                    print(sys.exc_info())
                    return im

            pic_rotate = self.parent.t_pic_rotate.value()
            quality = self.parent.t_pic_quality.value() * 95 // 100
            print(",quality=quality", quality)
            bspt = QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + '/JamPicture/'
            pt = bspt + "resize" + str(time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())) + "/"
            if not os.path.exists(pt):
                os.mkdir(pt)
            self.set_style(self.parent.t_pic_pushButton)
            format = self.parent.t_pic_format.currentText()
            if self.parent.t_pic_bc.isChecked():
                w = self.parent.t_pic_sp.value()
                for i in pics:
                    name = pt + QFileInfo(i).completeBaseName() + "." + format
                    pic = Image.open(i)
                    pic = reorient_image(pic)
                    if self.parent.t_pic_changesize.isChecked():
                        scale = w / pic.size[0]
                        s = (w, int(pic.size[1] * scale))
                        pic = pic.resize(s, Image.ANTIALIAS)

                    if pic_rotate != 0:
                        pic = pic.rotate(pic_rotate)
                    if format == 'jpg':
                        pic = pic.convert("RGB")
                        pic.save(name, quality=quality)
                    else:
                        pic.save(name, quality=quality)
            else:
                s = (self.parent.t_pic_sp.value(), self.parent.t_pic_sz.value())
                for i in pics:
                    name = pt + QFileInfo(i).completeBaseName() + "." + format
                    # print(name)
                    pic = Image.open(i)
                    if self.parent.t_pic_changesize.isChecked():
                        pic = pic.resize(s, Image.ANTIALIAS)
                    if pic_rotate != 0:
                        pic = pic.rotate(pic_rotate)
                    if format == 'jpg':
                        pic = pic.convert("RGB")
                        pic.save(name, quality=quality)
                    else:
                        pic.save(name, quality=quality)
            self.showm_signal.emit('处理完成，文件保存于：\n图片/JamPicture/文件夹\n点击此处可打开')
            self.parent.statusBar().showMessage('处理完成，文件保存于：图片/JamPicture文件夹')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = pt
            self.reset_style(self.parent.t_pic_pushButton)

    def video_cut(self, vd):
        self.set_style(self.parent.video_cut_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        fileinfo = QFileInfo(vd).suffix()
        form_t = self.parent.vd_cutform.time().toString("HH:mm:ss")
        to_t = self.parent.vd_cutto.time().toString("HH:mm:ss")
        dt = ' '
        if to_t != '00:00:00':
            dt = ' -ss ' + form_t + ' -to ' + to_t
        try:
            self.transforma = subprocess.Popen(
                self.f_path + dt + ' -accurate_seek -i "' + vd + '" -codec copy '
                                                                 '-avoid_negative_ts 1 '
                + QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/part' + self.name + '.' + fileinfo
                + ' -y',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except:
            self.parent.statusBar().showMessage('出现错误，请确保输入时间段正确')
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("视频裁剪完成，文件保存于：\n视频/jam_video/part" + self.name + '\n点击此处可打开')
            self.parent.statusBar().showMessage("视频裁剪完成，文件保存于：视频/jam_video/part" + self.name)
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/'
        self.reset_style(self.parent.video_cut_pushButton)

    def video_merge(self, vds):
        self.set_style(self.parent.video_merge_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        fileinfo = QFileInfo(vds[0]).suffix()
        # self.showm_signal.emit("正在处理，请耐心等待。。。")
        with open('video_mergelist.txt', 'w+')as f:
            s = ''
            for i in vds:
                s += "file '%s'\n" % i

            f.write(s)

        try:
            self.transforma = subprocess.Popen(
                self.f_path + " -f concat -safe 0 -i video_mergelist.txt -c copy " + QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/merge' + self.name + '.' + fileinfo
                + ' -y',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except:
            self.parent.statusBar().showMessage('出现错误，请确保名称内没有空格等非法字符')
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("视频拼接完成，文件保存于：\n视频/jam_video/merge" + self.name + '\n点击此处可打开')
            self.parent.statusBar().showMessage("视频拼接完成，文件保存于：视频/jam_video/merge" + self.name)
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/'
        self.reset_style(self.parent.video_merge_pushButton)

    def audio_cut(self, ad):
        self.set_style(self.parent.audio_cut_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        fileinfo = QFileInfo(ad).suffix()
        form_t = self.parent.ad_cutform.time().toString("HH:mm:ss")
        to_t = self.parent.ad_cutto.time().toString("HH:mm:ss")
        dt = ' '
        if to_t != '00:00:00':
            dt = ' -ss ' + form_t + ' -to ' + to_t

        try:
            print(self.f_path + dt + ' -i "' + ad + '" -codec copy '
                  + QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/part' + self.name + '.' + fileinfo)
            self.transforma = subprocess.Popen(
                self.f_path + ' -ss ' + form_t + ' -to ' + to_t + ' -i "' + ad + '" -codec copy '
                + QStandardPaths.writableLocation(
                    QStandardPaths.MusicLocation) + '/jam_audio/part' + self.name + '.' + fileinfo
                + ' -y',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        except:
            self.parent.statusBar().showMessage('出现错误，请确保输入时间段正确')
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("音频裁剪完成，文件保存于：\n音乐/jam_audio/part" + self.name + '\n点击此处可打开')
            self.parent.statusBar().showMessage("音频裁剪完成，文件保存于：音乐/jam_audio/part" + self.name)
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/'
        self.reset_style(self.parent.audio_cut_pushButton)

    def audio_Splicing(self, ads):
        self.set_style(self.parent.audio_Splicing_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        fileinfo = QFileInfo(ads[0]).suffix()
        with open('video_mergelist.txt', 'w+')as f:
            s = ''
            for i in ads:
                s += "file '%s'\n" % i

            f.write(s)

        try:
            self.transforma = subprocess.Popen(
                self.f_path + " -f concat -safe 0 -i video_mergelist.txt -c copy " + QStandardPaths.writableLocation(
                    QStandardPaths.MusicLocation) + '/jam_audio/merge' + self.name + '.' + fileinfo
                + ' -y',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except:
            self.parent.statusBar().showMessage('出现错误，请确保名称内没有空格等非法字符')
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("音频拼接完成，文件保存于：\n音乐/jam_audio/merge" + self.name + '\n点击此处可打开')
            self.parent.statusBar().showMessage("音频拼接完成，文件保存于：视频/jam_video/merge" + self.name)
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/'
        self.reset_style(self.parent.audio_Splicing_pushButton)

    def t_video(self, vds, recording=False):
        print(vds)
        t_videofile_format = 'gif'
        dt = fps = video_w = keep_ws = out_file = ' '
        vd_speed = ["" for i in range(len(vds))]
        if not recording:
            self.set_style(self.parent.t_video_pushButton)
            t_videofile_format = self.parent.t_videofile_format.currentText()
            t_code_format = self.parent.t_code_format.currentText()
            video_w = ' -vf scale=%d:-2 ' % self.parent.t_videoscale.value()
            # t_qp = ' -qp ' + str(self.parent.t_qp.value()) + ' '
            t_form = self.parent.t_form.time().toString('HH:mm:ss')
            t_to = self.parent.t_to.time().toString('HH:mm:ss')
            dt = ' -ss ' + t_form + ' -to ' + t_to
            preset = self.parent.t_preset_format.currentText()
            fps = ' -r ' + str(self.parent.t_videofps.value()) + ' '
            speed = self.parent.t_vd_speed.value()
            vdfileformat = os.path.splitext(vds[0])[1][1:]
            print(vdfileformat, t_videofile_format)
            if video_w == ' -vf scale=0:-2 ':
                video_w = ' '
            if t_to == '00:00:00':
                dt = ' '
            if fps == ' -r 0.0 ':
                fps = ' '
                # print('fps 原来')
            if t_code_format == '自动选择' and t_videofile_format in ('mp4', 'flv'):
                t_code_format = 'H.264'
            # self.showm_signal.emit("正在处理，请耐心等待。。。")
            out_file = ' '
            keep_ws = ''
            if self.parent.t_nondestructive.isChecked() and t_code_format == 'H.264' and \
                    vdfileformat != t_videofile_format:
                keep_ws = ' -qp 0 '
                # print('qp 0')
            if t_code_format == 'H.264':
                out_file = ' -profile:v high444 -level 4.2  ' \
                           '-preset:v ' + preset + \
                           ' -preset:a  ' + preset + ' -vcodec libx264 ' + keep_ws
                if self.parent.hardware_transforma.isChecked():
                    out_file = ' -profile:v high  ' \
                               '-preset:v ' + preset + \
                               ' -preset:a  ' + preset + ' -vcodec h264_nvenc ' + keep_ws
            elif t_code_format == 'H.265':
                out_file = ' -vcodec libx265 '
            elif t_code_format == 'mpeg4':
                out_file = ' -vcodec mpeg4 '
            elif t_code_format == 'wmv1':
                out_file = ' -vcodec wmv1 '
            elif t_code_format == 'wmv2':
                out_file = ' -vcodec wmv2 '
            else:
                out_file = ' '

            if speed != 1:
                vd_speed = []
                for vd in vds:
                    info_finder = subprocess.Popen(
                        self.f_path + r' -i "' + str(
                            vd) + '"',
                        shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                    info = info_finder.stderr.read().lower()
                    if "stream #0:1" not in info or "audio" not in info:
                        print("无音频")
                        vd_speed.append(' -filter:v "setpts={:.2f}*PTS" '.format(1 / speed))
                    else:
                        vd_speed.append(
                            ' -filter_complex "[0:v]setpts={:.2f}*PTS[v];[0:a]atempo={:.2f}[a]" -map "[v]" -map "[a]" '.format(
                                1 / speed, speed))
        if t_videofile_format == 'gif':
            print('is gif')
            for vd in vds:
                self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
                print(vd)
                # if vd_speed == '':
                #     vd_speed = ' -codec copy '
                if not recording:
                    # if self.parent.t_videofps.value() == 0:
                    #     fps = ' -r 9 '
                    self.transforma = subprocess.Popen(
                        self.f_path + ' -i "' + vd + '"' + dt + fps + video_w + vd_speed[0] + keep_ws + temp_path +
                        '/j_temp/temp_video.mp4'
                        + ' -y',
                        shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                    self.transforma.wait()
                    print('视频输出')
                self.transforma = subprocess.Popen(
                    self.f_path + ' -i "' + temp_path + '/j_temp/temp_video.mp4" -filter_complex "[0:v] palettegen" ' + temp_path
                    + '/j_temp/palette.png'
                    + ' -y',
                    shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                self.transforma.wait()
                print('取样图片输出')
                self.transforma = subprocess.Popen(
                    self.f_path + ' -i "' + temp_path + '/j_temp/temp_video.mp4" -i ' + temp_path +
                    '/j_temp/palette.png -filter_complex "[0:v][1:v] paletteuse" ' +
                    QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation) + '/jam_video/t' + self.name + '.gif'
                    + ' -y',
                    shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                self.transforma.wait()
                if os.path.exists(temp_path + '/j_temp/temp_video.mp4'):
                    os.remove(temp_path + '/j_temp/temp_video.mp4')
                    print('del tempfile')
                print('gif输出')
        else:
            for i, vd in enumerate(vds):
                print("正在处理", vd)
                self.showm_signal.emit("正在处理{}".format(vd))
                self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
                # try:
                print(
                    self.f_path + ' -i "' + vd + '"' + dt + ' -pix_fmt yuv420p ' + fps + video_w + vd_speed[
                        i] + out_file +
                    QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation) + '/jam_video/t' + self.name + '.' + t_videofile_format
                    + ' -y')
                self.transforma = subprocess.Popen(
                    self.f_path + ' -i "' + vd + '"' + dt + ' -pix_fmt yuv420p ' + fps + video_w + vd_speed[
                        i] + out_file +
                    QStandardPaths.writableLocation(
                        QStandardPaths.MoviesLocation) + '/jam_video/t' + self.name + '.' + t_videofile_format
                    + ' -y',
                    shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                self.transforma.wait()
                if self.stoper:
                    break
        if not recording:
            self.reset_style(self.parent.t_video_pushButton)
            if self.stoper:
                self.stoper = False
                self.showm_signal.emit('操作已中止！')
            else:
                self.showm_signal.emit("视频处理完成，文件保存于：\n视频/jam_video/t" + self.name + '\n点击此处可打开')
                self.parent.statusBar().showMessage("视频处理完成，文件保存于：\n视频/jam_video/t" + self.name)
                self.parent.trayicon.tran_open = True
        else:
            self.showm_signal.emit("gif生成完毕，文件保存于：\n视频/jam_video/t" + self.name + '\n点击此处可打开')
            self.parent.statusBar().showMessage("gif生成完毕，文件保存于：\n视频/jam_video/t" + self.name)
            self.parent.trayicon.tran_open = True

        self.time = time.time()
        self.open_path = QStandardPaths.writableLocation(
            QStandardPaths.MoviesLocation) + '/jam_video/'

    def t_audio(self, aus):
        self.set_style(self.parent.t_audio_pushButton)
        t_audiofile_format = self.parent.t_audiofile_format.currentText()
        t_aar = ' -ar ' + self.parent.t_aar.currentText()
        t_ac = ' -ac ' + str(self.parent.t_ac.value())
        t_form = self.parent.t_aform.time().toString('HH:mm:ss')
        t_to = self.parent.t_ato.time().toString('HH:mm:ss')
        dt = ' '
        if t_to != '00:00:00':
            dt = ' -ss ' + t_form + ' -to ' + t_to
        if t_aar == ' -ar 0':
            t_aar = ' '
        if t_ac == ' -ac 0':
            t_ac = ' '

        # self.showm_signal.emit("正在处理，请耐心等待。。。")
        out_file = '.' + t_audiofile_format

        for ad in aus:
            self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
            print(self.f_path + ' -i "' + ad + '"' + dt + ' ' + t_aar + ' ' + t_ac + ' ' +
                  QStandardPaths.writableLocation(
                      QStandardPaths.MusicLocation) + '/jam_audio/t' + self.name + out_file
                  + ' -y')
            self.transforma = subprocess.Popen(
                self.f_path + ' -i ' + '"' + ad + '"' + dt + ' ' + t_aar + ' ' + t_ac + ' ' +
                QStandardPaths.writableLocation(
                    QStandardPaths.MusicLocation) + '/jam_audio/t' + self.name + out_file
                + ' -y',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            # except:
            #     self.parent.statusBar().showMessage('出现错误，请确保输入时间段正确')
            self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("视频处理完成，文件保存于：\n音乐/jam_audio/t" + self.name + out_file + '\n点击此处可打开')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/'
        self.reset_style(self.parent.t_audio_pushButton)

    def gifzip(self, gifs):
        self.set_style(self.parent.gifzip_pushButton)
        scale = ' --scale ' + str(self.parent.gifscale.value())
        color = ' --colors ' + str(self.parent.gifcolor.currentText())
        # self.showm_signal.emit("正在处理，可能存在卡顿，请耐心等待。。。")

        if color == ' --colors 0':
            color = ' '
        for gif in gifs:
            self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
            print(self.g_path + ' -O3 ' + '"' + gif + '"' + scale + color + ' ' + ' -o ' +
                  QStandardPaths.writableLocation(
                      QStandardPaths.MusicLocation) + '/jam_audio/t' + self.name + '.gif')
            self.transforma = subprocess.Popen(
                self.g_path + ' -O3 ' + '"' + gif + '"' + scale + color + ' ' + ' -o ' +
                QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation) + '/JamPicture/gifzip' + self.name + '.gif',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.transforma.wait()
            self.showm_signal.emit('处理完成，文件保存于：\n图片/JamPicture/文件夹\n点击此处可打开')
            self.parent.statusBar().showMessage('处理完成，文件保存于：图片/JamPicture文件夹')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + '/JamPicture/'
        self.reset_style(self.parent.gifzip_pushButton)

    def extract_ad_form_vd(self, vd):
        self.set_style(self.parent.extract_ad_form_vd_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        self.transforma = subprocess.Popen(
            self.f_path + ' -i "' + vd + '" -vn ' +
            QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/extract' + self.name + '.mp3'
            + ' -y',
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("视频处理完成，文件保存于：\n音乐/jam_audio/extract" + self.name + '\n点击此处可打开')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/'
        self.reset_style(self.parent.extract_ad_form_vd_pushButton)

    def extract_vd_form_vd(self, vd):
        self.set_style(self.parent.extract_vd_form_vd_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        self.transforma = subprocess.Popen(
            self.f_path + ' -i "' + vd + '" -an   ' +
            QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/extract' + self.name + '.mp4'
            + ' -y',
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("视频处理完成，文件保存于：\n视频/jam_video/extract" + self.name + '\n点击此处可打开')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/'
        self.reset_style(self.parent.extract_vd_form_vd_pushButton)

    def extract_pic_form_vd(self, vds):
        self.set_style(self.parent.extract_pic_form_vd_pushButton)
        fps = ' -r ' + str(self.parent.extract_pic_fps.value()) + ' '
        # self.showm_signal.emit("正在处理，可能存在卡顿，请耐心等待。。。")
        # filepath = QFileInfo(vd).path()
        for vd in vds:
            createpath = QFileInfo(vd).completeBaseName().replace(' ', '').replace('%', '+') + '/'
            if not os.path.exists(QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation) + "/JamPicture/extractfrom" + createpath):
                os.mkdir(QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation) + "/JamPicture/extractfrom" + createpath)
            self.name = QFileInfo(vd).completeBaseName().replace(' ', '').replace('%', '')
            print(self.name)
            self.transforma = subprocess.Popen(
                self.f_path + ' -i "' + vd + '"' + fps + '"' +
                QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation) + "/JamPicture/extractfrom" + createpath + self.name + '-%05d.png"'
                + ' -update  -y',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit(
                "图片提取完成，文件保存于：\n图片/JamPicture/extractfrom" + createpath + self.name + '.png\n点击此处可打开')
            self.parent.statusBar().showMessage(
                "图片提取完成，文件保存于：图片/JamPicture/extractfrom" + createpath + self.name + '.png')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + "/JamPicture/extractfrom" + createpath
        self.reset_style(self.parent.extract_pic_form_vd_pushButton)

    def synthesis_ad_vd(self, mix):
        self.set_style(self.parent.synthesis_ad_vd_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        print(self.f_path + ' -i ' + '"' + mix[0] + '" -i ' + '"' + mix[1] +
              '" -map 0:v -map 1:a -filter_complex " [1:0] apad " -shortest ' +
              QStandardPaths.writableLocation(
                  QStandardPaths.MoviesLocation) + '/jam_video/synthesis' + self.name + '.mp4'
              + ' -y')
        self.transforma = subprocess.Popen(
            self.f_path + ' -i ' + '"' + mix[0] + '" -i ' + '"' + mix[1] +
            '" -map 0:v -map 1:a -filter_complex " [1:0] apad " -shortest ' +
            QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/synthesis' + self.name + '.mp4'
            + ' -y',
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("视频已合成，文件保存于：\n视频/jam_video/synthesis" + self.name + '\n点击此处可打开')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/'
        self.reset_style(self.parent.synthesis_ad_vd_pushButton)

    def rerename(self, bakupfiles):
        self.showm_signal.emit("正在恢复...")
        shutil.copy(bakupfiles, ".")
        if os.path.exists(os.path.split(bakupfiles)[1]):
            with open(os.path.split(bakupfiles)[1], "r", encoding="utf-8")as file:
                line = file.readline()
                while line:
                    try:
                        old, new = line.split("->")
                        old = old.replace("\n", "")
                        new = new.replace("\n", "")
                        print(old, "->", new)
                        if os.path.exists(new):
                            os.rename(new, old)
                        else:
                            print("不存在")
                            self.showm_signal.emit("找不到已经命名的文件!请逆序选择对应的备份文件!".format(os.path.split(new)[1]))
                            break
                        line = file.readline()
                    except:
                        print(sys.exc_info(), 6745)
                        continue
            self.showm_signal.emit("已恢复!")

        else:
            print(sys.exc_info())
            self.showm_signal.emit("恢复出错!请联系作者!")

    def rename(self, files, vd=0):
        self.set_style(self.parent.rename_pushButton)
        backup = self.parent.rename_backup_check_bot.isChecked()
        renamestyle = self.parent.rename_style.currentText()  # 命名类型
        renameform = self.parent.renameform.text()  # 命名内容字符
        renamesort = self.parent.rename_sort.currentText()  # 命名顺序
        rename_sort_reverse = self.parent.rename_sort_reverse.isChecked()  # 是否倒序
        randlen = self.parent.rename_randlen.value()  # 随机字符长度
        randstr = "qwert61ybnm72uio45dfgpas89hjklzxcv3_"

        def get_randstr(n=4):
            s = ''
            for i in range(n):
                s += randstr[random.randint(0, len(randstr) - 1)]
            return s

        new = ''
        index = 999
        addstr = renameform
        if vd:
            renameform = 'to_video%04d'
            renamestyle = "序列"
            renamesort = "文件名称"
            rename_sort_reverse = False
            backup = False
        elif '%' not in renameform:
            if renamestyle == "序列":
                renameform += '%04d'
        if renamestyle == "随机字符" and len(renameform) > 1:
            randstr = renameform
        elif renamestyle == "原名+S":
            if "{" in renameform and "}" in renameform:
                try:
                    index = int(renameform[renameform.index("{") + 1:renameform.index("}")])
                    addstr = str(renameform[:renameform.index("{")])
                except:
                    print(sys.exc_info())
                    self.showm_signal.emit("输入的附加字符串格式有误!已将字符串位置重置为最后")
                    index = 999
        if backup:
            info = QFileInfo(files[0])
            pathbak = open(
                os.path.join(info.path(), str(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())) + ".jambak"), "w",
                encoding="utf-8")
            # filerootpath = QFileInfo(files[0]).path() + '/'
            # if not os.path.exists(filerootpath + 'rename_backup'):
            #     os.mkdir(filerootpath + 'rename_backup')
            # for f in files:
            #     rp, n = os.path.split(f)
            #     print("已复制", f)
            #     self.parent.statusBar().showMessage("正在复制文件{}".format(f))
            #     shutil.copy2(f, rp + '/rename_backup/' + n)
        if renamesort == "文件大小":
            files = sorted(files, key=lambda f: QFileInfo(f).size(), reverse=rename_sort_reverse)
        elif renamesort == "修改时间":
            # print("前", files)
            files = sorted(files, key=lambda f: QFileInfo(f).lastModified(), reverse=rename_sort_reverse)
            # print("后", files)
        elif rename_sort_reverse:
            files = sorted(files, reverse=rename_sort_reverse)
        # sort_names = []
        # rand_names = []
        # modified_names = []
        dir_files = os.listdir(os.path.split(files[0])[0])

        # print("dir_files", dir_files)

        def get_new_rand_name(n):
            name = filepath + str(get_randstr(randlen)) + '.' + filesuffix
            if name in files:
                name = get_new_rand_name(n)
            return name

        def get_sort_name(n):
            def get_sort_dname(name):  # 当存在相同文件未被选择时
                name = os.path.splitext(name)[0] + "_1" + os.path.splitext(name)[1]
                if name in dir_files:
                    name = get_sort_dname(name)
                return name

            name = filepath + str(renameform % n) + '.' + filesuffix
            if name in files:
                tempname = filepath + "temp{}".format(get_randstr(8)) + '.' + filesuffix
                try:
                    os.rename(name, tempname)
                except:
                    print(sys.exc_info(), 6849)
                files[files.index(name)] = tempname
                print("选到重复名称", name, tempname)
            elif name not in rfiles and os.path.split(name)[1] in dir_files:
                print("重复文件未选择", files)
                name = get_sort_dname(name)
            return name

        rfiles = files[:]
        # print("files", files)
        self.parent.statusBar().showMessage("正在重命名...")
        for j, i in enumerate(files):  # 文件扩展名统一小写
            info = QFileInfo(i)
            filepath = info.path() + '/'
            filesuffix = info.suffix()
            basename = info.completeBaseName()
            files[j] = filepath + basename + '.' + filesuffix.lower()
        for j, i in enumerate(files):
            # print(renameform % j)
            info = QFileInfo(i)
            filepath = info.path() + '/'
            filesuffix = info.suffix()
            if renamestyle == "序列":
                new = get_sort_name(j)

            elif renamestyle == "随机字符":
                try:
                    new = get_new_rand_name(randlen)
                except:
                    new = get_new_rand_name(randlen + 2)
                # rand_names.append(new)
            elif renamestyle == "原名+S":
                basename = str(info.completeBaseName())
                new = filepath + basename[:index] + addstr + basename[index:] + "." + filesuffix
            else:
                new = filepath + str(info.lastModified().toString("yyyy-MM-dd hh_mm_ss_ff")) + \
                      str(random.randint(1000, 9999)) + '.' + filesuffix
            print(files[j], "->", new)
            if backup:
                pathbak.write(rfiles[j] + "->" + new + "\n")
            try:
                os.rename(files[j], new)
            except:
                print(sys.exc_info(), "6849")
                self.showm_signal.emit("重命名错误!{}".format(sys.exc_info()))
            files[j] = new
        if backup:
            pathbak.close()
        # print("list", sort_names, rand_names, modified_names)

        if vd:
            self.showm_signal.emit('图片已重命名！正在生成视频...')
            self.parent.statusBar().showMessage("图片已重命名！正在生成视频...")
        else:
            self.showm_signal.emit('重命名完成！点击此处打开文件夹')
            self.parent.statusBar().showMessage("重命名完成！")
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = filepath
        self.reset_style(self.parent.rename_pushButton)

    def pic_to_vd(self, pics):
        self.set_style(self.parent.pic_to_vd_pushButton)
        fps = str(self.parent.pic_to_vd_fps.value())
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        try:
            self.rename(pics, 1)
        except FileExistsError:
            print(sys.exc_info())
            self.showm_signal.emit("视频生成失败:文件重命名失败，请把图片放于一单独文件夹后重试！")
        else:
            info = QFileInfo(pics[0])
            filepath = info.path() + '/'
            filesuffix = info.suffix()
            self.transforma = subprocess.Popen(
                self.f_path + '-threads 4  -r ' + fps + ' -i ' + filepath + 'to_video%04d.' + filesuffix + ' -r ' + fps +
                ' -vcodec libx264 -pix_fmt yuv420p -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" ' +
                QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/generate' + self.name + '.mp4 '
                + ' -y',
                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.transforma.wait()
            if self.stoper:
                self.stoper = False
                self.showm_signal.emit('操作已中止！')
            else:
                self.showm_signal.emit("视频已合成，文件保存于：\n视频/jam_video/generate" + self.name + '\n点击此处打开文件夹')
                self.parent.trayicon.tran_open = True
                self.time = time.time()
                self.open_path = QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/'
        finally:
            self.reset_style(self.parent.pic_to_vd_pushButton)

    def mix_ads(self, ads):
        self.set_style(self.parent.mix_ads_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        filesuffix = QFileInfo(ads[0]).suffix()
        input_file = ' '
        filter_complex = ''
        for j, i in enumerate(ads):
            input_file += '-i "' + i + '" '
            filter_complex += '[{}:a]'.format(j)
        filter_complex += 'amerge=inputs={}[aout]'.format(len(ads))
        print(self.f_path + input_file + '-filter_complex "' + filter_complex + '" -map "[aout]" -ac 2 ' +
              QStandardPaths.writableLocation(
                  QStandardPaths.MusicLocation) + '/jam_audio/extract' + self.name + '.' + filesuffix
              + ' -y')
        self.transforma = subprocess.Popen(
            self.f_path + input_file + '-filter_complex "' + filter_complex + '" -map "[aout]" -ac 2 ' +
            QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/extract' + self.name + '.' + filesuffix
            + ' -y',
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("视频处理完成，文件保存于：\n音乐/jam_audio/extract" + self.name + '\n点击此处可打开')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MusicLocation) + '/jam_audio/'
        self.reset_style(self.parent.mix_ads_pushButton)

    def clear_logo(self, vd):
        self.set_style(self.parent.clear_logo_pushbutton)
        show = str(int(self.parent.clear_logo_test.isChecked()))
        pos = self.parent.clear_logo_pos.text().lower().replace(' ', '')
        if pos == '':
            pos = '20:y=40'
        elif 'x' in pos:
            tup = pos.split('x')
            print(tup)
            if len(tup) == 2 and tup[0].isalnum() and tup[1].isalnum():
                pos = pos.replace('x', ':y=')
            else:
                print('输入错误！')
                self.showm_signal.emit('坐标输入格式错误')
                self.reset_style(self.parent.clear_logo_pushbutton)
                return
        else:
            self.reset_style(self.parent.clear_logo_pushbutton)
            self.showm_signal.emit('坐标格式错误！')
            return
        size = self.parent.clear_logo_size.text().lower().replace(' ', '')

        if size == '':
            size = '200:h=50'
        elif 'x' in size:
            tup = size.split('x')
            print(tup)
            if len(tup) == 2 and tup[0].isalnum() and tup[1].isalnum():
                size = size.replace('x', ':h=')
            else:
                print('输入错误！')
                self.showm_signal.emit('大小输入格式错误')
                self.reset_style(self.parent.clear_logo_pushbutton)
                return

        else:
            self.reset_style(self.parent.clear_logo_pushbutton)
            self.showm_signal.emit('大小格式错误！')
            return
        self.name = QFileInfo(vd).baseName() + str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        print(
            self.f_path + ' -i "' + vd + '" -acodec copy -vf delogo=x=' + pos + ':w=' + size + ':show=' + show + ' "' +
            QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/clear_logo' + self.name + '.mp4" '
            + ' -y')
        self.transforma = subprocess.Popen(
            self.f_path + ' -i "' + vd + '" -acodec copy -vf delogo=x=' + pos + ':w=' + size + ':show=' + show + ' "' +
            QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/clear_logo' + self.name + '.mp4" '
            + ' -y', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("水印已去除，文件保存于：\n视频/jam_video/generate" + self.name + '\n点击此处打开文件夹')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/'
        self.reset_style(self.parent.clear_logo_pushbutton)

    def add_logo(self, vd):
        self.set_style(self.parent.add_logo_pushbutton)
        # show=str(int(self.parent.clear_logo_test.isChecked()))
        # logo=self.add_logo_path
        pos = self.parent.add_logo_pos.text().lower().replace(' ', '')
        if pos == '':
            pos = '20:y=40'
        elif 'x' in pos:
            tup = pos.split('x')
            print(tup)
            if len(tup) == 2 and tup[0].isalnum() and tup[1].isalnum():
                pos = pos.replace('x', ':')
            else:
                print('输入错误！')
                self.showm_signal.emit('坐标输入格式错误')
                self.reset_style(self.parent.add_logo_pushbutton)
                return
        else:
            self.showm_signal.emit('格式错误！')
            self.reset_style(self.parent.add_logo_pushbutton)
            return

        self.name = QFileInfo(vd).baseName() + str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        gs = QFileInfo(self.add_logo_path).suffix()
        if gs != 'gif':
            print(
                self.f_path + ' -i "' + vd + '" -i "' + self.add_logo_path + '" -filter_complex "overlay=' + pos + '"  -acodec copy "' +
                QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/add_logo' + self.name + '.mp4" '
                + ' -y')
            self.transforma = subprocess.Popen(
                self.f_path + ' -i "' + vd + '" -i "' + self.add_logo_path + '" -filter_complex "overlay=' + pos + '"  -acodec copy "' +
                QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/add_logo' + self.name + '.mp4" '
                + ' -y', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.transforma.wait()
        else:
            print(
                self.f_path + ' -i "' + vd + '" -ignore_loop 0 -i "' + self.add_logo_path + '" -filter_complex  "[0:v][1:v]overlay=' + pos + ':shortest=1"  -acodec copy "' +
                QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/add_logo' + self.name + '.mp4" '
                + ' -y')
            self.transforma = subprocess.Popen(
                self.f_path + ' -i "' + vd + '" -ignore_loop 0 -i "' + self.add_logo_path + '" -filter_complex  "[0:v][1:v]overlay=' + pos + ':shortest=1"  -acodec copy "' +
                QStandardPaths.writableLocation(
                    QStandardPaths.MoviesLocation) + '/jam_video/add_logo' + self.name + '.mp4" '
                + ' -y', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.transforma.wait()
        if self.stoper:
            self.stoper = False
            self.showm_signal.emit('操作已中止！')
        else:
            self.showm_signal.emit("水印已去除，文件保存于：\n视频/jam_video/generate" + self.name + '\n点击此处打开文件夹')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.MoviesLocation) + '/jam_video/'
        self.reset_style(self.parent.add_logo_pushbutton)

    def qr_code(self):
        self.set_style(self.parent.t_qr_pushButton)
        self.name = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        version = self.parent.t_qr_version.value()
        if version == 0:
            version = None
        # error=self.parent.t_qr_error.currentText()
        try:
            qr = qrcode.QRCode(
                version=version,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            data = self.parent.t_qr_data.toPlainText()
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + "/JamPicture/qrcode" + self.name + '.png')
        except qrcode.exceptions.DataOverflowError:
            self.showm_signal.emit('数据量过大！')
        except:
            print('生成失败')
            self.showm_signal.emit('未知错误，生成失败！')
        else:
            self.showm_signal.emit("二维码已生成，文件保存于：\n图片/JamPicture/qrcode" + self.name + '.png\n点击此处可打开')
            self.parent.statusBar().showMessage("二维码已生成，文件保存于：图片/JamPicture/qrcode" + self.name + '.png')
            self.parent.trayicon.tran_open = True
            self.time = time.time()
            self.open_path = QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + "/JamPicture/"
            p = QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation) + "/JamPicture/qrcode" + self.name + '.png'
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        finally:
            self.reset_style(self.parent.t_qr_pushButton)

    def reset_style(self, pushbutton):

        pushbutton.setStyleSheet("QPushButton{color:black}"
                                 "QPushButton:hover{color:green}"
                                 "QPushButton:hover{background-color:rgb(200,200,100)}"
                                 "QPushButton{background-color:rgb(239,239,239)}"
                                 "QPushButton{padding:1px 4px }")
        if pushbutton == self.parent.t_pic_pushButton or pushbutton == self.parent.piccut_pushButton \
                or pushbutton == self.parent.picSplicing_pushButton or pushbutton == self.parent.rename_pushButton:
            pass
        else:
            if pushbutton == self.parent.gifzip_pushButton:
                self.gifzip_running = False
            else:
                self.ffmpeg_running = False

    def set_style(self, pushbutton):
        self.showm_signal.emit('开始处理...')
        self.parent.statusBar().showMessage("处理中......")
        if pushbutton == self.parent.t_pic_pushButton or pushbutton == self.parent.piccut_pushButton \
                or pushbutton == self.parent.picSplicing_pushButton or pushbutton == self.parent.rename_pushButton:
            pushbutton.setStyleSheet("QPushButton{color:green}"
                                     "QPushButton:hover{color:lightgreen}"
                                     "QPushButton:hover{background-color:lightyellow}"
                                     "QPushButton{background-color:yellow}"
                                     "QPushButton{padding:1px 4px }")
        else:
            if pushbutton == self.parent.gifzip_pushButton:
                self.gifzip_running = True

            else:
                self.ffmpeg_running = True

            pushbutton.setStyleSheet("QPushButton{color:green}"
                                     "QPushButton:hover{color:lightgreen}"
                                     "QPushButton:hover{background-color:lightred}"
                                     "QPushButton{background-color:red}"
                                     "QPushButton{padding:1px 4px }")

    def stop_transform(self):
        try:
            self.transforma.stdin.write('q'.encode("GBK"))
            self.transforma.communicate()
            self.transforma.kill()
            self.stoper = True
        except ValueError:
            self.showm_signal.emit('没有正在进行的操作！')
        except:
            print(sys.exc_info()[0])


class Settings_save(QThread):
    def __init__(self):
        super(QThread, self).__init__()

    def run(self):
        if jamtools.recview:
            try:
                jamtools.settings.beginGroup('rec_settings')
                jamtools.settings.setValue('mouse_rec', jamtools.mouse_rec.isChecked())
                jamtools.settings.setValue('hide_rec', jamtools.hide_rec.isChecked())
                jamtools.settings.setValue('hardware_rec', jamtools.hardware_rec.isChecked())
                jamtools.settings.endGroup()
                print('rec')
                jamtools.settings.sync()
            except:
                print('saverec')
        if jamtools.ssview:
            try:
                jamtools.settings.beginGroup('screenshot')
                jamtools.settings.setValue('open_png', jamtools.open_png.isChecked())
                jamtools.settings.setValue('save_png', jamtools.save_png.isChecked())
                jamtools.settings.setValue('hide_ss', jamtools.hide_ss.isChecked())
                jamtools.settings.setValue('roll_nfeatures', jamtools.roll_nfeatures.value())
                jamtools.settings.setValue('roll_speed', jamtools.roll_speed.value())
                # jamtools.settings.setValue('fault_rate_ss', jamtools.fault_rate_ss.value())
                jamtools.settings.setValue('copy_type_ss', jamtools.copy_type_ss.currentText())
                jamtools.settings.endGroup()
                # print(jamtools.settings.value('screenshot/save_png', False, type=bool))
            except:
                print(22)
            jamtools.settings.sync()
            print('save')
        # if jamtools.controlling:
        #     try:
        #         jamtools.settings.setValue('can_controll', jamtools.can_controll_box.isChecked())
        #         jamtools.can_controll = jamtools.can_controll_box.isChecked()
        #         Trayicon.control.setChecked(jamtools.can_controll_box.isChecked())
        #     except:
        #         print('error to save cancontrol')


class Chat_Thread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, action, args):
        super(QThread, self).__init__()
        self.action = action
        self.args = args
        self.signal.connect(jamtools.recieve_chat)

    def run(self):
        try:
            mess = self.action(self.args)
            self.signal.emit(mess)
            """由于腾讯的api改为付费了,所以不显示播放声音(作者没钱了qaq),如需使用可以打开注释然后在voice_and_text和txpythonsdk中修改api即可"""
            # if jamtools.settings.value("chater/playvoice", False, type=bool):
            #     Text2voice().get_voice_and_paly_it(mess, voicetype=jamtools.settings.value("chater/voicetype", 101001,
            #                                                                                type=int))
        except:
            print("Unexpected error:", sys.exc_info())
            jamtools.statusBar().showMessage(str(sys.exc_info()[0]))


class ChildUpdateWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent, Qt.WindowCloseButtonHint)
        self.active = True
        self.setWindowTitle("检查更新")
        self.setFixedSize(400, 100)
        self.setWindowModality(Qt.ApplicationModal)
        self.label = QLabel("    正在检查更新", self)
        self.label.setGeometry(20, 10, 360, 60)
        self.giflabel = QLabel(self.label)
        self.giflabel.setGeometry(200, 15, 35, 35)
        self.gif = QMovie(':./load.gif')
        self.gif.setScaledSize(QSize(30, 30))
        self.giflabel.setMovie(self.gif)
        self.gif.start()
        self.canalbtn = QPushButton("取消", self)
        self.canalbtn.clicked.connect(self.canal)
        self.backgroundbtn = QPushButton("后台运行", self)
        self.backgroundbtn.clicked.connect(self.hide)
        self.canalbtn.move(60, self.height() - 30)
        self.backgroundbtn.move(220, self.height() - 30)
        self.pbar = QProgressBar(self.label)
        self.pbar.setMaximum(100)
        self.pbar.setGeometry(70, 12, self.width() - 105, 18)
        self.pbar.hide()
        self.checkforupdateThread = CheckForUpdateThread()
        self.checkforupdateThread.checkresult_signal.connect(self.showresultsignalhandle)
        self.checkforupdateThread.updating_signal.connect(self.downloading)
        self.checkforupdateThread.close_signal.connect(self.canal)
        self.checkforupdateThread.start()
        self.show()

    def downloading(self, text, value):
        self.pbar.show()
        if value == -1:
            self.pbar.setDisabled(True)
            return
        self.pbar.setValue(value)
        self.label.setText(text)

    def showresultsignalhandle(self, res):
        self.pbar.hide()
        self.gif.stop()
        self.giflabel.clear()
        self.giflabel.hide()
        self.label.setText(res)

    def hide(self) -> None:
        super(ChildUpdateWindow, self).hide()

    def closeEvent(self, e) -> None:
        super(ChildUpdateWindow, self).closeEvent(e)
        self.active = False

    def canal(self):
        self.gif.stop()
        self.giflabel.clear()
        self.checkforupdateThread.quit()
        try:
            if os.path.exists(self.checkforupdateThread.newversonname):
                os.remove(self.checkforupdateThread.newversonname)
        except:
            print(sys.exc_info(), 5223)
        self.close()


class CheckForUpdateThread(QThread):
    checkresult_signal = pyqtSignal(str)
    updating_signal = pyqtSignal(str, int)
    close_signal = pyqtSignal()

    def __init__(self):
        super(CheckForUpdateThread, self).__init__()
        self.newversonname = "jam.exe"

    def run(self) -> None:
        try:
            self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientsocket.settimeout(20)
            self.clientsocket.connect(("47.106.169.20", 6941))
            print("连接成功")
            V = self.clientsocket.recv(99999).decode()
            print("最版本{}".format(V))
            if V != VERSON:

                self.checkresult_signal.emit("检测到新版本{},正在准备更新..".format(V))
            else:
                self.checkresult_signal.emit("已是最新版本")
                self.clientsocket.send("up to date".encode())
                return
            self.clientsocket.send("update".encode())
            self.clientsocket.settimeout(None)
        except:
            print(sys.exc_info(), 7383)
            self.checkresult_signal.emit("连接更新服务器失败!请稍后再试..")
            return
        try:
            info = self.clientsocket.recv(9999).decode()
            if info == "404":
                self.checkresult_signal.emit("服务器出错!")
                return
            self.updating_signal.emit("准备下载:", 0)
            info = json.loads(info)
            print(info)
            totalsize = info["size"]
            s = 0
            self.newversonname = info["name"]
            self.clientsocket.send("ready".encode())
            if not os.path.exists(self.newversonname) or os.path.getsize(self.newversonname) != totalsize:
                with open(self.newversonname, "wb")as apk:
                    adump = self.clientsocket.recv(99999)
                    while adump:
                        sig = adump.find("<<|end|>>".encode())
                        s += len(adump)
                        if sig != -1:
                            s -= 9
                        self.updating_signal.emit(
                            "正在下载:\n{:.2f}M/{:.2f}M".format(s / 1024 / 1024, totalsize / 1024 / 1024),
                            int(s / totalsize * 100))
                        if sig == -1:
                            apk.write(adump)
                            adump = self.clientsocket.recv(99999)
                        else:
                            apk.write(adump[:sig])
                            break
                print("接收完成")
                self.checkresult_signal.emit("下载完成,正在准备更新...")
            else:
                self.checkresult_signal.emit("已经存在安装文件,正在启动安装程序...")
        except:
            print(sys.exc_info(), 7430)
            # self.updating_signal.emit("服务器断开!",-1)
            self.checkresult_signal.emit("服务器断开!")
            return
        try:
            if os.path.exists(self.newversonname) and os.path.getsize(self.newversonname) == totalsize:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.newversonname))
                print("start end")
                self.close_signal.emit()
            else:
                self.checkresult_signal.emit("文件校核出错请重新检查更新!")
                if os.path.exists(self.newversonname):
                    os.remove(self.newversonname)
                raise OSError
        except OSError:

            self.checkresult_signal.emit("文件校核出错请重新检查更新!")


class InitThread(QThread):
    def __init__(self, parent=None):
        super(QThread, self).__init__(parent)
        # self.action = action
        # self.args = args

    def run(self):
        # time.sleep()
        jamtools.record_screen_deviceinit()
        # jamtools.record_screen()
        # jamtools.control()
        if sys.argv.__len__() >= 2:
            if os.path.splitext(sys.argv[1].lower())[-1] == '.jam':
                jamtools.start_action_run(sys.argv[1])
                print('start control')
                jamtools.hide()



def main():
    global jamtools, ffmpeg_path, documents_path, temp_path, iconpng, paypng, transformater, \
        transtalater
    start_t = time.time()
    appctxt = ApplicationContext()
    A = QObject()
    serverName = 'jamtoolsserver'
    # QLocalServer.removeServer(serverName)
    ssocket = QLocalSocket(A)
    ssocket.connectToServer(serverName)
    # print("e",  ssocket.errorString(), ssocket.error())
    # refuse:0  invalid name:2 unknown error:-1
    # 如果连接成功，表明server已经存在，当前已有实例在运行
    if ssocket.waitForConnected(500):
        print('connected server')
        ssocket.write(str(sys.argv).encode('utf-8'))
        ssocket.waitForBytesWritten()
        appctxt.app.quit()
        sys.exit()
    else:
        if ssocket.error() == 0:
            QLocalServer.removeServer(serverName)
            print(ssocket.errorString(), ",Remove it")
        print('no server')
        localServer = QLocalServer()  # 没有实例运行，创建服务器
        localServer.listen(serverName)

        def ready_():
            client = localServer.nextPendingConnection()

            def read_():
                data = client.readAll().data().decode('utf-8')
                data = data.replace('[', '').replace(']', '').replace("'", "").replace('"', '').replace(' ', '').split(
                    ',')
                print(data, len(data))
                if len(data) >= 2:
                    print(sys.argv)
                    if os.path.splitext(data[1].lower())[-1] == '.jam':
                        jamtools.start_action_run(data[1])
                        print('start')
                        jamtools.hide()
                else:
                    QSettings('Fandes', 'jamtools').setValue("S_SIMPLE_MODE", False)
                    jamtools.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                    jamtools.show()
                    jamtools.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                    jamtools.show()
                    jamtools.activateWindow()


            client.readyRead.connect(read_)
            print('read server', client.readAll().data())

        localServer.newConnection.connect(ready_)

        ffmpeg_path = os.path.join(apppath, 'bin', PLATFORM_SYS)
        documents_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)

        temp_path = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        os.chdir(temp_path)
        if not os.path.exists("j_temp"):
            os.mkdir("j_temp")
        else:
            if os.path.exists("j_temp/triggerpix.png"):
                os.remove("j_temp/triggerpix.png")
        jamtools = Swindow()
        transtalater = Transtalater(jamtools)  # 翻译
        transformater = Transforma(jamtools)  # 格式转换

        # 初始化录屏线程
        jamtools.init_rec_con_thread = InitThread()
        jamtools.init_rec_con_thread.start()
        jamtools.statusBar().showMessage('初始化用时：%f' % float(time.time() - start_t))
        print('init_swindowtime:', time.time() - start_t)
        sys.exit(appctxt.app.exec_())


if __name__ == '__main__':
    main()
