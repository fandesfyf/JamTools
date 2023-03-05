# -*- coding: utf-8 -*-
# @Author  : Fandes
import random
import requests
import sys
import hashlib
import http.client
from urllib.parse import quote

from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QStandardPaths, QTimer, QSettings, QFileInfo, \
    QUrl, QObject, QSize
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont, QImage, QTextCursor, QColor, QDesktopServices, QMovie
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QToolTip, QAction, QTextEdit, QLineEdit, \
    QMessageBox, QFileDialog, QMenu, QSystemTrayIcon, QGroupBox, QComboBox, QCheckBox, QSpinBox, QTabWidget, \
    QDoubleSpinBox, QLCDNumber, QScrollArea, QWidget, QToolBox, QRadioButton, QTimeEdit, QListWidget, QDialog, \
    QProgressBar, QTextBrowser
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from threading import Thread
from jampublic import get_UserAgent

class Translator(QObject):
    result_signal = pyqtSignal(str,str,str)#result,from_lan,to_lan
    status_signal = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__()
        self.fromLang = '自动检测'
        self.toLang = '中文'
        self.engine = "YouDao"
        self.parent = parent
        self.text = ' '
        self.thread = None
        #支持的引擎:百度BaiDu,有道Youdao
        bd_lang_dict = {'自动检测': 'auto', '中文': 'zh', '英语': 'en', '文言文': 'wyw', '粤语': 'yue', '日语': 'jp', '德语': 'de',
                     '韩语': 'kor',
                     '法语': 'fra', '俄语': 'ru', '泰语': 'th', '意大利语': 'it', '葡萄牙语': 'pt', '西班牙语': 'spa'}
        yd_lang_dict = {'自动检测': 'AUTO', '中文': 'ZH_CN', '英语': 'EN', '日语': 'JA','韩语': 'KR','法语': 'FR', 
                        '俄语': 'RU', '西班牙语': 'SP'}
        self.translate_engine_info = {"YouDao":yd_lang_dict,
                                      "BaiDu":bd_lang_dict}
        
    def get_available_langs(self,engine="YouDao"):
        return list(self.translate_engine_info[engine].keys())
    
    def translate(self,text,from_lang = '自动检测',to_lang = "中文",engine = "YouDao"):
        pl={"YouDao":self.Youdaotra,
            "BaiDu":self.Bdtra}
        if engine in pl:
            self.fromLang = from_lang
            self.toLang = to_lang
            self.engine = engine
            self.text = text
            func = pl[engine]
            print("开始翻译")
            self.thread = Thread(target=func)
            self.thread.start()
            self.status_signal.emit("正在翻译...")
        else:
            print("调用错误")
            self.status_signal.emit("调用错误")
            
    def Youdaotra(self):
        try:
            headers = {"User-Agent":get_UserAgent()}
            mode_dict = self.translate_engine_info["YouDao"]
            if self.fromLang == "自动检测":
                mode = "AUTO"
            else:
                mode = mode_dict[self.fromLang]+"2"+mode_dict[self.toLang]
            
            url = "http://fanyi.youdao.com/translate?&doctype=json&type={}&i={}".format(mode,self.text)
            res = requests.get(url,headers=headers).json()
            print(res)
            result = res["translateResult"][0][0]["tgt"]
            result_type_dict = dict(zip(mode_dict.values(),mode_dict.keys()))
            from_lan,to_lan = res["type"].split("2")
            from_lan,to_lan = result_type_dict[from_lan],result_type_dict[to_lan]
            self.result_signal.emit(result,from_lan,to_lan)
            self.status_signal.emit("翻译完成!")
        except Exception as e:
            print(e,__file__)
            self.status_signal.emit("翻译失败!")
    
    def Bdtra(self):
        print('Bdtra翻译开始')
        try:
            mode_dict = self.translate_engine_info["BaiDu"]
            bd_tra = BaiduTranslate(self.text,mode_dict[self.fromLang],mode_dict[self.toLang])
            result = bd_tra.tra()
            if result is not None:
                result,from_lan,to_lan = result
                result_type_dict = dict(zip(mode_dict.values(),mode_dict.keys()))
                from_lan,to_lan = result_type_dict[from_lan],result_type_dict[to_lan]
                self.result_signal.emit(result,from_lan,to_lan)
                self.status_signal.emit("翻译完成!")
            else:
                raise Exception("识别结果错误")
        except Exception as e:
            print(e,__file__)
            self.status_signal.emit("翻译出错!")

    def get_lang(self):
        try:
            dictl = {'自动检测': 'auto', '中文': 'zh', '英语': 'en', '文言文': 'wyw', '粤语': 'yue', '日语': 'jp', '德语': 'de',
                     '韩语': 'kor',
                     '法语': 'fra', '俄语': 'ru', '泰语': 'th', '意大利语': 'it', '葡萄牙语': 'pt', '西班牙语': 'spa'}
            self.fromLang = dictl[self.fromLang]
            self.toLang = dictl[self.toLang]
        except:
            print('auto')

    def show_detal(self):
        self.get_lang()
        url = 'https://fanyi.baidu.com/#' + self.fromLang + '/' + self.toLang + '/' + self.text
        QDesktopServices.openUrl(QUrl(url))

class BaiduTranslate(QObject):
    resultsignal = pyqtSignal(str)
    showm_singal = pyqtSignal(str)
    change_item_signal = pyqtSignal(str)

    def __init__(self, text, from_lan, to_lan):
        super().__init__()
        self.text = text
        self.toLang = to_lan
        #由于被人恶意调用,我的百度翻译调用量已经用完,这个appid已经不可用了,可以将自己的appid在设置里面填入.
        self.appid = QSettings('Fandes', 'jamtools').value('tran_appid', '20190928000337891', str)
        self.secretKey = QSettings('Fandes', 'jamtools').value('tran_secretKey', 'SiNITAufl_JCVpk7fAUS', str)
        salt = str(random.randint(32768, 65536))
        sign = self.appid + self.text + salt + self.secretKey
        m1 = hashlib.md5()
        m1.update(sign.encode(encoding='utf-8'))
        sign = m1.hexdigest()
        q= quote(self.text)
        self.re_url = '/api/trans/vip/translate?appid=' + self.appid + '&q=' + q + '&from=' + from_lan + '&to={0}&salt=' + str(
            salt) + '&sign=' + sign
        self.geturl = self.re_url.format(self.toLang)
        # self.args={"sign": sign,"salt":salt, "appid": self.appid,"to": to_lan,"from":from_lan ,"q":q}

    def tra(self,replay = 3):

        if len(str(self.text).replace(" ", "").replace("\n", "")) == 0:
            print("空翻译")
            self.resultsignal.emit("没有文本!")
            return
        try:
            httpClient0 = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient0.request('GET', self.geturl)
            response = httpClient0.getresponse()
        except:
            print(sys.exc_info())
            self.showm_singal.emit("翻译出错！请确保网络畅通！{}".format(sys.exc_info()[0]))
        else:
            s = response.read().decode('utf-8')
            print(s)
            s = eval(s)
            text = ''
            # print(s)
            f_l = s['from']
            t_l = s['to']
            if f_l == t_l:
                if t_l == 'zh':
                    self.geturl = self.re_url.format('en')
                    try:
                        # jamtools.tra_to.setCurrentText('英语')
                        self.change_item_signal.emit("英语")
                    except:
                        print(sys.exc_info())
                else:
                    self.geturl = self.re_url.format('zh')
                    try:
                        self.change_item_signal.emit("中文")
                        # jamtools.tra_to.setCurrentText('中文')
                    except:
                        print(sys.exc_info())
                if replay > 0:
                    return self.tra(replay-1)
                else:
                    return None
            for line in s['trans_result']:
                temp = line['dst'] + '\n'
                text += temp
            return text,f_l,t_l
