import base64
import hashlib
import json

from PyQt5.QtNetwork import QNetworkInterface, QHostInfo

import html
import http.server
import mimetypes
import os
import platform
import posixpath
import queue
import random
import re
import shutil
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from io import StringIO
from socketserver import ThreadingMixIn

import psutil
import qrcode
from PIL import ImageQt
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QObject, QSettings
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QDesktopServices, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QGroupBox, QComboBox, QFileDialog, QCheckBox, QLineEdit

SHOW_PATH = os.getcwd()
Work_Path = os.getcwd()


def get_ips():
    match_ip_list = []
    ipconfig_result_list = os.popen('ipconfig|findstr IPv4').readlines()
    for i in range(0, len(ipconfig_result_list)):
        if 'IPv4 地址' in ipconfig_result_list[i] and "自动配置" not in ipconfig_result_list[i]:
            match_ip = ipconfig_result_list[i].split(":")[-1].replace(" ", "").replace("\n", "")

            match_ip_list.append(match_ip)
    # print("使用中的ip:", match_ip_list)
    return match_ip_list


def get_all_networks_nameandip():
    r""" 打印多网卡 mac 和 ip 信息 """
    dic = psutil.net_if_addrs()
    # print(dic)
    networks = {}
    for adapter in dic:
        snicList = dic[adapter]
        ipv4 = '无 ipv4 地址'
        for snic in snicList:
            if snic.family.name == 'AF_INET':
                ipv4 = snic.address
        networks[adapter] = ipv4
    # print(networks)
    return networks


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def modification_date(filename):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(filename)))


q = queue.Queue()


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=SHOW_PATH, **kwargs):
        # print("初始化")

        self.pathm = SHOW_PATH
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        q.put({"ip": self.client_address[0], "time": self.log_date_time_string(), "action": args})

    def do_GET(self):
        print("do get", self.path, self.headers["Cookie"])
        f = self.respond_get()
        if f:
            line = f.read(999999)
            try:
                while line:
                    print("doget action")
                    if type(line) is str:
                        self.wfile.write(line.encode("utf-8"))
                    else:
                        # print("2")
                        self.wfile.write(line)

                    line = f.read(999999)
            except WindowsError:
                print(sys.exc_info(), 103)

    def do_HEAD(self):
        print("do head")
        f = self.respond_get()
        if f:
            f.close()

    def do_POST(self):
        print("do post", self.path)
        # print(self.headers)
        post_data = self.rfile.read(int(self.headers['content-length'])).decode()
        # print(post_data)
        datadict = json.loads(post_data)
        if "location" in datadict.keys():
            datadict["location"] = urllib.parse.unquote(datadict["location"])
        requesttype = datadict["requesttype"]
        print("requesttype :", requesttype)
        if requesttype == "login":
            psw = datadict["password"]
            if psw == QSettings('Fandes', 'jamtools').value('transmitter/login_password', "1234"):
                print("密码正确")
                cookie = {
                    "port": "{}".format(QSettings('Fandes', 'jamtools').value("webtransmitterport", 8524, type=int)),
                    "password": "{}".format(
                        QSettings('Fandes', 'jamtools').value('transmitter/login_password', "1234"))}
                cookiestr = json.dumps(cookie)
                encode = str.maketrans("so3wudphankvigbrq85t94lm71jf6cyzx2e", "i91x4bpv2cytol7aw5szhjr3gkd6mn8eufq")
                # decode = str.maketrans("i91x4bpv2cytol7aw5szhjr3gkd6mn8eufq", "so3wudphankvigbrq85t94lm71jf6cyzx2e")
                cookiestr = cookiestr.translate(encode)
                print("encode", cookiestr)
                self.response_post(200, cookiestr)
            else:
                print("密码不正确")
                self.response_post(203, '{"密码不正确":0}')
            return
        elif requesttype == "chekcfile":
            print(datadict)
            fn = datadict["filename"]
            location = os.path.join(os.path.join(self.pathm, str(datadict["location"]).lstrip("/")),
                                    datadict["filename"])
            prlocation = location + ".jamdownloading"
            size = datadict["size"]
            print(fn, location, size)
            if os.path.exists(location):
                startdata = datadict["checkdata"]
                startdata = base64.b64decode(startdata[startdata.find("base64,") + 7:])  # 提取出base64数据
                print("存在同名文件", startdata[:50])
                with open(location, "rb")as f:
                    filedata = f.read(1024)
                    print(filedata[:50])
                if startdata == filedata and size == os.path.getsize(location):
                    print("文件开头/大小相同")
                    self.response_post(200, '{"flag":"2"}')
                else:
                    print("文件不同,重命名")
                    n = 1
                    pl = os.path.splitext(fn)
                    newname = pl[0] + "-{}".format(n) + pl[1]
                    newpath = os.path.join(os.path.join(self.pathm, str(datadict["location"]).lstrip("/")), newname)
                    while os.path.exists(newpath):
                        n += 1
                        newname = pl[0] + "-{}".format(n) + pl[1]
                        newpath = os.path.join(os.path.join(self.pathm, str(datadict["location"]).lstrip("/")), newname)
                    jslist = {"flag": "3", "newName": newname}
                    js = json.dumps(jslist)
                    print("新命名为:", newpath, newname, js)
                    self.response_post(200, js)
            elif os.path.exists(prlocation):
                print("存在未完成传输")
                startdata = datadict["checkdata"]
                startdata = base64.b64decode(startdata[startdata.find("base64,") + 7:])  # 提取出base64数据
                with open(prlocation, "rb")as f:
                    filedata = f.read(1024)
                if startdata == filedata:
                    print("文件正确,继续传输", startdata[:10], filedata[:10])
                    startid = os.path.getsize(prlocation)
                    self.response_post(200, '{"flag":"1","startindex":"' + str(startid) + '"}')
                else:
                    print("文件不同,删除重传")
                    os.remove(prlocation)
                    self.response_post(200, '{"startindex":"0","flag":"0"}')
            else:
                self.response_post(200, '{"startindex":"0","flag":"0"}')
        elif requesttype == "finishupload":
            print("结束", datadict)
            location = os.path.join(os.path.join(self.pathm, str(datadict["location"]).lstrip("/")),
                                    datadict["filename"])
            prlocation = location + ".jamdownloading"
            truesize = datadict["totalsize"]
            st = time.time()
            while truesize != os.path.getsize(prlocation) and (time.time() - st) < 2:
                time.sleep(0.1)
                print("wait writing")
            print(truesize, os.path.getsize(prlocation))
            if os.path.exists(prlocation) and os.path.getsize(prlocation) == datadict["totalsize"]:
                os.rename(prlocation, location)
                self.response_post(200)
            else:
                print("文件校验出错")
                if os.path.exists(prlocation): os.remove(prlocation)
                self.response_post(500)
        elif requesttype == "uploaddata":
            try:
                d = datadict["data"]
                d = d[d.find("base64,") + 7:]
                d = base64.b64decode(d)
                # print(d[:10])
                location = os.path.join(os.path.join(self.pathm, str(datadict["location"]).lstrip("/")),
                                        datadict["filename"]) + ".jamdownloading"
                print("receive data", datadict["startindex"])
            except:
                print(sys.exc_info(), 209)
                self.response_post(500)
            else:
                with open(location, "ab")as f:
                    f.write(d)
                self.response_post(200)
        elif requesttype == "stopupload":
            location = os.path.join(os.path.join(self.pathm, str(datadict["location"]).lstrip("/")),
                                    datadict["filename"]) + ".jamdownloading"
            if os.path.exists(location):
                os.remove(location)
        elif requesttype == "createdir":
            d = os.path.join(self.pathm, str(datadict["location"]).lstrip("/home"))
            location = os.path.join(d, datadict["dirname"])
            try:
                if os.path.exists(d):
                    os.mkdir(location)
                    self.response_post(200)
                    print("创建文件夹成功")
                else:
                    print("创建文件夹失败,没有", d, urllib.parse.unquote(d))
                    raise Exception
            except:
                self.response_post(400)

    # json.dumps()# 将python对象编码成Json字符串
    # json.loads() # 将Json字符串解码成python对象
    # json.dump() # 将python中的对象转化成json储存到文件中
    # json.load()# 将文件中的json的格式转化成python对象提取出来
    def response_post(self, code: int = 200, jsonstr="{}", Content_type="text/plain", ):
        # s = json.dumps(jsonstr)
        self.send_response(code)
        self.send_header("Content-type", Content_type)
        self.send_header("Content-Length", str(len(jsonstr)))
        self.end_headers()
        self.wfile.write(jsonstr.encode())

    def get_file_md5(self, file_name):
        """
        计算文件的md5
        :param file_name:
        :return:
        """
        m = hashlib.md5()  # 创建md5对象
        with open(file_name, 'rb') as fobj:
            while True:
                data = fobj.read(4096)
                if not data:
                    break
                m.update(data)  # 更新md5对象

        return m.hexdigest()  # 返回md5对象

    def judge_cookie(self):
        try:
            cookiedict = {s.split("=")[0]: s.split("=")[1] for s in str(self.headers["Cookie"]).split("; ")}
            print(cookiedict)
            if "p2iix9ab" in cookiedict.keys() and "p9az" in cookiedict.keys():
                decode = str.maketrans("i91x4bpv2cytol7aw5szhjr3gkd6mn8eufq", "so3wudphankvigbrq85t94lm71jf6cyzx2e")
                setting = QSettings('Fandes', 'jamtools')
                port = cookiedict["p9az"].translate(decode)
                password = cookiedict["p2iix9ab"].translate(decode)
                if int(port) != setting.value("webtransmitterport", 8524, type=int) or \
                        password != setting.value('transmitter/login_password', "1234"):
                    print("cookie不正确", password, port, setting.value('transmitter/login_password', "1234"),
                          setting.value("webtransmitterport", 8524, type=int))
                    return False
                else:
                    return True
            print("没有cookie")
        except:
            print(sys.exc_info())
        return False

    def respond_get(self):  # 响应get请求
        if self.need_login and (self.path.startswith("/home") or self.path == "/"):
            if self.judge_cookie():
                if self.path == "/":
                    print("已登录重定向")
                    self.send_response(302)
                    self.send_header("Location", "/home")
                    self.end_headers()
                    return None
            else:  # no cookie
                if self.path != "/":
                    print("未登录重定向00")
                    self.send_response(302)
                    self.send_header("Location", "/")
                    self.end_headers()
                    return None
        path = self.translate_path(self.path)
        print("respond_get path:", self.path, path)
        if path == None: return
        if os.path.isdir(path):
            # if not self.path.endswith('/'):
            #     print("重定向00")
            #     self.send_response(302)
            #     self.send_header("Location",path+"/")
            #     self.end_headers()
            #     return None
            return self.list_directory(path)
        print("not dir")
        f = None
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None

        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a)
        print(list)

        with open(os.path.join(Work_Path, "html/jamlistdir.html"), "r", encoding="utf-8") as hf:
            listdir_html_str = hf.read()
        currentdir = html.escape(urllib.parse.unquote(self.path.replace("/home", "/")))
        print(currentdir)
        listdir_html_str = listdir_html_str.replace("{currentdir}", currentdir)

        if self.canupload:
            listdir_html_str = listdir_html_str.replace("<!--canupload", "")
        if not self.need_login:
            listdir_html_str = listdir_html_str.replace('value="退出登录"', 'value="退出登录" hidden')
        tablestr = ""
        for name in list:
            fullname = os.path.join(path, name)
            colorName = displayname = linkname = name
            if os.path.isdir(fullname):
                colorName = '<span style="color: #fc8a18;font-size: 16px;">' + name + '</span>'
                linkname = name + "/"
            if os.path.islink(fullname):
                colorName = '<span style="color: #ec0505;font-size: 16px;">' + name + '.lnk</span>'
            checkboxstr = '<td width="2%%"><input type="checkbox"  name="checkboxitems" id="{}" /></td>' \
                .format(urllib.parse.quote(os.path.join(currentdir, linkname))) if not os.path.isdir(
                fullname) else '<td width="2%%"></td>'
            downloadbtstr = '<td width="2%%"><a href="{}" download=""><input type="image" src=jamhtmlpic/jamdowload.png style="border: 0;width:16px;height:16px;" /></a></td>' \
                .format(urllib.parse.quote(linkname)) if not os.path.isdir(fullname) else '<td width="2%%"></td>'
            if len(self.limitpath) == 0 or (len(self.limitpath) > 0 and name in self.limitpath):
                tablestr += '<tr>\n' \
                            '{}' \
                            '<td width="50%%"><a href="{}" {}>{}</a></td>\n' \
                            '{}' \
                            '<td width="15%%">{}</td><td width="25%%">{}</td>\n' \
                            '</tr>\n' \
                    .format(checkboxstr,
                            urllib.parse.quote(linkname),
                            'target="_blank"' if not os.path.isdir(fullname) else "",
                            colorName, downloadbtstr,
                            sizeof_fmt(os.path.getsize(fullname)) if not os.path.isdir(fullname) else "文件夹",
                            modification_date(fullname))
                # print(urllib.parse.quote(os.path.join(currentdir,linkname)))
            else:
                print("{} not in list".format(name))
        if tablestr == "":  tablestr = "该目录下没有文件!"
        listdir_html_str = listdir_html_str.replace("{dirlist}", tablestr)
        f = StringIO()
        f.write(listdir_html_str)
        f.seek(0)
        length = len(f.read().encode())
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = [_f for _f in words if _f]

        if self.path == "/":
            if self.need_login:
                return os.path.join(Work_Path, "html/index.html")
            else:
                print("重定向")
                self.send_response(302)
                self.send_header("Location", self.path + "home/")
                self.end_headers()
                return None
        else:
            for word in words:
                if word in ["jamcss", "jamjs", "jamhtmlpic", "jamlistdir.html", "favicon.ico"] or (
                        word == "jamupload.html" and self.canupload):
                    print(os.path.join(Work_Path, "html/" + word + path.split(word)[1]))
                    p = os.path.join(Work_Path, "html/" + word + path.split(word)[1])
                    return p
        if "home" == words[0]:
            print("取根目录")
            words.pop(0)
        p = self.pathm
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            p = os.path.join(p, word)
        # print("test path", path)
        return p

    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init()  # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream',  # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
    })


class ThreadingServer(ThreadingMixIn, http.server.HTTPServer):
    pass


class WebFilesTransmitter_infolabel(QLabel):
    showm_signal = pyqtSignal(str)

    def __init__(self, parent: QGroupBox):
        super().__init__(parent)
        self.sharepath = "请先选择要共享的文件"
        self.ip = ""
        self.port = ""
        self.url = ""
        self.setWordWrap(True)
        self.qrcode_label = QLabel(self)
        self.qrcode_label.setGeometry(270, 0, 180, 180)
        pix = QPixmap(200, 200)
        pix.fill(QColor(255, 255, 255))
        self.qrcode_label.setPixmap(pix)
        self.whatbtn = QPushButton(QIcon(":/why.png"), "", self)
        self.whatbtn.setGeometry(80, 100, 20, 20)
        self.whatbtn.setStyleSheet("border-radius:10px")
        self.whatbtn.setToolTip("共享文件后每个网卡都有一个链接和对应的二维码,\n选择要访问的设备网络所在的适配器即可生成对应的链接(和二维码),\n通过访问该链接(二维码)可访问共享文件夹\n"
                                "如:A设备共享了一个文件,通过打开电脑的热点让手机连接上了,\n则可以通过选择网络适配器为本地连接xxx字样(对应电脑热点适配器)生成链接,\n即可通过访问该链接或扫描二维码从网页端访问共享文件了\n"
                                "注意:共享文件为全网段共享,即使没有选择对应的网络适配器,该网段仍然可以通过ip+端口的方式访问!\n"
                                "所以不选择网络适配器生成链接而直接用ip+端口形式访问也是可的\n选择网络适配器只是为了方便输入(复制粘贴/扫码)而已...")
        self.copy_qrcode_btn = QPushButton("复制二维码", self)
        self.copy_qrcode_btn.move(320, 180)
        self.copy_qrcode_btn.clicked.connect(self.copy_qrcode)
        self.copy_url_btn = QPushButton("复制链接", self)
        self.copy_url_btn.move(180, 100)
        self.copy_url_btn.clicked.connect(self.copy_url)
        self.open_url_btn = QPushButton("打开链接", self)
        self.open_url_btn.move(110, 100)
        self.open_url_btn.clicked.connect(self.open_url)
        self.update()

        # self.setOpenExternalLinks(True)
        # self.urledit = QTextBrowser(self)
        # self.urledit.setHtml('<a href="http://172.30.84.32:20174/">http://172.30.84.32:20174/</a>')

    def open_url(self):
        QDesktopServices.openUrl(QUrl(self.url))
        print("打开链接", self.url)

    def copy_qrcode(self):
        pix = self.qrcode_label.pixmap()
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(pix)
        print("二维码已复制到剪切板")
        self.showm_signal.emit("二维码已复制到剪切板")

    def copy_url(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.url)
        print("链接已复制到剪切板")
        self.showm_signal.emit("链接已复制到剪切板")

    def get_qrcode(self, url):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(str(url))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        pix = ImageQt.toqpixmap(img)
        self.qrcode_label.setPixmap(pix.scaled(self.qrcode_label.width(), self.qrcode_label.height()))

        # img.save()

    def set_info(self, sharepath="请先选择要共享的文件", ip="", port=0000):
        self.sharepath = sharepath
        self.ip = ip
        self.port = port
        self.url = "http://{}:{}".format(self.ip, self.port)
        # self.urledit.setHtml('<a href="{}">link</a>'.format(self.url))
        self.get_qrcode(self.url)
        self.update()
        QApplication.processEvents()
        print(self.url)

    def paintEvent(self, e) -> None:
        super(WebFilesTransmitter_infolabel, self).paintEvent(e)
        painter = QPainter(self)
        s = 50
        d = 23
        painter.drawText(5, s - 30, "共享路径:")
        painter.drawText(5, s - 12, "{}".format(self.sharepath))
        painter.drawText(5, s + d, "网络适配器:")
        painter.drawText(5, s + d * 2, "IP:{}  端口:{}".format(self.ip, self.port))
        painter.drawText(5, s + d * 3, "链接:")
        painter.drawText(5, s + d * 4 - 5, "{}".format(self.url))
        painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
        painter.drawText(5, s + d * 4, 240, 200, Qt.TextWordWrap,
                         "请确保设备处于同一网段中,通过浏览器访问上述链接或扫描右侧二维码访问共享文件")

        painter.end()


class serverloghandle(QThread):
    showm_signal = pyqtSignal(str)

    def __init__(self):
        super(serverloghandle, self).__init__()
        self.q = q
        self.servering = True
        self.iplist = []

    def run(self) -> None:
        self.servering = True
        olddir = ""
        while self.servering:
            if not self.q.empty():
                log = self.q.get()
                ip = log["ip"]
                actiontime = log["time"].split()[1]
                # if ip not in self.iplist:
                #     self.iplist.append(ip)
                #     self.showm_signal.emit("{}正在访问你的共享文件\n{}".format(ip, actiontime))
                # print("action", log["action"])
                # if type(log["action"][0]) == str and log["action"][1] == "200":
                #     if "get" in log["action"][0].lower():
                #         getfile = urllib.parse.unquote(log["action"][0].split()[1])
                #         if getfile[-1] == "/":
                #             print("正在访问:", getfile)
                #             if getfile != olddir:
                #                 olddir = getfile
                #                 self.showm_signal.emit("{}正在访问{}\nat{}".format(ip, getfile, actiontime))
                #         else:
                #             print("下载了", getfile)
                #             self.showm_signal.emit("{}下载了一个文件:\n{}\nat{}".format(ip, getfile, actiontime))
                #     elif "post" in log["action"][0].lower():
                #         self.showm_signal.emit("{}上传了一个文件到共享文件夹\nat{}".format(ip, actiontime))

            time.sleep(0.1)

    def quit(self) -> None:
        self.servering = False
        super(serverloghandle, self).quit()


class WebFilesTransmitter(QThread):
    # start_btn_ss_signal = pyqtSignal(str)
    showm_signal = pyqtSignal(str)

    def __init__(self):
        super(WebFilesTransmitter, self).__init__()
        self.port = QSettings('Fandes', 'jamtools').value("webtransmitterport", random.randint(6048, 65530), type=int)
        QSettings('Fandes', 'jamtools').setValue("webtransmitterport", self.port)
        print("端口:", self.port)
        self.canupload = False
        self.need_login = True
        self.limitpath = []
        self.ip = ""
        self.sharepath = "请先选择要共享的文件"
        self.devicedict = {}

        self.sharing = False

    def run(self) -> None:
        print("start server")
        self.http_handler = SimpleHTTPRequestHandler
        serverlog = serverloghandle()
        serverlog.showm_signal.connect(self.tranformshowmsignal)
        serverlog.start()
        try:
            self.threadingServer = ThreadingServer(("", self.port), self.http_handler)
        except:
            print(sys.exc_info())
            self.resetport()
        if self.sharepath == "请先选择要共享的文件":
            print("未选择要共享的文件!")
            self.showm_signal.emit("未选择要共享的文件!")
            return
        self.sharing = True
        self.showm_signal.emit("已共享文件(夹):{}\n如需访问请将其他设备连接到同一局域网,使用相应IP:端口的形式从浏览器访问即可".format(self.sharepath))
        self.http_handler.canupload = self.canupload
        self.http_handler.need_login = self.need_login
        self.http_handler.limitpath = self.limitpath

        for ip in self.devicedict.values():
            print("http://" + str(ip) + ":" + str(self.port))
        self.threadingServer.serve_forever()
        serverlog.quit()

        self.showm_signal.emit("已结束文件(夹)的共享")
        self.sharing = False
        print("exit server")

    def tranformshowmsignal(self, s):
        self.showm_signal.emit(s)

    def get_alldevices(self):

        dv = QNetworkInterface.allInterfaces()
        availabledevices = {interface.humanReadableName(): interface.addressEntries()[-1].ip().toString() for interface in dv if
                  (not interface.addressEntries()[-1].ip().isLinkLocal()and interface.addressEntries()[-1].ip().toString()!="127.0.0.1")}

        self.devicedict = {k: v for k, v in sorted(availabledevices.items(), key=lambda item: item[1], reverse=True)}
        print(self.devicedict)

        return self.devicedict

    def change_SHOWPATH(self, path):
        global SHOW_PATH
        print("share path change to ", path)
        SHOW_PATH = path
        self.sharepath = path

    def show_a_dir(self, dir, canupload=False, need_login=True):
        if os.path.isdir(dir):
            try:
                self.limitpath = self.http_handler.limitpath = []
                self.canupload = self.http_handler.canupload = canupload
                self.need_login = self.http_handler.need_login = need_login
            except AttributeError:
                self.limitpath = []
                self.canupload = canupload
                self.need_login = need_login
            self.change_SHOWPATH(dir)
            if self.sharing:
                self.showm_signal.emit("已立即更换共享路径为:{}".format(dir))
            # self.start()

    def show_some_files(self, filelist=None, canupload=False, need_login=True):
        if len(filelist) > 0:
            self.limitpath = [os.path.split(p)[1] for p in filelist]
            self.canupload = canupload
            self.need_login = need_login
            try:
                self.http_handler.limitpath = [os.path.split(p)[1] for p in filelist]
                self.http_handler.canupload = canupload
                self.http_handler.need_login = need_login
            except:
                print(sys.exc_info())

            self.change_SHOWPATH(os.path.split(filelist[0])[0])
            if self.sharing:
                self.showm_signal.emit("已立即更换共享文件为" + str(filelist))
            # self.start()

    def stop_server(self):
        try:
            if self.sharing:
                self.threadingServer.shutdown()
        except:
            print(sys.exc_info(), 529, "transmitter")
        self.quit()


class WebFilesTransmitterBox(QGroupBox):
    showm_signal = pyqtSignal(str)

    def __init__(self, WebFilesTransmitter: WebFilesTransmitter, text="", parent=None):
        super(WebFilesTransmitterBox, self).__init__(text, parent)
        self.WebFilesTransmitter = WebFilesTransmitter
        self.transmitter_web_start_btn = QPushButton("开始共享", self)
        self.transmitter_web_start_btn.setGeometry(5, 22, 80, 28)
        self.transmitter_web_start_btn.clicked.connect(self.changeshare)
        # self.WebFilesTransmitter.start_btn_ss_signal.connect(self.transmitter_web_start_btn.setStyleSheet)
        self.transmitter_reset_web_port_btn = QPushButton("重置端口", self)
        self.transmitter_reset_web_port_btn.setGeometry(self.transmitter_web_start_btn.x(),
                                                        self.transmitter_web_start_btn.y() + self.transmitter_web_start_btn.height() + 10,
                                                        self.transmitter_web_start_btn.width(),
                                                        self.transmitter_web_start_btn.height())
        self.transmitter_reset_web_port_btn.clicked.connect(self.resetport)
        self.transmitter_reset_web_port_btn.setToolTip("重置端口并重启服务,此前的链接将不可以!")
        self.transmitter_web_allowupload = QCheckBox("允许上传", self)
        self.transmitter_web_allowupload.setToolTip("允许网页端上传文件,文件将保存于共享的文件夹内")
        self.transmitter_web_allowupload.setStatusTip("允许网页端上传文件,文件将保存于共享的文件夹内")
        self.transmitter_web_allowupload.setChecked(
            QSettings('Fandes', 'jamtools').value('transmitter/allowupload', False, type=bool))
        self.transmitter_web_allowupload.move(self.transmitter_reset_web_port_btn.x() + 2,
                                              self.transmitter_reset_web_port_btn.y() + self.transmitter_reset_web_port_btn.height() + 15)

        def allowuploadchange(a):
            try:
                self.WebFilesTransmitter.http_handler.canupload = True if a else False
            except:
                pass
            self.WebFilesTransmitter.canupload = True if a else False
            QSettings('Fandes', 'jamtools').setValue('transmitter/allowupload',
                                                     self.transmitter_web_allowupload.isChecked())
            if self.WebFilesTransmitter.sharing:
                self.showm_signal.emit("已{}网页端文件上传".format("允许" if a else "禁止"))

        self.transmitter_web_allowupload.stateChanged.connect(allowuploadchange)

        self.transmitter_web_need_login = QCheckBox("需要密码", self)
        self.transmitter_web_need_login.setToolTip("需要先登录")
        self.transmitter_web_need_login.setStatusTip("需要先用密码登录")
        self.transmitter_web_need_login.move(self.transmitter_web_allowupload.x(),
                                             self.transmitter_web_allowupload.y() + self.transmitter_web_allowupload.height() + 5)

        def need_loginchange(a):
            try:
                self.WebFilesTransmitter.http_handler.need_login = True if a else False
            except:
                pass
            self.WebFilesTransmitter.need_login = True if a else False
            self.transmitter_web_need_login.setChecked(a)
            self.transmitter_web_need_login_label.setVisible(bool(a))
            QSettings('Fandes', 'jamtools').setValue('transmitter/need_login',
                                                     self.transmitter_web_need_login.isChecked())

        self.transmitter_web_need_login.stateChanged.connect(need_loginchange)
        self.transmitter_web_need_login_label = QLineEdit(self)
        self.transmitter_web_need_login_label.setGeometry(self.transmitter_web_need_login.x(),
                                                          self.transmitter_web_need_login.y() + self.transmitter_web_need_login.height() - 10,
                                                          self.transmitter_web_need_login.width() - 10, 25)
        self.transmitter_web_need_login_label.setPlaceholderText("1234")
        self.transmitter_web_need_login_label.textChanged.connect(
            lambda x: QSettings('Fandes', 'jamtools').setValue('transmitter/login_password', x if len(x) else "1234"))
        self.transmitter_web_need_login_label.setText(
            QSettings('Fandes', 'jamtools').value('transmitter/login_password',
                                                  "1234"))
        need_loginchange(QSettings('Fandes', 'jamtools').value('transmitter/need_login', True, type=bool))
        self.transmitter_web_info = WebFilesTransmitter_infolabel(self)
        self.transmitter_web_info.showm_signal.connect(self.showm_signal.emit)
        self.transmitter_web_info.setGeometry(
            self.transmitter_web_start_btn.x() + self.transmitter_web_start_btn.width() + 15,
            self.transmitter_web_start_btn.y(),
            500, 200)
        print(self.transmitter_web_info.isVisible(), self.transmitter_web_info.size(), 500, "vis")

        def choicefiles():
            files, l = QFileDialog.getOpenFileNames(self, "选择要共享的文件", "", "all files(*.*);;")
            print(files)
            if len(files):
                self.WebFilesTransmitter.show_some_files(files, self.transmitter_web_allowupload.isChecked(),
                                                         self.transmitter_web_need_login.isChecked())
                self.transmitter_web_info.sharepath = os.path.split(files[0])[0] + "/{}个文件".format(len(files))
                QSettings('Fandes', 'jamtools').setValue('transmitter/sharepath', os.path.split(files[0])[0])

        def choicedir():
            dir = QFileDialog.getExistingDirectory(self, "选择要共享的文件夹", "")
            print(dir)
            if len(dir):
                self.WebFilesTransmitter.show_a_dir(dir, self.transmitter_web_allowupload.isChecked(),
                                                    self.transmitter_web_need_login.isChecked())
                self.transmitter_web_info.sharepath = dir
                QSettings('Fandes', 'jamtools').setValue('transmitter/sharepath', dir)

        self.transmitter_web_choice_files = QPushButton("选择文件", self)
        self.transmitter_web_choice_files.clicked.connect(choicefiles)
        self.transmitter_web_choice_files.setToolTip("选择一个文件夹内的多个文件共享")
        self.transmitter_web_choice_files.setStatusTip("选择一个文件夹内的多个文件共享")
        self.transmitter_web_choice_dir = QPushButton("选择文件夹", self)
        self.transmitter_web_choice_dir.clicked.connect(choicedir)
        self.transmitter_web_choice_dir.setToolTip("选择一个文件夹,共享整个文件夹包括其子文件夹")
        self.transmitter_web_choice_dir.setStatusTip("选择一个文件夹,共享整个文件夹包括其子文件夹")
        self.transmitter_web_choice_files.setGeometry(280, 20, 80, 23)
        self.transmitter_web_choice_dir.setGeometry(self.transmitter_web_choice_files.x(),
                                                    self.transmitter_web_choice_files.y() + self.transmitter_web_choice_files.height(),
                                                    self.transmitter_web_choice_files.width(),
                                                    self.transmitter_web_choice_files.height())
        self.transmitter_web_devices = QComboBox(self)
        self.transmitter_web_devices.setGeometry(190, 80, 140, 23)
        self.transmitter_web_devices.setToolTip("请选择要生成链接的网卡,设备需要连入共同网段才可访问共享文件,\n"
                                                "例如:本机已通过以太网连入校园网时,可选择以太网适配器生成链接和二维码,\n"
                                                "另一台已经连入该校园网的设备就可以通过链接或扫描二维码访问共享文件")
        self.transmitter_web_devices.setStatusTip("多网卡用户请选择要生成链接的网卡,设备需要连入共同网段才可访问共享文件")
        self.transmitter_web_devices.currentTextChanged.connect(
            lambda x: self.transmitter_web_info.set_info(self.WebFilesTransmitter.sharepath,
                                                         self.WebFilesTransmitter.devicedict[x],
                                                         self.WebFilesTransmitter.port) if x != "" else None)
        update_btn = QPushButton(QIcon(":/update.png"), "", self)
        update_btn.setToolTip("刷新设备,如改变了wifi/移动热点请刷新一下以获取正确的链接")
        update_btn.setGeometry(self.transmitter_web_devices.x() + self.transmitter_web_devices.width() + 5,
                               self.transmitter_web_devices.y(), 20, 20)
        update_btn.clicked.connect(self.updatedevice)
        d = QSettings('Fandes', 'jamtools').value('transmitter/sharepath', "")
        if d != "":
            self.WebFilesTransmitter.show_a_dir(d, self.transmitter_web_allowupload.isChecked(),
                                                self.transmitter_web_need_login.isChecked())
            self.transmitter_web_info.sharepath = d

    def changeshare(self):
        if self.transmitter_web_info.sharepath == "请先选择要共享的文件":
            self.showm_signal.emit("未选择要共享的路径/文件!")
            print("未选择要共享的路径")
            return
        if self.WebFilesTransmitter.sharing:
            print("停止共享")
            self.transmitter_web_start_btn.setStyleSheet("QPushButton{background-color:rgb(239,239,239);}")
            self.transmitter_web_start_btn.setText("开始共享")
            self.WebFilesTransmitter.stop_server()
        else:
            self.transmitter_web_start_btn.setStyleSheet("QPushButton{background-color:rgb(255,50,50);}")
            self.transmitter_web_start_btn.setText("结束共享")
            self.WebFilesTransmitter.start()
            print("开始共享")

    def resetport(self):
        sharing = self.WebFilesTransmitter.sharing
        if sharing:
            try:
                self.changeshare()
            except:
                print(sys.exc_info())
        self.WebFilesTransmitter.port = random.randint(6048, 65530)
        QSettings('Fandes', 'jamtools').setValue("webtransmitterport", self.WebFilesTransmitter.port)
        if sharing:
            self.WebFilesTransmitter.wait()
            self.changeshare()
        self.updatedevice()

    def updatedevice(self):
        self.transmitter_web_devices.clear()
        self.transmitter_web_devices.addItems(self.WebFilesTransmitter.get_alldevices().keys())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    web = WebFilesTransmitter()
    webtransmitterbox = WebFilesTransmitterBox(web, "通过网页传输")
    webtransmitterbox.updatedevice()
    webtransmitterbox.show()
    sys.exit(app.exec_())
