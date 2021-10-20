import json
import os
import shutil
import sys
import time

import cv2

from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal, QStandardPaths, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QGroupBox
from numpy import asarray
from pynput import keyboard, mouse
from pynput.keyboard import Controller as KeyBoardController, KeyCode
from pynput.mouse import Button, Controller as MouseController

from jampublic import Transparent_windows


def high_precision_delay(delay_time):
    """ Function to provide accurate time delay in millisecond
    """
    _ = time.perf_counter() + delay_time
    while time.perf_counter() < _:
        pass


class ControlTimer():
    def __init__(self):
        self.start_time = time.time()
        self.stime = self.start_time

    def count(self):
        t = time.time()
        dtime = t - self.stime
        # print(dtime)
        self.stime = t
        return dtime


# 键盘动作模板
def keyboard_action_template():
    return {
        "name": "keyboard",
        "event": "default",
        "vk": "default",
        "time": 0.0
    }


# 鼠标动作模板
def mouse_action_template():
    return {
        "name": "mouse",
        "event": "default",
        "target": "default",
        "action": "default",
        "location": {
            "x": "0",
            "y": "0"
        },
        "time": 0.0
    }


# 键盘动作监听
class KeyboardActionListener(QThread):

    def __init__(self, parent=None, file_name='j_temp/keyboard.jam'):
        super().__init__()
        self.parent = parent
        self.file_name = file_name
        self.timer = ControlTimer()

    def run(self):
        with open(self.file_name, 'w', encoding='utf-8') as file:
            # 键盘按下监听
            def on_press(key):
                template = keyboard_action_template()
                template['event'] = 'press'
                template['time'] = self.timer.count()
                try:
                    template['vk'] = key.vk
                except AttributeError:
                    template['vk'] = key.value.vk
                finally:
                    # print(template)
                    file.writelines(json.dumps(template) + "\n")
                    file.flush()

            # 键盘抬起监听
            def on_release(key):

                template = keyboard_action_template()
                template['event'] = 'release'
                template['time'] = self.timer.count()
                try:
                    template['vk'] = key.vk
                except AttributeError:
                    template['vk'] = key.value.vk
                finally:
                    print(template)
                    file.writelines(json.dumps(template) + "\n")
                    file.flush()

            # 键盘监听
            self.keyboardListener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.keyboardListener.start()

            while self.keyboardListener.running:
                if not self.parent.listening:
                    self.keyboardListener.stop()
                    print("keyboard break")
                    break
                time.sleep(0.1)


# 鼠标动作监听
class MouseActionListener(QThread):
    def __init__(self, file_name='j_temp/mouse.jam', controll_roller=120, parent=None):
        super().__init__()
        self.file_name = file_name
        self.parent = parent
        self.controll_roller = controll_roller
        self.timer = ControlTimer()
        # self.mouseListener=None

    def run(self):
        with open(self.file_name, 'w', encoding='utf-8') as file:
            # 鼠标移动事件
            def on_move(x, y):
                template = mouse_action_template()
                template['event'] = 'move'
                template['location']['x'] = x
                template['location']['y'] = y
                template['time'] = self.timer.count()
                file.writelines(json.dumps(template) + "\n")
                file.flush()

            # 鼠标点击事件
            def on_click(x, y, button, pressed):
                template = mouse_action_template()
                template['event'] = 'click'
                template['target'] = button.name
                template['action'] = pressed
                template['location']['x'] = x
                template['location']['y'] = y
                template['time'] = self.timer.count()

                file.writelines(json.dumps(template) + "\n")
                file.flush()

            # 鼠标滚动事件
            def on_scroll(x, y, x_axis, y_axis):
                template = mouse_action_template()
                template['event'] = 'scroll'
                template['location']['x'] = x_axis * self.controll_roller
                template['location']['y'] = y_axis * self.controll_roller
                template['time'] = self.timer.count()
                file.writelines(json.dumps(template) + "\n")
                file.flush()

            self.mouseListener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
            self.mouseListener.start()
            while self.mouseListener.running:
                if not self.parent.listening:
                    self.mouseListener.stop()
                    print("mouse break")
                    break
                time.sleep(0.1)


# 键盘动作执行
class KeyboardActionExecute(QThread):
    end_run_a_round_signal = pyqtSignal()

    def __init__(self, parent=None, file_name='j_temp/keyboard0.jam', speed=1.0):
        super().__init__()
        self.file_name = file_name
        self.stoper = False
        # self.stoper = False
        self.speed = speed
        self.parent = parent

    def listening_sleep(self, t):
        count = int(t / 0.1)
        for i in range(count):
            time.sleep(0.1)
            if self.stoper:
                break

    def run(self):
        if not os.path.exists(self.file_name):
            os.mkdir(self.file_name)
        with open(self.file_name, 'r', encoding='utf-8') as file:
            keyboard_exec = KeyBoardController()
            line = file.readline()
            # if not line:
            #     print('no key')
            #     return
            while line:
                if len(line) == 1:
                    line = file.readline()
                    continue
                obj = json.loads(line)
                # print(obj)
                if obj['name'] == 'keyboard':
                    delay = obj['time'] / self.speed
                    if delay > 1:
                        self.listening_sleep(delay)
                    else:
                        time.sleep(delay)

                    if obj['event'] == 'press':

                        keyboard_exec.press(KeyCode.from_vk(obj['vk']))

                    elif obj['event'] == 'release':

                        keyboard_exec.release(KeyCode.from_vk(obj['vk']))
                if self.stoper:
                    print('keystoper')
                    # self.stoper = False
                    break
                line = file.readline()
            keyboard_exec.release(keyboard.Key.ctrl)
            keyboard_exec.release(keyboard.Key.shift)
            keyboard_exec.release(keyboard.Key.alt)

        while self.parent.mouseActionrunner.isRunning():
            time.sleep(0.1)
            # print('waiting mouse stop')
        print('动作播放完一次')
        if not self.stoper:
            self.end_run_a_round_signal.emit()


# 鼠标动作执行
class MouseActionExecute(QThread):
    def __init__(self, parent=None, file_name='j_temp/mouse0.jam', speed=1):
        super().__init__()
        self.file_name = file_name
        self.stoper = False
        # self.stoper = False
        self.speed = speed
        self.parent = parent

    def listening_sleep(self, t):
        count = int(t / 0.1)
        for i in range(count):
            time.sleep(0.1)
            if self.stoper:
                print("stop sleep")
                break

    def run(self):
        if not os.path.exists(self.file_name):
            os.mkdir(self.file_name)
        with open(self.file_name, 'r', encoding='utf-8') as file:
            mouse_exec = MouseController()
            line = file.readline()
            # if not line:
            #     print('no mouse')
            #     return
            while line:
                obj = json.loads(line)
                # print(obj)
                if obj['name'] == 'mouse':
                    delay = obj['time'] / self.speed
                    if delay < 0.1:
                        high_precision_delay(delay)
                    elif 1 > delay > 0.1:
                        time.sleep(delay)
                    else:
                        self.listening_sleep(delay)

                    if obj['event'] == 'move':
                        mouse_exec.position = (obj['location']['x'], obj['location']['y'])
                        # print(1)
                    elif obj['event'] == 'click':
                        if obj['action']:
                            # time.sleep(obj['time'])
                            if obj['target'] == 'left':
                                mouse_exec.press(Button.left)
                            else:
                                mouse_exec.press(Button.right)
                        else:
                            if obj['target'] == 'left':
                                mouse_exec.release(Button.left)
                            else:
                                mouse_exec.release(Button.right)
                    elif obj['event'] == 'scroll':
                        # time.sleep(obj['time'])
                        mouse_exec.scroll(20, obj['location']['y'])
                    if self.stoper:
                        print('鼠标stoper')
                        self.stoper = False
                        break
                line = file.readline()


class ActionController(QObject):
    record_wait_tc_signal = pyqtSignal(float)
    run_wait_tc_signal = pyqtSignal(float)  # 等待时间改变信号
    return_samrate_signal = pyqtSignal(list)
    showm_signal = pyqtSignal(str)  # 通知信号
    showrect_signal = pyqtSignal(bool)
    controlrun_bot_stylesheet_signal = pyqtSignal(str)
    controlrecord_bot_stylesheet_signal = pyqtSignal(str)
    updata_control_list_signal = pyqtSignal()

    def __init__(self, id=0):
        super(ActionController, self).__init__()
        self.id = id
        self.listening = False
        self.running = False
        self.stop_wait = False
        self.waiting = False
        self.execute_count = 1
        self.delay = 0
        self.speed = 1
        self.comparison_info = None
        documentpath = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        self.open_path = documentpath + '/jam_control/current.jam'
        if not os.path.exists(documentpath + '/jam_control'):
            os.mkdir(documentpath + '/jam_control')

    def controlerlisten_start(self, delay=0, controll_roller=120):
        self.listening = True
        if delay > 0:
            self.controlrecord_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(180,180,50)}")
            print("开始等待")

            self.ListenerWaiterThread = DelayWaitingThread(self, isListening=True, delay=delay,
                                                           arges=(controll_roller,))
            self.ListenerWaiterThread.allow_signal.connect(self.controlerlisten_start_func)
            self.ListenerWaiterThread.start()
        else:
            self.controlerlisten_start_func(arges=(controll_roller,))

    def controlerlisten_start_func(self, arges: tuple):
        controll_roller = arges[0]
        self.showm_signal.emit('开始录制动作')
        self.controlrecord_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(255,50,50)}")
        print('开始监听')
        self.mouseActionListener = MouseActionListener(controll_roller=controll_roller, parent=self)
        self.keboardrelistener = KeyboardActionListener(parent=self)
        self.mouseActionListener.start()
        self.keboardrelistener.start()

    def controlerlisten_stop(self):
        self.listening = False
        print('结束监听')
        self.showm_signal.emit('结束录制，动作已保存！于系统文档/jam_control目录下，可播放或分享使用')
        print("aaa")

        try:
            time.sleep(0.2)
            del self.mouseActionListener.mouseListener
            del self.keboardrelistener.keyboardListener
            # self.mouseActionListener.mouseListener.stop()
            # self.keboardrelistener.keyboardListener.stop()
        except:
            print(sys.exc_info(),362)
        print("stop")
        self.mouseActionListener.quit()
        self.keboardrelistener.quit()
        print("退出00")
        self.mouseActionListener.wait(1)
        print("退出11")
        self.keboardrelistener.wait(1)
        st = time.process_time()
        print("已退出")
        if not os.path.exists(QStandardPaths.writableLocation(
                QStandardPaths.DocumentsLocation) + '/jam_control/'):
            os.mkdir(QStandardPaths.writableLocation(
                QStandardPaths.DocumentsLocation) + '/jam_control/')
        with open(QStandardPaths.writableLocation(
                QStandardPaths.DocumentsLocation) + '/jam_control/current.jam', 'w', encoding='utf-8')as file:
            jamfile = {'keyboardjam': '', 'mousejam': ''}
            with open('j_temp/keyboard.jam', 'r')as keyboardjam:
                keyboardjamstrlist = keyboardjam.readlines()
                if self.isNoFormatStartEnd(keyboardjamstrlist[:2]):
                    keyboardjamstrlist = keyboardjamstrlist[2:]
                if self.isNoFormatStartEnd(keyboardjamstrlist[-2:]):
                    keyboardjamstrlist = keyboardjamstrlist[:-2]
                print(keyboardjamstrlist)
                jamfile['keyboardjam'] = "".join(keyboardjamstrlist)
            with open('j_temp/mouse.jam', 'r')as mousejam:
                jamfile['mousejam'] = mousejam.read()
            file.write(json.dumps(jamfile, indent=4))
            file.flush()
        ntime = str(time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))
        shutil.copy2(QStandardPaths.writableLocation(
            QStandardPaths.DocumentsLocation) + '/jam_control/current.jam', QStandardPaths.writableLocation(
            QStandardPaths.DocumentsLocation) + '/jam_control/{}.jam'.format(ntime))
        print('setjamdone', time.process_time() - st)

    def isNoFormatStartEnd(self, d: list):
        i = 0
        for line in d:
            kc = json.loads(line)["vk"]
            if kc == 49:
                i += 1
            elif kc == 164:
                i += 2
        if i == 3:
            return True
        return False

    def listening_change(self, delay=0, controll_roller=120):
        if self.waiting and not self.stop_wait and not self.running:
            self.stop_wait = True
        else:
            if self.running:
                print("正在播放动作，不能录制！")
                self.showm_signal.emit('正在播放动作，不能录制！')
                return
            if self.listening:
                self.controlerlisten_stop()
                self.controlrecord_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(239,239,239);}")
                self.updata_control_list_signal.emit()
            elif not self.listening:
                self.controlerlisten_start(delay, controll_roller)

    def controlerrun_start(self, delay=0, execute_count=1,
                           speed=1,
                           path=QStandardPaths.writableLocation(
                               QStandardPaths.DocumentsLocation) + '/jam_control/current.jam'):

        self.execute_count = execute_count
        self.delay = delay
        self.speed = speed
        self.running = True
        with open(path, 'r', encoding='utf-8')as file:
            obj = json.loads(file.read())
            with open('j_temp/mouse{}.jam'.format(self.id), 'w')as mou:
                mou.write(obj['mousejam'])
            with open('j_temp/keyboard{}.jam'.format(self.id), 'w')as key:
                key.write(obj['keyboardjam'])

        self.controlerrun_start_handle()

    def controlerrun_start_handle(self):  # 开始条件判断
        delay = self.delay
        speed = self.speed
        if self.execute_count <= 0:
            print("动作播放结束!")
            self.showm_signal.emit("动作播放结束!")
            self.running = False
            self.controlrun_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(239,239,239);}")
            return
        if self.comparison_info["areas"][0][2:] != (0, 0):  # 宽高不为零
            print("开始比对")
            # self.showm_signal.emit("开始比对图像...")
            self.controlrun_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(180,180,50)}")
            self.showrect_signal.emit(True)
            areas, pix, same_rate, interval = self.comparison_info.values()
            self.comparison_Thread = ControllTrigger(self, areas=areas, pixpaths=pix, same_rate=same_rate,
                                                     args=(speed,))
            self.comparison_Thread.allow_signal.connect(self.controlerrun_start_func)
            self.comparison_Thread.start()
        elif delay > 0:
            self.controlrun_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(180,180,50)}")
            self.RunnerWaiterThread = DelayWaitingThread(self, isListening=False, delay=delay,
                                                         arges=(speed,))
            self.RunnerWaiterThread.allow_signal.connect(self.controlerrun_start_func)
            self.RunnerWaiterThread.start()

        else:
            self.controlerrun_start_func((speed,))
        self.execute_count -= 1

    def controlerrun_start_func(self, arges):  # 开始播放
        self.showrect_signal.emit(False)
        self.controlrun_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(255,50,50)}")
        speed = arges[0]
        self.mouseActionrunner = MouseActionExecute(parent=self, file_name='j_temp/mouse{}.jam'.format(self.id),
                                                    speed=speed)
        self.keyboardrunner = KeyboardActionExecute(parent=self, file_name='j_temp/keyboard{}.jam'.format(self.id),
                                                    speed=speed)
        self.keyboardrunner.end_run_a_round_signal.connect(self.controlerrun_start_handle)
        self.mouseActionrunner.start()
        self.keyboardrunner.start()
        print('开始播放')
        self.showm_signal.emit('开始播放动作')
        # try:
        #     jamtools.controlrun.setStyleSheet(
        #         "QPushButton{background-color:rgb(239,50,50);}")
        # except:
        #     pass

    def controlerrun_stop(self):
        print("动作播放中止")
        self.showrect_signal.emit(False)
        self.showm_signal.emit('动作播放中止！')
        self.running = False
        try:
            if self.mouseActionrunner.isRunning():
                self.mouseActionrunner.stoper = True
                # self.mouseActionrunner.stoper = True
                self.mouseActionrunner.wait()
            if self.keyboardrunner.isRunning():
                self.keyboardrunner.stoper = True
                # self.keyboardrunner.stoper = True
                self.keyboardrunner.wait()
        except:
            print("出错l576", sys.exc_info())
        self.controlrun_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(239,239,239);}")

    def running_change(self, delay=0, execute_count=1, speed=1,
                       comparison_info: dict = None,
                       path=QStandardPaths.writableLocation(
                           QStandardPaths.DocumentsLocation) + '/jam_control/current.jam'):
        if comparison_info is None:
            comparison_info = {"areas": [(0, 0, 0, 0), ], "pixs": ["j_temp/triggerpix00.png", ], "sampling_same": 0.9,
                               "dtime": 500}
        self.comparison_info = comparison_info
        print('runningchanged', self.waiting and not self.stop_wait and not self.listening)
        if self.waiting and not self.stop_wait and not self.listening:
            print("中止等待")
            self.stop_wait = True
            self.showrect_signal.emit(False)
            self.showm_signal.emit("中止等待!")
        else:
            if self.listening:
                print('正在录制动作，不能播放！')
                self.showm_signal.emit('正在录制动作，不能播放！')
                return
            if self.running:
                print("播放中停止")
                self.controlerrun_stop()
            elif not self.running:
                def on_press(key):
                    if key == keyboard.Key.f4:
                        self.controlerrun_stop()
                        self.runnerstopper.stop()
                self.runnerstopper = keyboard.Listener(on_press=on_press)
                self.runnerstopper.start()
                if os.path.exists(path):
                    self.controlerrun_start(delay=delay, path=path,
                                            execute_count=execute_count, speed=speed)
                else:
                    self.controlerrun_start(delay=delay, execute_count=execute_count,
                                            speed=speed,
                                            path=QStandardPaths.writableLocation(
                                                QStandardPaths.DocumentsLocation) + '/jam_control/current.jam')


class ControllTrigger(QThread):
    allow_signal = pyqtSignal(tuple)

    def __init__(self, parent: ActionController = None, areas=((0, 0, 0, 0),), pixpaths=("j_temp/triggerpix00.png",),
                 interval=500,
                 same_rate=0.9, args: tuple = ()):
        super(ControllTrigger, self).__init__()
        self.interval = interval / 1000
        self.parent = parent
        self.areas = areas
        self.screen = QApplication.primaryScreen()
        self.comparing = True
        self.samplingpix = [cv2.imread(pix) for pix in pixpaths]
        self.same_rate = same_rate
        self.args = args

    def run(self) -> None:
        self.parent.waiting = True
        self.parent.showm_signal.emit('正在识别画面内容...')
        print('正在识别画面内容')

        while self.comparing and not self.parent.stop_wait:
            judge_rates = []
            for area, sam_pix in zip(self.areas, self.samplingpix):
                pix = self.screen.grabWindow(QApplication.desktop().winId(), area[0], area[1], area[2], area[3])
                newimg = Image.fromqpixmap(pix)
                img = cv2.cvtColor(asarray(newimg), cv2.COLOR_RGB2BGR)
                sam, samrate = self.is_same(img, sam_pix)
                judge_rates.append(samrate)
                if sam:
                    self.allow_signal.emit(self.args)
                    print('is same')
                    self.comparing = False
                    break
            if len(judge_rates) == len(self.areas):
                self.parent.return_samrate_signal.emit(judge_rates)
            time.sleep(self.interval)
        print("结束识别")
        self.parent.controlrun_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(239,239,239);}")

        self.parent.waiting = False
        self.parent.stop_wait = False
        self.parent.running = False

    def is_same(self, image1, image2, size=(256, 256)):
        # 将图像resize后，分离为RGB三个通道，再计算每个通道的相似值
        image1 = cv2.resize(image1, size)
        image2 = cv2.resize(image2, size)
        sub_image1 = cv2.split(image1)
        sub_image2 = cv2.split(image2)
        sub_data = 0
        for im1, im2 in zip(sub_image1, sub_image2):
            sub_data += self.calculate(im1, im2)
        sub_data = sub_data / 3
        # print(sub_data)
        # self.same_rate = sub_data
        # self.parent.sampling_label.setText(
        #     '已取样!\npos:({0},{1})\nsize:({2},{3})\n当前相似度:{4}'.format(self.area[0], self.area[1],
        #                                                             self.area[2], self.area[3], sub_data[0]))
        if sub_data >= self.same_rate:
            return 1, sub_data
        else:
            return 0, sub_data

    # 计算单通道的直方图的相似值
    def calculate(self, image1, image2):
        hist1 = cv2.calcHist([image1], [0], None, [256], [0.0, 255.0])
        hist2 = cv2.calcHist([image2], [0], None, [256], [0.0, 255.0])
        # 计算直方图的重合度
        degree = 0
        for i in range(len(hist1)):
            if hist1[i] != hist2[i]:
                degree = degree + (1 - abs(hist1[i] - hist2[i]) / max(hist1[i], hist2[i]))
            else:
                degree = degree + 1
        degree = degree / len(hist1)
        return degree


class DelayWaitingThread(QThread):
    allow_signal = pyqtSignal(tuple)

    def __init__(self, parent: ActionController = None, isListening=True, delay=0, arges=()):
        super(DelayWaitingThread, self).__init__()
        self.parent = parent
        self.isListening = isListening
        self.delay = delay
        self.arges = arges

    def run(self) -> None:
        self.parent.waiting = True
        self.parent.showm_signal.emit("倒计时{}秒".format(self.delay))
        while self.delay > 0 and not self.parent.stop_wait:
            # QApplication.processEvents()
            time.sleep(0.1)
            self.delay -= 0.1
            if self.isListening:
                self.parent.record_wait_tc_signal.emit(self.delay)
            else:
                self.parent.run_wait_tc_signal.emit(self.delay)
        self.parent.waiting = False
        if not self.parent.stop_wait:
            self.allow_signal.emit(self.arges)
        else:
            if self.isListening:
                self.parent.controlrecord_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(239,239,239);}")
                self.parent.stop_wait = False
                self.parent.listening = False
            else:
                self.parent.controlrun_bot_stylesheet_signal.emit("QPushButton{background-color:rgb(239,239,239);}")
                self.parent.stop_wait = False
                self.parent.running = False
            self.parent.showm_signal.emit('退出倒计时！')
            print("退出倒计时")

            QApplication.processEvents()
            return


class ActionCondition(QGroupBox):
    showm_signal = pyqtSignal(str)
    clicked_signal = pyqtSignal(int)

    def __init__(self, parent=None, id=0):
        super(ActionCondition, self).__init__(parent=parent)

        def showpix():
            try:
                if os.path.exists("j_temp\\triggerpix0{}.png".format(self.id)):
                    os.startfile("j_temp\\triggerpix0{}.png".format(self.id))
                else:
                    print("查看失败,没有样本!请先取样")
                    self.showm_signal.emit('查看失败,请重新取样!')
            except:
                print("查看失败,请重新取样!", sys.exc_info())
                self.showm_signal.emit('查看失败,请重新取样!')

        self.parent = parent
        self.canshowrect = True
        h = 110
        self.id = id
        self.setTitle("条件{}".format(id))
        self.setGeometry(5, 10 + id * (h + 20), self.parent.width() - 10, h)

        self.sampling_bot = QPushButton("取样", self)
        self.sampling_bot.setToolTip('从截屏中取样,区域应尽量具有特征性')
        self.sampling_bot.setGeometry(5, 18, 40, 20)
        self.sampling_bot.clicked.connect(self.sampling_click)
        # self.sampling_bot.clicked.emit(self.)
        self.see_samps_bot = QPushButton("查看", self)
        self.see_samps_bot.setToolTip('查看取样文件')
        self.see_samps_bot.clicked.connect(showpix)
        self.see_samps_bot.setGeometry(self.sampling_bot.x() + self.sampling_bot.width() + 5, 18, 40, 20)
        self.detal_label = QLabel(self)
        self.detal_label.setText("无条件")
        self.detal_label.setGeometry(5, self.see_samps_bot.height() + self.see_samps_bot.y() + 2, self.width() - 40,
                                     self.height() - (self.see_samps_bot.height() + self.see_samps_bot.y() + 5))
        self.area = (0, 0, 0, 0)
        self.pix = None
        self.show()

    def sampling_update(self, area, pixpath):
        self.pix = pixpath
        self.area = area
        self.detal_label.setText('已取样!\npos&size{}'.format(area))
        self.showrect = Transparent_windows(area[0], area[1], area[2], area[3], havelabel=True)
        self.showrect.hide()

    def update_samerate(self, rate):
        self.detal_label.setText('已取样!\npos&size:{}\n相似度:{}'.format(self.area, rate))
        self.showrect.label.setText("[{:.3f}]".format(float(rate)))

    def sampling_click(self):
        self.clicked_signal.emit(self.id)

    def showrectornot(self, t):
        try:
            if t and self.area != (0, 0, 0, 0) and self.canshowrect:
                self.showrect.show()
            else:
                self.showrect.hide()
        except:
            print(sys.exc_info())


class Mainwin(QMainWindow):
    def __init__(self):
        super(Mainwin, self).__init__()
        self.resize(600, 400)

        self.startbot = QPushButton("播放", self)
        self.startbot.move(10, 10)
        self.startbot.clicked.connect(self.changeActionRun)
        self.recbot = QPushButton("录制", self)
        self.recbot.move(10, 50)
        self.recbot.clicked.connect(self.changeActionListen)

        self.actioncotroller = ActionController()

    def changeActionListen(self):
        self.actioncotroller.listening_change(delay=0)

    def changeActionRun(self):
        self.actioncotroller.running_change(delay=0, execute_count=5, speed=1,
                                            comparison_info=(
                                                ((0, 0, 0, 0),), ("j_temp/triggerpix00.png",), 0.35, 500))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    m = Mainwin()
    m.show()
    sys.exit(app.exec_())
