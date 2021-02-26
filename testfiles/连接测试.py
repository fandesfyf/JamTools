import os, sys, threading

class th(threading.Thread):
    def __init__(self,ac,ips):
        super().__init__()
        self.action=ac
        self.ips=ips
    def run(self) -> None:
        # print(self.ips)
        for ip in self.ips:
            self.action(ip)
def pingip(ip):
    ipconfig_result_list = os.popen('ping 172.30.84.{}'.format(ip)).readlines()
    for line in ipconfig_result_list:
        if "100% 丢失" in line or "请求超时" in line:
            # print(ip,"连接失败")
            return
    print(ipconfig_result_list)
ths=[]
n=1
ips=range(0,255)
for i in range(0,255//n-1):
    print(i*n,n*(i+1))
    thread=th(pingip,ips[i*n:i*(n+1)])
    thread.start()
    ths.append(thread)
for th in ths:
    th.join()

