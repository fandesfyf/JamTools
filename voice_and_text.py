import ast
import base64
import hashlib
import http.client
import random
import sys
import time
import urllib
import wave

import pyaudio
import requests
import speech_recognition as sr
from PyQt5.QtCore import QObject, pyqtSignal

from txpythonsdk import TxTest2Voice


class BdAsr:
    def __init__(self, faster=False):
        self.faster = faster

    def __get_response(self, host, method, url, body, headers):
        conn = http.client.HTTPSConnection(host)
        conn.request(method, url, body, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        return data

    # 获取token
    def __get_token(self, API_KEY='WeH4bNSdcDD029kgYHe6NcQf', SECRET_KEY='UToC7r2pCVIfBFZQGs23bNIgE0Ykm0UG',
                    GRANT_TYPE='client_credentials'):
        url = "/oauth/2.0/token?client_id=%s&client_secret=%s&grant_type=%s" % (API_KEY, SECRET_KEY, GRANT_TYPE)
        res = self.__get_response("openapi.baidu.com", 'POST', url, '', {})
        dict_data = ast.literal_eval(res)
        return dict_data.get('access_token')

    # 获取识别结果
    def get_result(self, audio_file="recording.wav", cuid='test', DEV_PID='80001'):
        access_token = self.__get_token()
        if type(audio_file) == bytes:
            body = audio_file
        else:
            with open(audio_file, 'rb') as speech_file:
                body = speech_file.read()
        if self.faster:
            url = "/pro_api?dev_pid=%s&cuid=%s&token=%s" % (DEV_PID, cuid, access_token)
            # 标准版也可通过http接口实现，改一下url和语言模型就好
            # 标准版的url
        else:
            url = "/server_api?dev_pid=%s&cuid=%s&token=%s" % (1537, cuid, access_token)
        headers = {
            'Content-Type': 'audio/pcm;rate=16000'
        }
        res = self.__get_response("vop.baidu.com", 'POST', url, body, headers)
        dict_data = ast.literal_eval(res)
        return dict_data.get('result')[0]


"""dev_pid	语言	模型	是否有标点	备注
1537	普通话(纯中文识别)	输入法模型	有标点	支持自定义词库
1737	英语		无标点	不支持自定义词库
1637	粤语		有标点	不支持自定义词库
1837	四川话		有标点	不支持自定义词库
1936	普通话远场	远场模型	有标点	不支持"""


class Voice2text(QObject):
    voice2text_signal = pyqtSignal(str, bool)
    recording2textsignal=pyqtSignal(str)
    def __init__(self):
        super(Voice2text, self).__init__()
        self.url = "https://api.ai.qq.com/fcgi-bin/aai/aai_asr"
        self.recorder = sr.Recognizer()
        self.recorder.non_speaking_duration = 0.2
        self.recorder.pause_threshold = 0.5
        self.bdasr = BdAsr()

    def __get_sign_code(self, params, app_key="TTkZvr74cJHQWQxR"):
        """ 生成签名CODE
        1. 计算步骤
        用于计算签名的参数在不同接口之间会有差异，但算法过程固定如下4个步骤。
        将<key, value>请求参数对按key进行字典升序排序，得到有序的参数对列表N
        将列表N中的参数对按URL键值对的格式拼接成字符串，得到字符串T（如：key1=value1&key2=value2），URL键值拼接过程value部分需要URL编码，URL编码算法用大写字母，例如%E8，而不是小写%e8
        将应用密钥以app_key为键名，组成URL键值拼接到字符串T末尾，得到字符串S（如：key1=value1&key2=value2&app_key=密钥)
        对字符串S进行MD5运算，将得到的MD5值所有字符转换成大写，得到接口请求签名
        2. 注意事项
        不同接口要求的参数对不一样，计算签名使用的参数对也不一样
        参数名区分大小写，参数值为空不参与签名
        URL键值拼接过程value部分需要URL编码
        签名有效期5分钟，需要请求接口时刻实时计算签名信息
        :param params: 参数字典
        :param app_key:
        :return:
        """
        if params is None or type(params) != dict or len(params) == 0: return
        try:
            params = sorted(params.items(), key=lambda x: x[0])
            _str = ''
            for item in params:
                key = item[0]
                value = item[1]
                if value == '': continue
                _str += urllib.parse.urlencode({key: value}) + '&'
            _str += 'app_key=' + app_key
            _str = hashlib.md5(_str.encode('utf-8')).hexdigest()
            return _str.upper()
        except Exception as e:
            print(e)

    def recording(self, rate=16000, timeout=None):
        with sr.Microphone(sample_rate=rate) as source:
            self.recorder.adjust_for_ambient_noise(source, 0.8)
            print("环境噪声阈值：", self.recorder.energy_threshold)
            print("please say something")
            self.recording2textsignal.emit("recording")
            audio = self.recorder.listen(source, timeout=timeout)

        print("end recording")
        # with open("recording.wav", "wb") as f:
        #     f.write(audio.get_wav_data())
        return audio.get_wav_data()

    def file_to_base64(self, speech):
        with open(speech, 'rb')as file:
            s = file.read()
            b64 = base64.b64encode(s)
        return b64

    def __get_random_str(self, n=17):
        s = "qwertyuiop7894561230asdfghjklzxcvbnm"
        rs = ''
        for i in range(n):
            rs += s[random.randint(0, 35)]
        return rs

    def record2text(self, Bd=True, timeout=None):
        st = time.time()
        try:
            voice_bytes_ = self.recording(timeout=timeout)
            self.recording2textsignal.emit("endrecordinggettingtext")
            if Bd:
                text = self.bdasr.get_result(voice_bytes_)
            else:
                text = self.tx_get_text_from_recording(voice_bytes_)
            print("转文本时间", time.time() - st, "内容", text)
            if len(text.replace(" ", "")) == 0:
                text = "听不到任何声音"
            self.recording2textsignal.emit("gettext"+text)
            self.voice2text_signal.emit(text, True)
            return text
        except:
            print("出现错误,voice and text.pyn l154",sys.exc_info())
            self.recording2textsignal.emit("endrecording")
            self.voice2text_signal.emit("听不到任何声音", True)
            return "听不到任何声音"

    def tx_get_text_from_recording(self, voice, format=2):
        t1 = time.time()
        if type(voice) == bytes:
            speech = base64.b64encode(voice)
        else:
            speech = self.file_to_base64(voice)
        t2 = time.time()
        params = {"app_id": 2154786206,
                  "time_stamp": int(time.time()),
                  "nonce_str": self.__get_random_str(),
                  "format": format,
                  "speech": speech
                  }
        params["sign"] = self.__get_sign_code(params)
        t3 = time.time()
        response = requests.post(self.url, data=params)
        print(time.time() - t3, t3 - t2, t2 - t1)
        js = response.json()

        text = js['data']['text']
        print(text)
        return text
        # audiobase64 = js["data"]["speech"]
        # audio = base64.b64decode(audiobase64)
        # with open("temp.wav", 'wb') as f:
        #     f.write(audio)
        #     f.close()


class Text2voice:
    def __init__(self):
        self.url = r"https://api.ai.qq.com/fcgi-bin/aai/aai_tts"
        self.text2voice = TxTest2Voice()

    def __get_sign_code(self, params, app_key="TTkZvr74cJHQWQxR"):
        """ 生成签名CODE
        1. 计算步骤
        用于计算签名的参数在不同接口之间会有差异，但算法过程固定如下4个步骤。
        将<key, value>请求参数对按key进行字典升序排序，得到有序的参数对列表N
        将列表N中的参数对按URL键值对的格式拼接成字符串，得到字符串T（如：key1=value1&key2=value2），URL键值拼接过程value部分需要URL编码，URL编码算法用大写字母，例如%E8，而不是小写%e8
        将应用密钥以app_key为键名，组成URL键值拼接到字符串T末尾，得到字符串S（如：key1=value1&key2=value2&app_key=密钥)
        对字符串S进行MD5运算，将得到的MD5值所有字符转换成大写，得到接口请求签名
        2. 注意事项
        不同接口要求的参数对不一样，计算签名使用的参数对也不一样
        参数名区分大小写，参数值为空不参与签名
        URL键值拼接过程value部分需要URL编码
        签名有效期5分钟，需要请求接口时刻实时计算签名信息
        :param params: 参数字典
        :param app_key:
        :return:
        """
        if params is None or type(params) != dict or len(params) == 0: return
        try:
            params = sorted(params.items(), key=lambda x: x[0])
            _str = ''
            for item in params:
                key = item[0]
                value = item[1]
                if value == '': continue
                _str += urllib.parse.urlencode({key: value}) + '&'
            _str += 'app_key=' + app_key
            _str = hashlib.md5(_str.encode('utf-8')).hexdigest()
            return _str.upper()
        except Exception as e:
            print(e)

    def __get_random_str(self, n=17):
        s = "qwertyuiop7894561230asdfghjklzxcvbnm"
        rs = ''
        for i in range(n):
            rs += s[random.randint(0, 35)]
        return rs

    def get_voice_and_paly_it(self, text, voicetype=101001, volume=10):
        bytes_ = self.text2voice.get_voice_from_text(text, voicetype, volume)
        # if not isman:
        #     speaker = 6
        # text = text.replace("~", ' ')
        # text = text.encode('utf-8')
        # if len(text) >= 150:
        #     print("字符超出", len(text))
        #     print("too long")
        #     return
        # elif text == '':
        #     print("空字符")
        #     return
        # params = {"app_id": 2154786206,
        #           "time_stamp": int(time.time()),
        #           "nonce_str": self.__get_random_str(),
        #           "speaker": speaker,
        #           "format": format,
        #           "volume": volume,
        #           "speed": speed,
        #           "text": text,
        #           "aht": aht,
        #           "apc": apc
        #           }
        # params["sign"] = self.__get_sign_code(params)
        # print(params)
        # response = requests.get(self.url, params=params)
        # js = response.json()
        # # print(js, "get_voice_and_paly_it")
        # audiobase64 = js["data"]["speech"]
        # audio = base64.b64decode(audiobase64)
        # print("ypcd", len(audio))
        # with open("rec_to_textfunctemp.wav", 'wb') as f:
        #     f.write(audiobytes)
        #     f.flush()
        self.play_bytes(bytes_)

    def play_bytes(self, voice_bytes):
        self.palyer = pyaudio.PyAudio()
        print("divicecount", self.palyer.get_device_count())
        stream = self.palyer.open(format=self.palyer.get_format_from_width(2),
                                  channels=1,
                                  rate=16000,
                                  output=True)
        stream.write(voice_bytes)
        # CHUNK = 1024
        # while voice_bytes:
        #     data = voice_bytes[:CHUNK]
        #     stream.write(data)
        #     voice_bytes = voice_bytes[CHUNK:]

        stream.stop_stream()
        stream.close()

    def play(self, file="rec_to_textfunctemp.wav"):
        CHUNK = 1024
        wf = wave.open(file, "rb")
        self.palyer = pyaudio.PyAudio()
        print("divicecount", self.palyer.get_device_count())
        stream = self.palyer.open(format=self.palyer.get_format_from_width(2),
                                  channels=1,
                                  rate=16000,
                                  output=True)

        data = wf.readframes(CHUNK)

        while len(data):
            stream.write(data)
            data = wf.readframes(CHUNK)

        stream.stop_stream()
        stream.close()


if __name__ == '__main__':
    # text = "你好啊 示例数据1000000001,redis"
    txt2vo = Text2voice()
    txt2vo.get_voice_and_paly_it("我在")
    # txt2vo.play(r'D:\python_work\Ar_project\voicecontrollermodel\rec_to_textfunctemp2.wav')
    #voicetotxt = Voice2text()
    #voicetotxt.record2text()

    # voicetotxt.tx_get_text_from_recording(r'F:\音乐\jam_audio\t2020-07-20_22.17.49.WAV')
    # if __name__ == '__main__':
    # f = BdAsr()
    # rs = f.get_result()
    # print(rs)
"""参数名称	是否必选	数据类型	数据约束	示例数据	描述
app_id	是	int	正整数	1000001	应用标识（AppId）
time_stamp	是	int	正整数	1493468759	请求时间戳（秒级）
nonce_str	是	string	非空且长度上限32字节	fa577ce340859f9fe	随机字符串
sign	是	string	非空且长度固定32字节		签名信息，详见接口鉴权
speaker	是	int	正整数	1	语音发音人编码，定义见下文描述
format	是	int	正整数	2	合成语音格式编码，定义见下文描述
volume	是	int	[-10, 10]	0	合成语音音量，取值范围[-10, 10]，如-10表示音量相对默认值小10dB，0表示默认音量，10表示音量相对默认值大10dB
speed	是	int	[50, 200]	100	合成语音语速，默认100
text	是	string	UTF-8编码，非空且长度上限150字节	腾讯，你好！	待合成文本
aht	是	int	[-24, 24]	0	合成语音降低/升高半音个数，即改变音高，默认0
apc	是	int	[0, 100]	58	控制频谱翘曲的程度，改变说话人的音色，默认58"""

"""
base64编码
with open("D:\\redis.png", 'rb') as f:
    encode_img = base64.b64encode(f.read())
    file_ext = os.path.splitext("D:\\redis.png")[1]
    print('data:image/{};base64,{}'.format(file_ext[1:], encode_img.decode()))
    f.close()
解码
with open("D:\\redis2.png", 'wb') as f:
    f.write(base64.b64decode(encode_img))
    f.close()
"""
