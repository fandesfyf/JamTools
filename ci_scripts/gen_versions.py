#!usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2023/2/9 21:47
# @Author  : Fandes
# @FileName: gen_version.py
# @Software: PyCharm


import time
import os
import sys
import re
os.chdir(sys.path[0])
os.chdir(os.path.abspath("../"))
sys.path.append(os.path.abspath("./"))
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def gethtml(url, times=3):  # 下载一个链接
    try:
        ua = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36 Edg/108.0.1462.54"
        response = requests.get(url, headers={"User-Agent": ua}, timeout=8, verify=False)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text

    except Exception as e:
        print(sys.exc_info(), '重试中')
        time.sleep(1)
        if times > 0:
            gethtml(url, times=times - 1)
        else:
            return "网络连接失败!"
        

PLATFORMS = ["win32","linux","darwin"]
class Gen_versions(object):
    def __init__(self) -> None:
        self.versions={}
        with open("ci_scripts/versions.json","r",encoding="utf-8")as f:
            self.versions = json.loads(f.read())
        print("原有版本信息{}".format(self.versions))
    def run(self) -> None:
        platform_dict = {"win32":"windows","linux":"linux","darwin":"darwin"}
        for pl in PLATFORMS:
            print("\n正在获取{}版本信息..".format(pl))
            versiondict = self.get_lastversion(pl)
            if len(versiondict):
                url,version = versiondict["url"],versiondict["versions"][0]
                self.versions[platform_dict[pl]]={"version":version,"url":url}
        with open("ci_scripts/versions.json","w",encoding="utf-8")as f:
            f.write(json.dumps(self.versions,indent=4))
        print("更新版本信息:{}".format(self.versions))
    def get_lastversion(self,platform="win32"):
        if platform == "win32":
            p = "exe"
        else:
            p = "deb" if platform == "linux" else "dmg"
        url = "https://github.com/fandesfyf/JamTools/releases"
        data = gethtml(url)
        tags = [i for i in re.findall('JamTools/releases/tag/(.*?)"', data)]
        print("tags",tags)
        all_version_urls = []
        for tag in tags:
            get_tag_page = gethtml("https://github.com/fandesfyf/JamTools/releases/expanded_assets/{}".format(tag))
            
            versionsurls = ["https://github.com" + i for i in
                            re.findall('(/fandesfyf/JamTools/releases/download/.*{})"'.format(p), get_tag_page)
                            if i[-3:] in ["deb", "exe", "dmg"]]
            all_version_urls.extend(versionsurls)
        versiondict = {}
        for link in all_version_urls:
            versionst = re.findall("\..*/.*(([1-9]?[0-9])\.([1-9]?[0-9])\.([1-9]?[0-9]*)([A|B]?))", link)[0]
            if versionst[0] != "":
                versiondict = {"url": link, "versions": versionst}
                break
        print(versiondict)
        return versiondict
    
if __name__ == "__main__":
    Gen_versions().run()
