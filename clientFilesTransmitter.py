import gc
import json
import os
import random
import socket
import sys
import time

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QStandardPaths, QSettings, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtNetwork import QNetworkInterface
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QLineEdit, \
    QMessageBox, QFileDialog, QGroupBox, QCheckBox, QSpinBox, QScrollArea, QWidget, QProgressBar
import jamresourse
from jampublic import Commen_Thread


def getdirsize(dir):
    size = 0
    for root, dirs, files in os.walk(dir):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    return size


def create_all_dirs(pathinfo, rootpath='.'):
    try:
        if not os.path.exists(rootpath):
            os.mkdir(rootpath)
        for info in pathinfo:
            d = os.path.join(rootpath, os.path.split(info)[0])
            if not os.path.exists(d):
                os.makedirs(d)
    except:
        print(sys.exc_info(), 33)
    print("已创建完文件夹!")


def fomatpath(p):
    while p[0] == "/" or p[0] == "\\":
        p = p[1:]
    return p


def get_directory_info(rootpath):
    infos = tuple(os.walk(rootpath))
    # print(infos)
    filesizedict = {}
    fileslist = []
    rootpathname = os.path.split(infos[0][0])[0]
    for d0 in infos:
        for name in d0[2]:
            fp = os.path.join(d0[0], name)
            fileslist.append(fp)
            filesizedict[fomatpath(fp.replace(rootpathname, ''))] = os.path.getsize(fp)
    size = sum(filesizedict.values())
    # returninfo = filesizedict.keys()
    # returninfo = [(fomatpath(i.replace(rootpathname, '')), j, k) for i, j, k in infos]  # 发送出去的文件名列表
    # fileslist = [os.path.join(d0[0], name) for d0 in infos for name in d0[2]]  # 在本地遍历的文件名列表
    # size = sum([os.path.getsize(name) for name in fileslist])
    return fileslist, size, filesizedict


def get_ips():  # 获取ip
    dv = QNetworkInterface.allInterfaces()
    print([interface.addressEntries()[i].ip().toString() for interface
           in dv for i in range(len(interface.addressEntries())) if
           (len(interface.addressEntries()) and not interface.addressEntries()[
               i].ip().isLinkLocal() and interface.addressEntries()[
                i].ip().toString() != "127.0.0.1") and ":" not in interface.addressEntries()[
               i].ip().toString() and "." in interface.addressEntries()[
               i].ip().toString()])
    ips = [interface.addressEntries()[i].ip().toString() for interface
           in dv for i in range(len(interface.addressEntries())) if
           (len(interface.addressEntries()) and not interface.addressEntries()[
               i].ip().isLinkLocal() and interface.addressEntries()[
                i].ip().toString() != "127.0.0.1") and ":" not in interface.addressEntries()[
               i].ip().toString() and "." in interface.addressEntries()[
               i].ip().toString()]
    print("all ips", ips)
    return ips


# 128-191是b类
def get_Network_segments(ips):
    segment = []
    end = []
    for ip in ips:
        if 128 < int(ip[:3]) < 191:
            segment.append("".join([ip.split('.')[0], "."]))
            end.append("".join([ip.split('.')[-3], ".", ip.split('.')[-2], ".", ip.split('.')[-1]]))
        else:
            segment.append("".join(str(s) + "." for s in ip.split('.')[:-1]))
            end.append("".join(ip.split('.')[-1:]))
    print(segment, end)
    return segment, end


# def get_all_networks_nameandip():
#     """ 多网卡 mac 和 ip 信息 """
#     dic = psutil.net_if_addrs()
#     print(dic)
#     networks = {}
#     for adapter in dic:
#         snicList = dic[adapter]
#         ipv4 = '无 ipv4 地址'
#         for snic in snicList:
#             if snic.family.name == 'AF_INET':
#                 ipv4 = snic.address
#         networks[adapter] = ipv4
#     print(networks)
#     return networks


class ClientFilesTransmitterGroupbox(QGroupBox):
    showm_signal = pyqtSignal(str)

    def __init__(self, text="", parent=None):
        super(ClientFilesTransmitterGroupbox, self).__init__(title=text, parent=parent)
        self.Transmitter = ClientFilesTransmitter(self)
        # self.setAcceptDrops(True)
        self.resize(560, 220)
        self.allowCheckBox = QCheckBox("允许连接", self)
        self.allowCheckBox.setToolTip("只有当该框勾选时才允许新的连接")
        self.allowCheckBox.setGeometry(10, 18, 90, 25)
        self.allowCheckBox.stateChanged.connect(self.allowconnectchange)
        self.allowCheckBox.setChecked(
            QSettings('Fandes', 'jamtools').value("clientfilestransmittertest/allowconnect", True, type=bool))
        self.needallowconnection = QCheckBox("需要确认", self)
        self.needallowconnection.setToolTip("不勾选则,自动确认所有连接请求")
        self.needallowconnection.setGeometry(self.allowCheckBox.x() + self.allowCheckBox.width() + 12,
                                             self.allowCheckBox.y(),
                                             self.allowCheckBox.width() + 10, self.allowCheckBox.height())
        self.needallowconnection.setChecked(
            QSettings('Fandes', 'jamtools').value("clientfilestransmittertest/needallow", True, type=bool))
        self.needallowconnection.stateChanged.connect(self.autoAllowchange)
        self.disconnectallbtn = QPushButton("关闭所有连接", self)
        self.disconnectallbtn.setToolTip("关闭所有连接,并禁止新的连接,需重新勾选允许连接才可用")
        self.disconnectallbtn.move(self.allowCheckBox.x(),
                                   self.allowCheckBox.height() + self.allowCheckBox.y() + 10)
        self.disconnectallbtn.clicked.connect(self.killallconnection)
        self.connectionstredit = QLineEdit(self.Transmitter.connectstr, self)
        self.connectionstredit.setReadOnly(True)
        self.connectionstredit.setToolTip("连接码")
        self.connectionstredit.setGeometry(self.disconnectallbtn.x(),
                                           self.disconnectallbtn.height() + self.disconnectallbtn.y() + 10, 120, 22)
        self.connectionstrupdate = QPushButton(QIcon(":/update.png"), "", self)
        self.connectionstrupdate.setGeometry(self.connectionstredit.x() + self.connectionstredit.width() + 3,
                                             self.connectionstredit.y(), 22, 22)
        self.connectionstrupdate.clicked.connect(self.Transmitter.update_connectionstr)
        self.connectionstrupdate.setToolTip("更新连接码")
        self.connectionstrupdate.setStatusTip("更新连接码")
        copyconnectionstrbtn = QPushButton("", self)
        copyconnectionstrbtn.setGeometry(self.connectionstrupdate.x() + self.connectionstrupdate.width() + 3,
                                         self.connectionstrupdate.y(), 22, 22)
        copyconnectionstrbtn.setIcon(QIcon(":/copy.png"))
        copyconnectionstrbtn.setToolTip("复制连接码")
        copyconnectionstrbtn.clicked.connect(self.copyconnectionstr)

        self.targetconnectionedit = QLineEdit(self)
        self.targetconnectionedit.setPlaceholderText("连接码")
        self.targetconnectionedit.setGeometry(self.connectionstredit.x(), copyconnectionstrbtn.y() + 35,
                                              self.connectionstredit.width(), self.connectionstredit.height())
        findserverbtn = QPushButton("连接", self)
        findserverbtn.setGeometry(self.targetconnectionedit.x() + self.targetconnectionedit.width() + 5,
                                  self.targetconnectionedit.y(), 65, 22)
        findserverbtn.clicked.connect(lambda: self.Transmitter.findandconnectserver(self.targetconnectionedit.text()))
        findserverbtn.setToolTip("输入连接码以连接")

        connection_ScrollArea = QScrollArea(self)
        connection_ScrollArea.setGeometry(250, 8, self.width() - 150, self.height() - 10)
        self.connection_ScrollArea_widget = QWidget()
        self.connection_ScrollArea_widget.setGeometry(connection_ScrollArea.geometry())
        connection_ScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        connection_ScrollArea.setWidget(self.connection_ScrollArea_widget)
        self.labeltest = QLabel("当前无连接,\n请输入连接码创建连接", self.connection_ScrollArea_widget)
        self.labeltest.setGeometry(10, 30, 150, 50)
        connection_ScrollArea.setStyleSheet("border: 1px solid black;")
        self.setStyleSheet("QScrollBar{width: 5px;}")
        self.connectionwidgetslist = []
        self.autoallow = not self.needallowconnection.isChecked()
        self.connectall()

    def copyconnectionstr(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.Transmitter.connectstr)

    def connectall(self):
        self.Transmitter.aconnectionsignal.connect(self.aconnectionsignalhandle)
        self.Transmitter.reconnectionsignal.connect(self.reconnectionhandle)
        self.Transmitter.foundserverMSGsignal.connect(self.foundserverMSGsignalhandle)
        self.Transmitter.update_connectionstrchangesignal.connect(self.connectionstredit.setText)
        self.Transmitter.show_warningsignal.connect(self.show_a_message)
        self.Transmitter.showm_signal.connect(self.showm_signal.emit)

    def foundserverMSGsignalhandle(self, foundresult: str):
        if foundresult == "notfound":
            QMessageBox.warning(self, "notfound!", "没有找到对方的设备，请检测对方是否允许连接、核对连接码并确保你们的设备处于同一网段!", QMessageBox.Yes)
        elif foundresult == "outofdate":
            QMessageBox.warning(self, "out of date!", "你的连接码已经过期了,请获取最新的连接码!", QMessageBox.Yes)
        else:
            infoBox = QMessageBox()
            infoBox.setIcon(QMessageBox.Information)
            infoBox.setText("{}在线\n正在等待对方确认连接...".format(foundresult))
            infoBox.setStandardButtons(QMessageBox.Ok)
            infoBox.button(QMessageBox.Ok).animateClick(3000)  # 3秒自动关闭
            infoBox.exec_()
            # self.add_a_connection_widget(foundresult)

    def reconnectionhandle(self, client_socket: socket.socket, client_address, fail=False):
        if fail:
            self.reconnectFail(client_address)
            return
        self.create_a_connection(client_socket, client_address)
        self.showm_signal.emit("{}已连接!".format(client_address))
        self.show_a_message("{}已连接!".format(client_address))

    def aconnectionsignalhandle(self, client_socket: socket.socket, client_address, connectport):
        if self.autoallow:
            client_socket.send("allow".encode())
            self.create_a_connection(client_socket, client_address, connectport)
            self.showm_signal.emit("{}已连接!".format(client_address))
            self.show_a_message("{}已连接!".format(client_address))
            return
        self.activateWindow()
        result = QMessageBox.warning(self, "允许连接?", "收到来自{}的一个连接请求\n是否允许连接?".format(client_address),
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if result == QMessageBox.Yes:
            client_socket.send("allow".encode())
            self.create_a_connection(client_socket, client_address, connectport)
        else:
            client_socket.send("refuse".encode())
            client_socket.close()

    def show_a_message(self, message, delay=3000):
        self.activateWindow()
        infoBox = QMessageBox(self)
        infoBox.setIcon(QMessageBox.Information)
        infoBox.setText(message)
        infoBox.setStandardButtons(QMessageBox.Ok)
        infoBox.button(QMessageBox.Ok).animateClick(delay)  # 3秒自动关闭
        infoBox.exec_()

    def create_a_connection(self, client_socket, client_address, connectport=0):
        for aconnectionbox in self.connectionwidgetslist:
            if aconnectionbox.ip == client_address:
                aconnectionbox.update_state("已重新连接")
                print("再次连接")
                break
        else:
            self.labeltest.hide()
            if connectport:
                self.Transmitter.targetdict[client_address] = connectport
            aconnectionbox = ClientConnectionbox(client_address, self.connection_ScrollArea_widget)
            aconnectionbox.move(5, 10 + (aconnectionbox.height() + 5) * len(self.connectionwidgetslist))
            aconnectionbox.show()

        th = ClientListenThread(client_socket, self.Transmitter, client_address)
        aconnectionbox.sendfilessignal.connect(th.sendfiles)
        aconnectionbox.senddirssignal.connect(th.senddirs)
        aconnectionbox.resetsignal.connect(self.reset)
        aconnectionbox.rootpathchangesignal.connect(th.rootpathchange)
        aconnectionbox.threadnum.valueChanged.connect(th.changethreadnum)
        aconnectionbox.pausebtn.clicked.connect(th.pause)
        aconnectionbox.cannelbtn.clicked.connect(th.cancel)
        th.resetsignal.connect(self.beReset)
        th.showm_signal.connect(self.showm_signal.emit)
        th.update_state_signal.connect(aconnectionbox.update_state)
        th.pausebtntext_signal.connect(aconnectionbox.pausebtn.setText)
        th.reconnectsignal.connect(self.reconnectionhandle)

        th.start()
        self.connectionwidgetslist.append(aconnectionbox)
        self.connection_ScrollArea_widget.resize(self.connection_ScrollArea_widget.width(),
                                                 20 + (aconnectionbox.height() + 5) * len(self.connectionwidgetslist))
        self.Transmitter.clientthreads.append(th)
        self.Transmitter.connectionips.add(client_address)
        self.Transmitter.allowip.add(client_address)
        print(client_address, "已连接")
        # self.Transmitter.create_a_connection(client_socket, client_address)

    def reset(self, ip):
        for th in self.Transmitter.clientthreads:
            if th.ip == ip:
                th.quit()
                try:
                    th.sendthreadmanager.quit()
                except:
                    print(sys.exc_info())
                self.Transmitter.clientthreads.remove(th)
                break
        try:
            self.Transmitter.connectionips.remove(ip)
            self.Transmitter.allowip.remove(ip)
        except:
            pass
        self.showm_signal.emit("你移除了与{}的连接".format(ip))
        print("已主动移除")

    def beReset(self, ip):
        print("bereset 444444444444")
        for th in self.Transmitter.clientthreads:
            if th.ip == ip:
                self.reconnectthrea = Commen_Thread(th.reconnect)
                self.reconnectthrea.start()
                break

    def reconnectFail(self, ip):
        for th in self.Transmitter.clientthreads:
            if th.ip == ip:
                try:
                    self.Transmitter.clientthreads.remove(th)
                except:
                    print(sys.exc_info(), 295)
        print("已被移除")
        for wid in self.connectionwidgetslist:
            if wid.ip == ip:
                wid.resetwidget()
        self.showm_signal.emit("{}移除了你的一个连接".format(ip))

        print(ip, self.Transmitter.connectionips)
        try:
            self.Transmitter.connectionips.remove(ip)
        except:
            print(sys.exc_info(), 284)

    def autoAllowchange(self, e):
        if e:
            QSettings('Fandes', 'jamtools').setValue("clientfilestransmittertest/needallow", True)
            self.autoallow = False
        else:
            QSettings('Fandes', 'jamtools').setValue("clientfilestransmittertest/needallow", False)
            self.autoallow = True

    def allowconnectchange(self, e):
        if e:
            QSettings('Fandes', 'jamtools').setValue("clientfilestransmittertest/allowconnect", True)
            self.Transmitter.canconnect = True
            self.Transmitter.start()

        else:
            QSettings('Fandes', 'jamtools').setValue("clientfilestransmittertest/allowconnect", False)
            self.Transmitter.canconnect = False

    def killallconnection(self):
        if self.Transmitter.closeall():
            return
        for wid in self.connectionwidgetslist:
            wid.resetwidget()
        self.allowCheckBox.setChecked(False)
        self.Transmitter.connectionips = set()
        self.Transmitter.allowip = set()


class ClientConnectionbox(QGroupBox):
    sendfilessignal = pyqtSignal(list)
    senddirssignal = pyqtSignal(str)
    resetsignal = pyqtSignal(str)
    rootpathchangesignal = pyqtSignal(str)

    def __init__(self, ip, parent: QWidget):
        super(ClientConnectionbox, self).__init__("连接:{}".format(ip), parent)
        self.ip = ip
        self.parent = parent
        self.resize(self.parent.width() - 10, 175)
        self.setAcceptDrops(True)
        self.disconnectbtn = QPushButton("断开", self)
        self.disconnectbtn.setGeometry(5, 18, 40, 25)
        self.disconnectbtn.clicked.connect(self.reset)
        self.signallight = QPushButton("", self)
        self.signallight.setStyleSheet("background-color:rgb(20,239,20);border:2px solid black;border-radius:6px;")
        self.signallight.setGeometry(self.disconnectbtn.x() + self.disconnectbtn.width() + 18,
                                     self.disconnectbtn.y() + 5, 12, 12)

        self.sendfilesbtn = QPushButton("发送文件", self)
        self.sendfilesbtn.setGeometry(5, self.disconnectbtn.y() + self.disconnectbtn.height(), 80, 25)
        self.sendfilesbtn.clicked.connect(self.sendfiles)
        self.senddirbtn = QPushButton("发送文件夹", self)
        self.senddirbtn.setGeometry(self.sendfilesbtn.x() + self.sendfilesbtn.width() + 5, self.sendfilesbtn.y(),
                                    self.sendfilesbtn.width(), self.sendfilesbtn.height())
        self.senddirbtn.clicked.connect(self.senddirs)
        self.threadnum = QSpinBox(self)
        self.threadnum.setPrefix("线程数:")
        self.threadnum.setValue(4)
        self.threadnum.setMinimum(1)
        self.threadnum.setMaximum(64)
        self.threadnum.setGeometry(self.senddirbtn.x() + self.senddirbtn.width() + 5, self.senddirbtn.y(), 100,
                                   self.senddirbtn.height())

        self.rootpathshowedit = QLineEdit("接收路径:下载/jamreceive", self)
        self.rootpathshowedit.setReadOnly(True)
        self.rootpathshowedit.setGeometry(5, self.sendfilesbtn.y() + self.sendfilesbtn.height() + 8, 220, 20)
        self.rootpathchangebtn = QPushButton("…", self)
        # self.rootpathchangebtn.setStyleSheet('border-image: url(:/choice_path.png);')
        self.rootpathchangebtn.setGeometry(self.rootpathshowedit.x() + self.rootpathshowedit.width() + 5,
                                           self.rootpathshowedit.y(),
                                           20, 20)
        self.rootpathchangebtn.clicked.connect(self.rootpathchange)
        self.rootpathchangebtn.setToolTip("改变接收路径")
        self.conditionlabel = QLabel("状态:已就绪", self)
        self.conditionlabel.move(5, self.rootpathshowedit.y() + self.rootpathshowedit.height() + 5)
        self.conditionlabel.resize(self.width() - self.conditionlabel.x(), 55)
        self.pbar = QProgressBar(self)
        self.pbar.setMaximum(100)
        self.pbar.setGeometry(5, 153, self.width() - 10, 18)
        self.setStyleSheet("QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                           "QPushButton:hover{color:green;background-color:rgb(200,200,100);}")

        self.pausebtn = QPushButton("暂停", self)
        self.cannelbtn = QPushButton("取消", self)
        self.pausebtn.setGeometry(self.width() - 40, self.conditionlabel.y(), 40, 25)
        self.cannelbtn.setGeometry(self.pausebtn.x(), self.pausebtn.y() + self.pausebtn.height(),
                                   self.pausebtn.width(), self.pausebtn.height())
        self.cannelbtn.hide()
        self.pausebtn.hide()

    def update_state(self, state: str):
        # print("update state", state)
        self.conditionlabel.setText("状态:{}".format(state))
        if "发送中" in state or "暂停" in state or "接收中" in state:
            if self.pausebtn.isHidden():
                self.pausebtn.setVisible(True)
                self.cannelbtn.setVisible(True)
        else:
            if self.cannelbtn.isVisible():
                self.pausebtn.hide()
                self.cannelbtn.hide()
        if "进度:" in state:
            s = int(eval(state.split("进度:")[-1].split(" ")[0].replace("%", "")))
            self.pbar.setValue(s)
        if "成功" in state:
            self.setalldisable(False)
            self.signallight.setStyleSheet("background-color:rgb(20,239,20);border:2px solid black;border-radius:6px;")
            self.pbar.setValue(100)
        elif "重新连接" in state or "取消" in state:
            self.setalldisable(False)
            self.signallight.setStyleSheet("background-color:rgb(20,239,20);border:2px solid black;border-radius:6px;")
            self.pbar.setValue(0)
            self.disconnectbtn.setEnabled(True)
            self.pbar.setStyleSheet("")
            self.setStyleSheet(
                "QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                "QPushButton:hover{color:green;background-color:rgb(200,200,100);}")
        elif "断开" in state or "掉线" in state:
            self.pbar.setDisabled(True)
            self.pbar.setValue(0)
            self.resetwidget()
            # self.signallight.setStyleSheet(
            #     "background-color:rgb(160,160,160);border:2px solid black;border-radius:6px;")
            # self.setalldisable(True)
            # self.disconnectbtn.setDisabled(True)
            if "掉线" in state:
                print("对方掉线已重置")
                self.reset()
            QApplication.processEvents()
        else:
            self.setalldisable(True)
            self.signallight.setStyleSheet("background-color:rgb(239,239,50);border:2px solid black;border-radius:6px;")
            # self.disconnectbtn.setStyleSheet("QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
            #                    "QPushButton:hover{color:green;background-color:rgb(200,200,100);}")
        QApplication.processEvents()

    def rootpathchange(self):
        dir = QFileDialog.getExistingDirectory(self, "选择接收文件的根目录", QStandardPaths.writableLocation(
            QStandardPaths.DownloadLocation))
        if dir:
            print(dir, "changedir")
            self.rootpathshowedit.setText("接收路径:{}".format(dir))
            self.rootpathchangesignal.emit(dir)

    def resetwidget(self):
        self.signallight.setStyleSheet("background-color:rgb(160,160,160);border:2px solid black;border-radius:6px;")
        self.conditionlabel.setText("状态:已断开!")
        self.pbar.setStyleSheet("""QProgressBar::chunk {
    background-color: gray;
}""")
        # self.sendfilesbtn.disconnect()
        # self.senddirbtn.disconnect()
        # self.disconnectbtn.disconnect()
        self.setAcceptDrops(False)
        self.setalldisable(True)
        self.disconnectbtn.setDisabled(True)
        self.setStyleSheet("QPushButton{color:rgb(120,120,120);background-color:rgb(200,200,200);}")

    def setalldisable(self, d: bool):
        if d:
            # print("set disable")
            self.sendfilesbtn.setStyleSheet("QPushButton{color:rgb(120,120,120);background-color:rgb(200,200,200);}")
            self.senddirbtn.setStyleSheet("QPushButton{color:rgb(120,120,120);background-color:rgb(200,200,200);}")
            self.rootpathchangebtn.setStyleSheet(
                "QPushButton{color:rgb(120,120,120);background-color:rgb(200,200,200);}")
        else:
            # print("set not disable")
            self.sendfilesbtn.setStyleSheet(
                "QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                "QPushButton:hover{color:green;background-color:rgb(200,200,100);}")
            self.senddirbtn.setStyleSheet(
                "QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                "QPushButton:hover{color:green;background-color:rgb(200,200,100);}")
            self.rootpathchangebtn.setStyleSheet(
                "QPushButton{color:black;background-color:rgb(239,239,239);padding:1px 4px;}"
                "QPushButton:hover{color:green;background-color:rgb(200,200,100);}")
        self.sendfilesbtn.setDisabled(d)
        self.senddirbtn.setDisabled(d)
        self.rootpathchangebtn.setDisabled(d)
        self.threadnum.setDisabled(d)

    def reset(self):
        self.resetwidget()
        self.resetsignal.emit(self.ip)

    def sendfiles(self):
        files, l = QFileDialog.getOpenFileNames(self, "选择要发送的文件", "", "all files(*.*);;")
        print(files)
        if len(files):
            self.sendfilessignal.emit(files)

    def senddirs(self):
        dir = QFileDialog.getExistingDirectory(self, "选择要发送的文件夹", "")
        print(dir)
        if len(dir):
            self.senddirssignal.emit(dir)

    def dragEnterEvent(self, e):
        print("box", e.mimeData().urls())

        e.acceptProposedAction()

    def dropEvent(self, e):
        print("boxdrop", e.mimeData().urls())
        data = []
        for i in range(len(e.mimeData().urls())):
            data.append(e.mimeData().urls()[i].toLocalFile())
        filelist = []
        dirlist = []
        for path in data:
            if os.path.isfile(path):
                filelist.append(path)
            else:
                dirlist.append(path)
        if len(filelist):
            self.sendfilessignal.emit(filelist)
        else:
            for d in dirlist:
                if os.path.isdir(d):
                    self.senddirssignal.emit(d)
                    break


class ClientFilesTransmitter(QThread):  # 客户端传输主要线程
    aconnectionsignal = pyqtSignal(socket.socket, str, int)
    reconnectionsignal = pyqtSignal(socket.socket, str)
    foundserverMSGsignal = pyqtSignal(str)
    update_connectionstrchangesignal = pyqtSignal(str)
    show_warningsignal = pyqtSignal(str)
    showm_signal = pyqtSignal(str)

    def __init__(self, parent: ClientFilesTransmitterGroupbox):
        super(ClientFilesTransmitter, self).__init__()
        self.parent = parent

        self.host = ""
        self.allowports = [2110, 5124, 2589, 3645, 8457]  # , 5124, 2589, 3645, 8457
        self.portids = "zxcvb"
        self.port = self.allowports[random.randint(0, len(self.allowports) - 1)]
        print("端口", self.port, self.portids[self.allowports.index(self.port)])

        self.ips = get_ips()
        if len(self.ips) == 0:
            self.show_warningsignal.emit("你的设备没有可用的网卡")
            self.showm_signal.emit("未接入网络!请接入网络(局域网)后使用!")
        self.targetdict = {}
        self.clientthreads = []
        self.connectionips = set()
        self.allowip = set()
        self.segments, self.endsegs = get_Network_segments(self.ips)
        self.canconnect = False
        self.targetendsegs = self.endsegs
        self.targetport = self.port
        if not os.path.exists(
                os.path.join(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), "jamreceive")):
            os.mkdir(os.path.join(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), "jamreceive"))
        self.rootpath = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), "jamreceive")
        self.connectstr = self.encode_ip()
        self.targetconnectstr = ""

    def openserver(self):
        print("开启服务")
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.serversocket.bind(("", self.port))
        except OSError:
            tport = self.allowports[random.randint(0, len(self.allowports) - 1)]
            print("地址重复")
            while tport == self.port:
                tport = self.allowports[random.randint(0, len(self.allowports) - 1)]
            self.port = tport
            self.update_connectionstr()
            self.serversocket.bind(("", self.port))
        self.serversocket.listen()

    def run(self):
        self.openserver()
        self.canconnect = True
        while self.canconnect:
            try:
                client_socket, client_address = self.serversocket.accept()
            except OSError:
                print(sys.exc_info(), "l294")
                if self.canconnect:
                    self.openserver()
                    continue
                break
            if not self.canconnect:
                client_socket.close()
                continue
            try:
                handupmes = client_socket.recv(1024).decode()
                if handupmes.split(":")[0] == "searching":
                    print("被找到", handupmes)
                    if handupmes.split(":")[1] == self.connectstr:
                        client_socket.send("{}".format(client_address[0]).encode())
                        continue
                    else:
                        client_socket.send("outofdate".encode())
                        continue
                elif handupmes == "reconnect":
                    if client_address[0] in self.allowip:
                        client_socket.send("allow".encode())
                        self.reconnectionsignal.emit(client_socket, client_address[0])
                    else:
                        client_socket.send("nopermit".encode())
                else:
                    if handupmes.split(":")[0] == "connect":
                        port = handupmes.split(":")[1]
                        print("jjjj", client_address, self.connectionips, port)
                        if client_address[0] not in self.connectionips:
                            self.aconnectionsignal.emit(client_socket, client_address[0], int(port))
                        else:
                            print("已存在", client_address)
                    else:
                        continue
            except:
                print(sys.exc_info(), "l314")
                client_socket.close()
                continue

        print("关闭服务")

    def update_connectionstr(self):
        self.updata_ips()
        self.connectstr = self.encode_ip()
        self.update_connectionstrchangesignal.emit(self.connectstr)

    def updata_ips(self):
        self.ips = get_ips()
        self.segments, self.endsegs = get_Network_segments(self.ips)

    def encode_ip(self):  # qwer为主机(1)的个数,tyu为没有主机随机加的,poi为不足两位随机加的
        def digitalpuss(d: int, p: int):
            if d + p > 9:
                return d - 10 + p
            else:
                return d + p

        end = self.portids[self.allowports.index(self.port)]

        mid = ""
        e = 0
        for seg in self.endsegs:
            if "." not in seg:
                if seg == str(1):
                    e += 1
                else:
                    m = str(hex(int(seg)))[2:].lower()
                    if len(m) == 2:
                        mid += m
                    else:
                        mid += "poi"[random.randint(0, 2)] + m
            else:
                tm = []
                for eseg in seg.split("."):
                    m = str(hex(int(eseg)))[2:].lower()
                    if len(m) == 2:
                        m = m
                    else:
                        m = "poi"[random.randint(0, 2)] + m
                    tm.append(m)
                mid += tm[0] + "zxv"[random.randint(0, 2)] + tm[1] + "zxv"[random.randint(0, 2)] + tm[2]

        randstr = mid + "qwrt"[e if e < 4 else 3] + end
        print("编码前", randstr)

        randstr = randstr.replace("a", "as?"[random.randint(0, 2)]).replace("b", "bnm"[random.randint(0, 2)]).replace(
            "c", "cgh"[
                random.randint(0, 2)]) \
            .replace("d", "djk"[random.randint(0, 2)]).replace("e", "eyu"[random.randint(0, 2)]).replace("f", "fl+"[
            random.randint(0, 2)])
        randseed = random.randint(0, 9)
        strlist = list(randstr)
        for i, s in enumerate(strlist):
            if s.isdigit():
                strlist[i] = str(digitalpuss(int(s), randseed))
        randstr = str(randseed) + "".join(strlist)
        print(randstr)
        return randstr

    def decode_ip(self, randstr: str):

        def digitalssub(d: int, s: int):
            if d - s < 0:
                return d + 10 - s
            else:
                return d - s

        if randstr == self.connectstr:
            print("企图连接自己?")
            self.show_warningsignal.emit("请不要企图连接自己!")
            return 0
        if not randstr[0].isdigit():
            self.show_warningsignal.emit("请输入正确的连接码!")
            return 0
        # try:
        randseed = int(randstr[0])
        randstrlist = list(randstr[1:])
        for i, s in enumerate(randstrlist):
            if s.isdigit():
                randstrlist[i] = str(digitalssub(int(s), randseed))
        randstr = "".join(randstrlist)
        ra = {"as?": "a", "bnm": "b", "cgh": "c", "djk": "d", "eyu": "e", "fl+": "f"}
        for b in ra.keys():
            for s in b:
                if s in randstr:
                    randstr = randstr.replace(s, ra[b])
        print("解码后:", randstr)
        if randstr[-1] not in self.portids:
            self.show_warningsignal.emit("错误连接码!")
            return 0
        self.targetport = self.allowports[self.portids.index(randstr[-1])]
        segmentstr = randstr[:-1]
        print("segmentstr", segmentstr)
        endsegs = []

        def formatstr(s: str, replacestr: str):
            for rs in replacestr:
                s = s.replace(rs, "")
            return s

        havepoint = []
        for i, s in enumerate(segmentstr):
            if s in "zxv":
                havepoint.append(i)
        if len(havepoint) and len(havepoint) % 2 == 0:
            havepoint = sorted(havepoint)
            print("havepoint", havepoint)
            for i in range(len(havepoint) // 2):
                pos = havepoint[i * 2]
                bseg = segmentstr[pos - 2:pos + 6].replace("z", ".").replace("x", ".").replace("v", ".")
                print("b类主机位置", bseg)
                endsegs.append("{}.{}.{}".format(int("0x" + formatstr(bseg.split(".")[0], "poi"), 16),
                                                 int("0x" + formatstr(bseg.split(".")[1], "poi"), 16),
                                                 int("0x" + formatstr(bseg.split(".")[2], "poi"), 16)))
            segmentstr = segmentstr[:havepoint[0] - 2] + segmentstr[havepoint[-1] + 3:]
        elif len(havepoint) % 2 != 0:
            print("错误连接码")
            self.show_warningsignal.emit("错误连接码")
            return 0
        if segmentstr[-1] not in "qwrt":
            self.show_warningsignal.emit("连接码有误!")
            return 0
        havee = "qwrt".index(segmentstr[-1])
        segmentstr = segmentstr[:-1]
        if havee:
            endsegs.append(str(1))
        print("剩余普通endseg:", segmentstr)
        while len(segmentstr) and len(segmentstr) % 2 == 0:
            endsegs.append(str(int("0x" + segmentstr[:2], 16)))
            segmentstr = segmentstr[2:]
        print("endsegs", endsegs)
        self.targetendsegs = endsegs
        return 1
        # except:
        #     s=sys.exc_info()
        #     print(s)
        #     self.show_warningsignal.emit("连接码解析错误!请联系作者反馈...({})".format(s))

    def findserver(self):
        self.findserverthread = ClientFindServer(self.targetport, self.targetendsegs, self.segments,
                                                 self.targetconnectstr, self.ips)
        self.findserverthread.foundserversignal.connect(self.foundserver)
        self.findserverthread.start()
        QApplication.processEvents()

    def foundserver(self, ip):  # 找到可用连接
        print((ip, self.targetport))
        if ip in self.connectionips:
            print(ip, "已经存在，不连接")
            self.show_warningsignal.emit("该连接已经存在！")
            return
        if ip != "notfound" and ip != "outofdate":
            self.waitAllowThread = clientWaitAllowThread(ip, self.targetport, self.port)
            self.waitAllowThread.allowsignal.connect(self.allowsignalhandle)
            self.waitAllowThread.start()
        self.foundserverMSGsignal.emit(str(ip))

    def allowsignalhandle(self, canconnect, address, clientsocket: socket.socket):  # 等待确认完毕的信号
        """clientsocket:返回的链接socket"""
        if canconnect:
            self.targetdict[address] = self.targetport
            self.parent.create_a_connection(clientsocket, address)
            self.show_warningsignal.emit("已创建与{}的连接".format(address))
        else:
            self.show_warningsignal.emit("对方拒绝了你的连接请求!")

    def findandconnectserver(self, randstr):
        if len(randstr):
            self.showm_signal.emit("正在查找并连接...")
            self.targetconnectstr = randstr
            if self.decode_ip(randstr):
                self.findserver()
        else:
            self.showm_signal.emit("请输入连接码")

    def disconnectserver(self, serverid=0):
        self.clientthreads[serverid].quit()
        self.clientthreads.pop(serverid)

    def closeall(self):
        result = QMessageBox.information(QWidget(), "重置?", "关闭所有连接并禁止被查找?", QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.Yes)
        if result == QMessageBox.No:
            return 1
        self.canconnect = False
        for th in self.clientthreads:
            th.quit()
        del self.clientthreads
        gc.collect()
        self.clientthreads = []
        try:
            self.serversocket.close()
        except AttributeError:
            print("服务未开启")

        self.quit()
        print("已关闭所有")


class clientWaitAllowThread(QThread):
    allowsignal = pyqtSignal(bool, str, socket.socket)

    def __init__(self, ip, port, myport=8888):
        super(clientWaitAllowThread, self).__init__()
        self.ip = ip
        self.myport = myport
        self.targetport = port

    def run(self):
        asaclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        asaclient.connect((self.ip, self.targetport))
        asaclient.send("connect:{}".format(self.myport).encode())
        try:
            connectresult = asaclient.recv(1024).decode()
        except ConnectionResetError:
            print("连接在确认中重置")
            self.allowsignal.emit(False, self.ip, asaclient)
            asaclient.close()
            return
        print("connectresult", connectresult)
        if connectresult == "allow":
            print("被允许连接")
            self.allowsignal.emit(True, self.ip, asaclient)
        else:
            print("拒绝连接")
            self.allowsignal.emit(False, self.ip, asaclient)
            asaclient.close()


class ClientFindServer(QThread):  # 根据连接码寻找服务器总线程
    foundserversignal = pyqtSignal(str)

    def __init__(self, targetport, targetendsegs, segments, connectstr, ips):
        super(ClientFindServer, self).__init__()
        print("target:", targetport, targetendsegs, segments, connectstr)
        self.targetport, self.segments = targetport, segments
        self.findthreads = []
        self.found = False
        self.connectstr = connectstr
        self.ips = ips
        self.bendseg = []
        self.cendseg = []
        for endseg in targetendsegs:
            if "." in endseg:
                self.bendseg.append(endseg)
            else:
                self.cendseg.append(endseg)

    def run(self):
        for segment in self.segments:
            if len(segment.split(".")) == 2:
                if len(self.bendseg):
                    print("解析b类地址")
                    thread = afindserverthread(self.targetport, segment, self.bendseg, self.connectstr, self.ips)
                    thread.foundsignal.connect(self.targetfound)
                    thread.start()
                    self.findthreads.append(thread)

            else:
                thread = afindserverthread(self.targetport, segment, self.cendseg, self.connectstr, self.ips)
                thread.foundsignal.connect(self.targetfound)
                thread.start()
                self.findthreads.append(thread)
        for thread in self.findthreads:
            thread.wait()
        if not self.found:
            print("没有找到")
            self.foundserversignal.emit("notfound")

    def targetfound(self, ip):
        self.found = True
        print("找到:", ip)
        for thread in self.findthreads:
            thread.quit()
        self.foundserversignal.emit(ip)
        # for thread in self.findthreads:
        #     # thread.wait()
        # self.wait()
        del self.findthreads
        gc.collect()
        # self.findthreads = []


class afindserverthread(QThread):  # 每个网段都开一个线程同时寻找
    foundsignal = pyqtSignal(str)

    def __init__(self, port, segment, targetendsegs, connectstr, ips):
        super(afindserverthread, self).__init__()
        self.targetport, self.segment, self.targetendsegs = port, segment, targetendsegs
        self.fquit = False
        self.connectstr = connectstr
        self.ips = ips

    def run(self):
        for endseg in self.targetendsegs:
            ip = self.segment + str(endseg)
            if ip in self.ips:
                print(ip, "是自己的ip")
                continue
            testclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                testclient.settimeout(3)
                testclient.connect((ip, self.targetport))
            except:
                print(sys.exc_info(), "l557")
                if self.fquit:
                    break
                testclient.close()
                continue
            try:
                testclient.send("searching:{}".format(self.connectstr).encode())
                ip = testclient.recv(1024).decode()
                print(ip)
                if ip == "outofdate":
                    print("out of date")
                    self.foundsignal.emit("outofdate")
                    break

            except:
                print(sys.exc_info(), "l572")
                if self.fquit:
                    break
                testclient.close()
                continue
            if not self.fquit:
                self.foundsignal.emit(self.segment + str(endseg))
            break
        try:
            testclient.close()
        except:
            print(sys.exc_info())

    def quit(self):
        self.fquit = True
        super(afindserverthread, self).quit()


class ClientListenThread(QThread):  # 客户端连接后持续监听线程
    resetsignal = pyqtSignal(str)
    reconnectsignal = pyqtSignal(socket.socket, str, bool)
    showm_signal = pyqtSignal(str)
    update_state_signal = pyqtSignal(str)
    pausebtntext_signal = pyqtSignal(str)

    def __init__(self, clientsocket: socket.socket, parent: ClientFilesTransmitter, ip):
        super(ClientListenThread, self).__init__()
        self.ip = ip
        self.parent = parent
        self.clientsocket = clientsocket
        self.onlistening = True
        self.rootpath = self.receivepath = self.parent.rootpath
        self.sendthreadnum = 4

    def run(self):
        self.onlistening = True
        allbytes = "".encode()
        while self.onlistening:
            try:
                a = self.clientsocket.recv(9999)
                if len(a) == 0:
                    print("no data exit 878")
                    # self.resetsignal.emit(self.ip)
                    self.showm_signal.emit("{}已断开!".format(self.ip))
                    break
                allbytes += a
                first = allbytes.find("<|<||{".encode())
                last = allbytes.find("||>|>".encode())
                if first != -1 and last != -1:
                    jsondata = json.loads(allbytes[first + 5:last].decode())
                    allbytes = allbytes[last + 5:]
                    action = jsondata["action"]
                    print("读取到:", action, jsondata)
                    if action == "quit":
                        raise ConnectionResetError
                    elif action == "senddir":
                        try:
                            self.update_state_signal.emit("正在创建文件夹...")
                        except:
                            print(sys.exc_info(), "915")
                        dirinfo = jsondata["filesizeinfo"]
                        size = jsondata["size"]
                        self.readytoreceive(dirinfo, self.ip, jsondata["port"], jsondata["thread"], size)
                    elif action == "sendfiles":
                        try:
                            self.update_state_signal.emit("准备接收文件...")
                        except:
                            print(sys.exc_info(), "923")
                        dirinfo = jsondata["filesizeinfo"]
                        size = jsondata["size"]
                        self.readytoreceive(dirinfo, self.ip, jsondata["port"], jsondata["thread"], size)
                    elif action == "pause":
                        print("对方已暂停..")
                        self.pause(True)
                    elif action == "cancel":
                        print("对方已取消")
                        self.cancel(True)
                    elif action == "readytosend":
                        print("对方已准备好连接")
                        sendsize = jsondata["sendsize"]
                        filestartdict = jsondata["filestartdict"]
                        noneed = jsondata["noneed"]
                        self.readytosend(filestartdict, sendsize, noneed)
            except ConnectionResetError:
                print("对方已重置", self.onlistening)
                if self.onlistening:
                    self.resetsignal.emit(self.ip)
                try:
                    self.sendthreadmanager.actioning = False
                    self.onlistening = False
                    self.sendthreadmanager.wait()
                except:
                    print(sys.exc_info(), "l862")
                break
            except ConnectionError:
                print(sys.exc_info(), "l628")
                self.resetsignal.emit(self.ip)
                break
            except OSError:
                print(sys.exc_info(), 1001)
                self.resetsignal.emit(self.ip)
                self.showm_signal.emit("{}已断开!对方网络状态已改变!".format(self.ip))
            except:
                print(sys.exc_info(), "l868")
                self.resetsignal.emit(self.ip)
                self.showm_signal.emit("{}已断开!未知错误!".format(self.ip))

    def reconnect(self):
        try:
            port = self.parent.targetdict[self.ip]
            asaclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            t = 3
            while t:
                try:
                    print("已发送重新连接请求", self.ip, port)
                    asaclient.connect((self.ip, port))
                    asaclient.send("reconnect".encode())

                    asaclient.settimeout(5)
                    if asaclient.recv(1024).decode() != "allow":
                        print("对方不允许")
                    asaclient.settimeout(None)
                    print("已重连")
                    self.reconnectsignal.emit(asaclient, self.ip, False)
                    return
                except OSError:
                    print("你的网络状态已改变!")
                    self.update_state_signal.emit("你的网络状态已改变!")
                except:
                    print(sys.exc_info(), 1061)
                t -= 1
            self.reconnectsignal.emit(asaclient, self.ip, True)
        except:
            print("重新连接失败", sys.exc_info())

    def changethreadnum(self, num: int):
        self.sendthreadnum = num

    def sendfiles(self, files: list):
        self.showm_signal.emit("开始发送文件...")
        self.anazytosend(files)

    def anazytosend(self, files):
        self.showm_signal.emit("正在计算文件总大小")
        self.update_state_signal.emit("正在统计文件大小...")

        if type(files) == list:
            try:
                self.sendrootpath = os.path.split(files[0])[0]
                filesizedict = {fomatpath(p.replace(self.sendrootpath, '')): os.path.getsize(p) for p in files if
                                p != '' and self.sendrootpath in p}
                size = sum(filesizedict.values())
            except OSError:
                print(sys.exc_info(), 1026)
                self.showm_signal.emit(str(sys.exc_info()))
                self.update_state_signal.emit("文件路径出错:\n已重新连接")
                return
            action = {"action": "sendfiles", "size": size, "filesizeinfo": filesizedict}
            filelist = files
        elif os.path.isdir(files):
            filelist, size, filesizedict = get_directory_info(files)
            action = {"action": "senddir", "size": size, "filesizeinfo": filesizedict}
            self.sendrootpath = os.path.split(files)[0]
        else:
            self.showm_signal.emit("无法解析文件路径!")
            return

        print("文件总大小为:", size)
        self.sendtotalsize = size
        self.update_state_signal.emit("文件总大小为:{}M".format(size / 1024 // 1024))
        self.filessenderserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            port = random.randint(2048, 60000)
            self.filessenderserver.bind(("", port))
        except:
            port = random.randint(2048, 60000)
            self.filessenderserver.bind(("", port))
        action["port"] = port
        action["thread"] = self.sendthreadnum
        self.sendDump(action)
        self.update_state_signal.emit("等待对方响应...\n已发送文件信息等待对方分析...")

    def readytosend(self, filestartdict: dict, sendsize, noneeddict):

        self.sendthreadmanager = clientSendThreadManager(self.filessenderserver, self.sendrootpath, filestartdict,
                                                         totalsize=self.sendtotalsize, threadnum=self.sendthreadnum,
                                                         sendsize=sendsize, noneeddictlen=len(noneeddict))
        self.sendthreadmanager.update_state_signal.connect(self.transformstatesignal)
        self.sendthreadmanager.start()

    def pause(self, be=False):
        onpause = False
        try:
            self.sendthreadmanager.pausesendchange()
            onpause = self.sendthreadmanager.pause
        except AttributeError:
            pass
        try:
            self.receivethreadmanager.pauserecchange()
            onpause = self.receivethreadmanager.pause
        except AttributeError:
            pass
        if onpause:
            self.pausebtntext_signal.emit("继续")
            if be:
                self.update_state("对方已暂停")
            else:
                self.sendDump({"action": "pause"})
                self.update_state("已暂停")
        else:
            self.pausebtntext_signal.emit("暂停")
            if not be:
                self.sendDump({"action": "pause"})
            self.update_state("继续传输...")

    def cancel(self, be=False):
        try:
            self.sendthreadmanager.cancelsend()
        except AttributeError:
            pass
        try:
            self.receivethreadmanager.cancelrec()
        except AttributeError:
            pass
        if be:
            self.update_state("对方已取消")
        else:
            self.update_state("已取消")
            self.sendDump({"action": "cancel"})

    def transformstatesignal(self, s):
        try:
            self.update_state_signal.emit(s)
        except:
            print("发送state失败")

    def senddirs(self, dir: str):
        self.showm_signal.emit("开始发送文件夹...")
        self.anazytosend(dir)

    def rootpathchange(self, p):
        self.rootpath = p

    def sendDump(self, dumpjs: dict):
        try:
            self.clientsocket.send("<|<||".encode() + json.dumps(dumpjs).encode() + "||>|>".encode())
        except:
            print(sys.exc_info(), 1200, "发送失败")

    def quit(self):
        self.onlistening = False
        self.sendDump({"action": "quit"})
        self.clientsocket.close()
        print("已重置")
        super(ClientListenThread, self).quit()

    def readytoreceive(self, filesizeinfo: dict, ip, port, threadnum, size):
        if not os.path.exists(self.rootpath):
            os.mkdir(self.rootpath)
        path = os.path.join(self.rootpath, "receivefrom{}".format(self.clientsocket.getsockname()[0]))
        if not os.path.exists(path):
            os.mkdir(path)
        self.receivepath = path
        create_all_dirs(filesizeinfo.keys(), rootpath=path)
        needreceivedict, noneed, recsize = self.analysistorec(filesizeinfo, rootpath=path)
        respondict = {'action': 'readytosend', "sendsize": recsize, "filestartdict": needreceivedict, "noneed": noneed}
        self.sendDump(respondict)
        self.receivethreadmanager = clientreceivemanager(ip, port, threadnum, self.receivepath, size, filesizeinfo,
                                                         recsize, noneedlen=len(noneed))
        self.receivethreadmanager.update_state_signal.connect(self.update_state)
        self.receivethreadmanager.start()
        # while len(self.receiverthreads)<threadnum:
        #     th=clientreceivemanager()
        #     self.receiverthreads.append()

    def analysistorec(self, filesizeinfo: dict, rootpath='.'):
        returnneedsenddict = {}
        notneeddict = []
        aleadysendsize = 0
        for file in filesizeinfo.keys():
            filepath = os.path.join(rootpath, file)
            if not os.path.exists(filepath):
                temppath = os.path.join(os.path.split(filepath)[0], "jamreceiving" + os.path.split(filepath)[1])
                if os.path.exists(temppath):
                    s = os.path.getsize(temppath)
                    aleadysendsize += s
                    returnneedsenddict[file] = s
                else:
                    returnneedsenddict[file] = 0
            else:
                s = os.path.getsize(filepath)
                if s == filesizeinfo[file]:
                    print("文件大小相同")
                    aleadysendsize += s
                    notneeddict.append(file)
                else:
                    returnneedsenddict[file] = 0
        return returnneedsenddict, notneeddict, aleadysendsize

    def update_state(self, s):
        try:
            self.update_state_signal.emit(s)
        except:
            print(sys.exc_info(), "l937")


class clientreceivemanager(QThread):
    update_state_signal = pyqtSignal(str)

    def __init__(self, ip, port, threadnum, rootpath, size, filesizeinfo, recsize=0, noneedlen=0):
        super(clientreceivemanager, self).__init__()
        self.receiverthreads = []
        self.ip = ip
        self.port = port
        self.filesizeinfo = filesizeinfo
        self.totalsize = size
        self.threadnum = threadnum
        self.onreceiving = True
        self.pause = False
        self.cancel = False
        self.datedict = {}
        self.rootpath = rootpath
        self.recsize = recsize
        self.noneedlen = noneedlen
        self.drecsize = 0

    def run(self):
        while len(self.receiverthreads) < self.threadnum:
            self.update_state_signal.emit("正在创建接收线程{}...".format(len(self.receiverthreads)))
            receivesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            receivesocket.connect((self.ip, self.port))
            th = areceivethread(self, receivesocket)
            th.start()
            self.receiverthreads.append(th)
            print("创建了一个接收线程")
        st = time.time()
        utime = time.time()
        while self.onreceiving:
            if self.cancel:
                break
            if self.pause or len(self.datedict) == 0:
                time.sleep(0.1)
                continue

            for path in list(self.datedict.keys()):  # 遍历存储数据的datedict
                print(os.path.join(self.rootpath, path))
                filepath = os.path.join(self.rootpath, path)
                temppath = os.path.join(os.path.split(filepath)[0], "jamreceiving" + os.path.split(filepath)[1])
                if os.path.exists(temppath):
                    file = open(temppath, "ab")
                    idsize = os.path.getsize(temppath)
                    file.seek(idsize)
                    self.recsize += idsize
                else:
                    file = open(temppath, "wb")
                    idsize = 0
                writeTime = time.time()
                while "end" not in self.datedict[path] or self.filesizeinfo[path] > idsize:  # 一个文件没有接收结束
                    # print(self.datedict[path].keys(), idsize)
                    if self.cancel:
                        break
                    elif self.pause:
                        time.sleep(0.1)
                        print("暂停中")
                        writeTime = time.time()

                        continue
                    if idsize in self.datedict[path]:
                        file.write(self.datedict[path][idsize])
                        writeTime = time.time()
                        # print("写入一组数据{}".format(idsize))
                        dumpsize = len(self.datedict[path][idsize])
                        self.recsize += dumpsize
                        del self.datedict[path][idsize]
                        idsize += dumpsize
                    now = time.time()
                    if now - writeTime > 20:  # 超时
                        print("接收{}超时".format(path))
                        break
                    time.sleep(0.01)
                    if now - utime > 0.5 and not self.pause:
                        dtime = now - utime
                        dsize = self.recsize - self.drecsize
                        self.update_state_signal.emit("接收中...\n正在接收{}\n进度:{:.2f}% 速度:{:.2f}M/s"
                                                      .format(path, self.recsize / self.totalsize * 100,
                                                              dsize / 1024 / 1024 / dtime))

                        print("接收中..{:.2f}%".format(self.recsize / self.totalsize * 100))
                        utime = time.time()
                        self.drecsize = self.recsize
                print("已写完一个文件{}".format(path))
                file.close()
                if os.path.exists(temppath) and os.path.getsize(temppath) == self.filesizeinfo[path]:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    os.rename(temppath, filepath)
                else:
                    print("传输出错")
                del self.datedict[path]

        print("主接收线程退出")
        if not self.cancel:
            self.update_state_signal.emit("接收成功!\n共接收{}个文件{},用时{:.2f}s\n总大小:{:.2f}M 平均速率:{:.2f}M/s"
                                          .format(len(self.filesizeinfo),
                                                  "(含{}个相同文件)".format(self.noneedlen) if self.noneedlen else "",
                                                  time.time() - st,
                                                  self.totalsize / 1024 / 1024,
                                                  self.totalsize / 1024 / 1024 / (time.time() - st)))

    def pauserecchange(self):
        self.pause = not self.pause

    def cancelrec(self):
        self.cancel = True


class areceivethread(QThread):
    def __init__(self, parent: clientreceivemanager, receivesocket: socket.socket):
        super(areceivethread, self).__init__()
        self.parent = parent
        self.receivesocket = receivesocket

    def run(self):
        streambytes = "".encode()
        while self.parent.onreceiving:
            try:
                recbytes = self.receivesocket.recv(9999999)
                if len(recbytes) == 0:
                    print("no data exit")
                    break
                streambytes += recbytes
            except ConnectionResetError:
                print("接收连接被重置")
                break
            first = streambytes.find("<|<||{".encode())
            last = streambytes.find("||>|>".encode())
            if first != -1 and last != -1:  # 防止发送本源码时出错
                allbytes = streambytes[first + 5:last]
                middle = allbytes.find(">|<".encode())
                print("allbytes", allbytes[:middle].decode())
                try:
                    info = json.loads(allbytes[:middle].decode())
                except:
                    print(sys.exc_info(), "l1231")
                else:
                    print("info", info)
                    action = info["action"]
                    path = info['path']
                    print("正在写", path)
                    index = info["idsize"]
                    # print("receive a datastream", path, index)
                    if action == "data":
                        databytes = allbytes[middle + 3:]
                        if path in self.parent.datedict:
                            self.parent.datedict[path][index] = databytes
                        else:
                            self.parent.datedict[path] = {index: databytes}
                    elif action == "quit":
                        self.parent.onreceiving = False
                        self.receivesocket.close()
                        break
                    else:
                        if path in self.parent.datedict:
                            self.parent.datedict[path]["end"] = index
                        else:
                            self.parent.datedict[path] = {"end": index}
                    streambytes = streambytes[last + 5:]
        print("子接收线程退出")


class clientSendThreadManager(QThread):  # 发送线程主管理
    showm_signal = pyqtSignal(str)
    update_state_signal = pyqtSignal(str)

    # reset_signal=pyqtSignal()
    def __init__(self, clientsocket: socket.socket, rootpath, needsenddict: dict, totalsize, threadnum=4, sendsize=0,
                 noneeddictlen=0):
        super(clientSendThreadManager, self).__init__()
        self.filessenderserver = clientsocket
        self.actioning = True
        self.pause = False
        self.cancel = False
        self.threadnum = threadnum
        self.threadslist = []

        self.totalsize = totalsize
        self.sendsize = sendsize
        self.oldsize = 0
        self.oldtime = time.time()
        self.noneeddictlen = noneeddictlen
        self.sendingname = ""
        self.needsenddict = needsenddict
        self.filelist = [os.path.join(rootpath, d) for d in needsenddict.keys()]  # 需要传输的文件列表
        self.rootpath = rootpath

    def run(self):
        self.filessenderserver.listen()
        self.actioning = True
        while len(self.threadslist) < self.threadnum:  # 开始创建发送线程
            self.update_state_signal.emit("正在创建线程...\n等待对方连接中...{}/{}".format(len(self.threadslist), self.threadnum))
            try:
                self.filessenderserver.settimeout(20)
                sendersocket, address = self.filessenderserver.accept()
                self.filessenderserver.settimeout(None)
                asender = asendthread(self, sendersocket)
                asender.start()
                self.threadslist.append(asender)
                print("创建了一个发送线程")
            except:
                print(sys.exc_info(), "l1101")
                try:
                    self.update_state_signal.emit("发送失败!对方似乎已经掉线了!")
                except:
                    print("state 更新失败", sys.exc_info())
                self.showm_signal.emit("对方似乎已经掉线了!")
                return

        self.sendfiles(self.filelist)
        # self.filesexplainer.start()
        # while self.actioning:
        #     try:
        #         a = self.threadslist[0].sendsocket.recv(999999)
        #         print(a, 8525555555555555555555555555555555555555555555555)
        #         time.sleep(0.5)
        #     except (ConnectionResetError, ConnectionAbortedError):
        #         print("发送连接被重置!")
        #         self.actioning = False
        #         self.filessenderserver.close()
        #         break
        print("已退出发送")

    def sendfiles(self, fileslist):
        st = time.time()
        for file in fileslist:
            if not self.actioning:
                break
            if self.cancel:
                break
            elif self.pause:
                time.sleep(0.1)
                print("暂停中")
                continue
            print("开始发送{}".format(file))
            self.sendingname = os.path.split(file)[1]
            idsize = 0
            if not os.path.exists(file):
                print("{}文件不存在".format(file))
                self.showm_signal.emit("{}文件不存在".format(file))
                continue
            with open(file, "rb")as f:
                bufsize = 9999999
                data = f.read(bufsize)
                self.sendsize += len(data)
                filepath = fomatpath(file.replace(self.rootpath, ""))
                while data and self.actioning:
                    if self.cancel:
                        break
                    elif self.pause:
                        time.sleep(0.1)
                        print("暂停中")
                        continue
                    datedict = {"action": "data", "path": filepath, "idsize": idsize}
                    databytes = "<|<||".encode() + json.dumps(datedict).encode(
                        "utf-8") + ">|<".encode() + data + "||>|>".encode()
                    self.sendadump(databytes)
                    self.get_speed()
                    print(idsize)
                    idsize += len(data)
                    data = f.read(bufsize)
                    self.sendsize += len(data)

                datedict = {"action": "end", "path": filepath, "idsize": idsize}
                databytes = "<|<||".encode() + json.dumps(datedict).encode(
                    "utf-8") + ">|<".encode() + "".encode() + "||>|>".encode()
                self.sendadump(databytes)
        print("发送完成{}".format(time.time() - st))
        time.sleep(1)
        for th in self.threadslist:
            datedict = {"action": "quit", "path": "filepath", "idsize": 0}
            databytes = "<|<||".encode() + json.dumps(datedict).encode(
                "utf-8") + ">|<".encode() + "".encode() + "||>|>".encode()
            try:
                th.sendsocket.send(databytes)
            except:
                print("发送结束指令失败", (sys.exc_info()))
            print("子线程发送结束指令")
        self.filessenderserver.close()
        size = self.totalsize / 1024 / 1024
        speed = size / (time.time() - st)
        try:

            if self.cancel:
                self.update_state_signal.emit("已取消")
            elif not self.actioning:
                self.update_state_signal.emit("已断开!")
            else:
                self.update_state_signal.emit(
                    "发送成功!\n已发送{}个文件{},用时:{:.2f}s\n共{:.2f}M,平均速率:{:.2f}M/s".format(len(fileslist),
                                                                                   "({}个相同文件)".format(
                                                                                       self.noneeddictlen) if self.noneeddictlen else "",
                                                                                   time.time() - st,
                                                                                   size,
                                                                                   speed))
        except:
            print(sys.exc_info())
        self.actioning = False

    def get_speed(self):
        t = time.time()
        b = self.sendsize / self.totalsize * 100
        s = (self.sendsize - self.oldsize) / 1024 / 1024 / (t - self.oldtime) if t - self.oldtime > 0 else 0
        print("进度:{:.2f}% 速度:{:.2f}M/s".format(b if b <= 100 else 100, s))
        if not self.pause:
            self.update_state_signal.emit(
                "发送中...\n正在发送{}...\n进度:{:.2f}% 速度:{:.2f}M/s".format(self.sendingname, b if b <= 100 else 100, s))

        self.oldsize = self.sendsize
        self.oldtime = t

    def sendadump(self, databytes):
        while databytes != "".encode() and self.actioning:
            for th in self.threadslist:
                if th.data == "".encode():
                    th.data = databytes
                    databytes = "".encode()
            time.sleep(0.05)

    def listener_on_sender(self):
        streambytes = "".encode()
        while self.actioning:
            try:
                recbytes = self.receivesocket.recv(9999999)
                if len(recbytes) == 0:
                    print("no data exit")
                    break
                streambytes += recbytes
            except ConnectionResetError:
                print("接收连接被重置")
                break
            first = streambytes.find("<|<||{".encode())
            last = streambytes.find("||>|>".encode())
            print("接收到数据", streambytes)
            if first != -1 and last != -1:
                allbytes = streambytes[first + 5:last]

    def pausesendchange(self):
        self.pause = not self.pause

    def cancelsend(self):
        self.cancel = True
        self.actioning = False

    def quit(self):
        self.actioning = False
        self.filessenderserver.close()
        super(clientSendThreadManager, self).quit()


class asendthread(QThread):
    nodatasignal = pyqtSignal(QThread)

    def __init__(self, parent: clientSendThreadManager, sendsocket: socket.socket):
        super(asendthread, self).__init__()
        self.parent = parent
        self.sendsocket = sendsocket
        self.data = "".encode()

    def run(self):
        while self.parent.actioning:
            if len(self.data) > 0:
                self.sendsocket.send(self.data)
                self.data = "".encode()
            else:
                time.sleep(0.1)
        self.sendsocket.close()
        print("子线程退出")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    t = ClientFilesTransmitterGroupbox()
    t.show()

    sys.exit(app.exec_())
