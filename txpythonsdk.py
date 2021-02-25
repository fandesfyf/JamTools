import base64
import os
import random
import wave

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tts.v20190823 import tts_client, models


class TxTest2Voice:
    def __init__(self):
        cred = credential.Credential("AKIDLWyFKBsNhw0jInuFD1g9YlnjU4QWqTK0", "hDYhFbs0uc8YmndeU9aqvpbCZlmbFtsf")

        # 实例化一个 http 选项，可选的，没有特殊需求可以跳过。
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tts.tencentcloudapi.com"

        # 实例化一个 client 选项，可选的，没有特殊需求可以跳过。
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        # 实例化要请求产品 (以 cvm 为例) 的 client 对象，clientProfile 是可选的。
        self.client = tts_client.TtsClient(cred, "ap-guangzhou", clientProfile)

        self.req = models.TextToVoiceRequest()

    def get_voice_from_text(self, text: str, voicetype=101001, volume=10, save_name=None):
        # 实例化一个 cvm 实例信息查询请求对象,每个接口都会对应一个 request 对象。

        params = '{"Text":"text","SessionId":"sessionid","ModelType":1,' \
                 '"Codec":"wav","VoiceType":type,"Volume":volume}'.replace("text", text).replace("sessionid",
                                                                                                 str(random.randint(
                                                                                                     1000, 9999))) \
            .replace("type", str(voicetype)).replace("volume", str(volume))
        print(params)
        self.req.from_json_string(params)

        # 通过 client 对象调用 DescribeInstances 方法发起请求。注意请求方法名与请求对象是对应的。
        # 返回的 resp 是一个 DescribeInstancesResponse 类的实例，与请求对象对应。
        resp = self.client.TextToVoice(self.req)
        # print(resp)
        b = base64.b64decode(resp.Audio)
        pos = b.find("data".encode())
        b = b[pos + 6:]

        if save_name is not None:
            f = wave.open(save_name, "wb")
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(16000)
            f.writeframes(b)
            f.close()
        return b
        # print(len(resp.Audio))
        # with open("1{}.wav".format(random.randint(1, 55)), "wb")as f:
        #     f.write(base64.b64decode(resp.Audio))


if __name__ == '__main__':
    a = TxTest2Voice()

    voices = {"亲和女声": 0, "亲和男声": 1, "成熟男声": 2, "温暖女声": 4, "情感女声": 5, "情感男声": 6, "客服女声": 7,
              "智侠|情感男声": 1000, "智瑜|情感女声": 1001, "智聆|通用女声": 1002, "智美|客服女声": 1003, "WeJack|英文男声": 1050,
              "WeRose|英文女声": 1051,
              "智侠|情感男声(精)": 101000, "智瑜|情感女声(精)": 101001, "智聆|通用女声(精)": 101002, "智美|客服女声(精)": 101003,
              "智云|通用男声": 101004, "智莉|通用女声": 101005, "智言|助手女声": 101006, "智娜|客服女声": 101007, "智琪|客服女声": 101008,
              "智芸|知性女声": 101009, "智华|通用男声": 101010, "WeJack|英文男声(精)": 101050, "WeRose|英文女声(精)": 101051,
              "贝蕾|客服女声": 102000, "贝果|客服女声": 102001, "贝紫|粤语女声": 102002, "贝雪|新闻女声": 102003}
    if not os.path.exists("inandoutchating_file"):
        os.mkdir('inandoutchating_file')
    for vo in voices.values():
        print(vo)
        a.get_voice_from_text(text="已退出聊天模式", voicetype=vo, save_name="inandoutchating_file/out{}.wav".format(vo))

# 普通音色：
# 0-云小宁，亲和女声（默认）
# 1-云小奇，亲和男声
# 2-云小晚，成熟男声
# 4-云小叶，温暖女声
# 5-云小欣，情感女声
# 6-云小龙，情感男声
# 7-云小曼，客服女声
# 1000-智侠，情感男声
# 1001-智瑜，情感女声
# 1002-智聆，通用女声
# 1003-智美，客服女声
# 1050-WeJack，英文男声
# 1051-WeRose，英文女声
# 精品音色：
# 精品音色拟真度更高，价格不同于普通音色，查看购买指南
# 101000-智侠，情感男声（精品）
# 101001-智瑜，情感女声（精品）
# 101002-智聆，通用女声（精品）
# 101003-智美，客服女声（精品）
# 101004-智云，通用男声
# 101005-智莉，通用女声
# 101006-智言，助手女声
# 101007-智娜，客服女声
# 101008-智琪，客服女声
# 101009-智芸，知性女声
# 101010-智华，通用男声
# 101050-WeJack，英文男声（精品）
# 101051-WeRose，英文女声（精品）
# 102000-贝蕾，客服女声
# 102001-贝果，客服女声
# 102002-贝紫，粤语女声
# 102003-贝雪，新闻女声
