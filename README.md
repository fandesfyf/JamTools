# JamTools
JamTools是一个小工具集,包含了(滚动)截屏、录屏、文字识别、多媒体格式转换、鼠标键盘动作录制播放、局域网文件传输、聊天机器人等功能，完全开源!

部分单独的模块已整理为项目：
[截屏功能](https://github.com/fandesfyf/Jamscreenshot) 
[滚动截屏功能](https://github.com/fandesfyf/roll_screenshot) 
[视频播放器](https://github.com/fandesfyf/JamVideoPlayer) 
[网页端传输项目](https://github.com/fandesfyf/WEBFilesTransmitter)
[客户端传输项目](https://github.com/fandesfyf/clientFilesTransmitter)

# >>>功能简介:
1.酱截屏：截图功能.快捷键Alt+z；支持选区截图、多边形截图、滚动截屏等、支持复制截屏文件或图像数据到剪切板、支持截图中文字识别(翻译)、图像识别等，左侧工具栏提供画笔橡皮擦等(QQ微信截屏有的都有)；支持滚动截屏，滚动过程中支持自动和手动滚动，滚动截屏比FSCapture的破解准确率更高，并且集成录屏功能，可以截屏时录屏。

2.酱识字：文字识别功能；截屏提取.快捷键Alt+x：截屏并提取文字；批量识别：可上传一张或多张图片进行文字提取

3.酱翻译：多语言翻译功能.无快捷键(极简模式下可通过浮窗使用)；输入文字翻译，支持多种语言互译！已集成到截屏等界面下。

4.酱录屏：录屏功能.快捷键Alt+c;屏幕录制功能，支持gif等多种格式录制；可以选定录制区，不选则为全屏录制；支持自定义编码速率、帧率、视频质量、声音源鼠标等；录屏结束后点击通知将直接播放！

5.酱转换：各种多媒体文件的裁剪拼接、压缩转码、提取混合功能...这个的功能太多自行探索...（有点像格式工厂）

6.酱控制：鼠标键盘所有动作的录制和(倍速无限次)重放，支持将录制的动作作为教程发送给你的小伙伴萌，支持快捷键启动Alt+1录制，Alt+2播放。注意是不是九宫格的数字1！是字母区上面的数字！动作文件(.jam)可以直接双击打开或拖入打开！（类似于按键精灵）

7.酱传输：提供快速的局域网传输功能,有客户端点对点连接传输和网页端共享两种方式。均支持数据双向传输。客户端传输需要通过连接码自动搜索并连接主机，建立连接之后即可互相发送文件或文件夹。网页端传输相当于共享文件夹，支持共享一个文件夹或文件夹下的某几个文件，通过选择对应网络适配器即可生成共享链接，连入该与适配器同一网络的其他设备即可通过链接或扫码访问共享文件，网页端勾选允许上传后支持文件上传，支持网页端传输密码设置，局域网传输比QQ微信传文件更高效快捷，实测通过连接同一热点的手机和电脑单向传输速率约为7MB/s(手机型号不同可能不一样)，校园网内两台电脑的双向传输达到10M/s。

8.酱聊天：。。。。彩蛋功能。。傻d机器人在线陪聊！！来自思知人工智能平台的机器人（别问为什么不用图灵机器人，因为没q啊！自己搞一个模型由太占空间了。。），填写用户ID后支持多轮对话，服务器有点慢。。。。毕竟思知也是免费提供的，还提供支持知识库训练，不能过多要求哈；默认保留50000字节的聊天记录。。

$其他功能：划屏提字：打开软件后可以在任何界面(图片也可)，用鼠标右键水平右划，即可提取出鼠标滑过的文字上下设定像素内的文字(并翻译)，可以在设置中心设置详细内容！
剪贴板翻译：监控剪贴板内容，剪切板内容变化7s内按下shift触发,支持英语自动翻译,网页自动打开,百度云链接提取码自动复制等！可在设置中心设置详细内容！
极简模式：(其实就是系统托盘加一个小界面)极简模式下不会显示主界面，截屏(Alt+z)、文字识别(Alt+x)、录屏(Alt+c)、键鼠动作录制(Alt+1)播放(Alt+2)均可以用(用快捷键/系统托盘)调用，所有功能显示均在小窗显示，小窗可以(回车)翻译(英-中),双击系统托盘可以进入/退出极简模式
##大部分功能可以在系统托盘调用！
# 界面展示
所有图片可以看image目录下的
### macos和ubuntu下的界面
![imgae](https://github.com/fandesfyf/JamTools/blob/main/image/ui.jpg)
### 截屏界面
![image](https://github.com/fandesfyf/JamTools/blob/main/image/jp.png)
##### 截屏时
![image](https://github.com/fandesfyf/JamTools/blob/main/image/jp0.jpg)
![image](https://github.com/fandesfyf/JamTools/blob/main/image/jp1.jpg)
### 录屏界面
![image](https://github.com/fandesfyf/JamTools/blob/main/image/sc.png)
### 文字提取界面
![image](https://github.com/fandesfyf/JamTools/blob/main/image/ocr.png)
### 多媒体格式转化界面
![image](https://github.com/fandesfyf/JamTools/blob/main/image/51.png)
![image](https://github.com/fandesfyf/JamTools/blob/main/image/52.png)
![image](https://github.com/fandesfyf/JamTools/blob/main/image/53.png)
### 键鼠动作录制播放界面
![image](https://github.com/fandesfyf/JamTools/blob/main/image/61.png)
![image](https://github.com/fandesfyf/JamTools/blob/main/image/62.png)
### 聊天机器人界面
![image](https://github.com/fandesfyf/JamTools/blob/main/image/chat.png)
### 其它功能
![image](https://github.com/fandesfyf/JamTools/blob/main/image/other.jpg)




# 项目目录
```c
目录结构:.
│  test.py //主程序文件.测试文件.
│  main.py //不是主程序,只是用来存放引入库的文件,防止打包出错
│  WEBFilesTransmitter.py //网页端传输模块
│  WEBFilesTransmittertest.py //网页端传输模块测试例子,单独ui
│  clientFilesTransmitter.py //客户端传输模块
│  clientFilesTransmittertest.py //客户端传输测试例子,单独ui
│  jamcontroller.py //酱控制模块
│  jamscreenshot.py //截屏模块
│  jamroll_screenshot.py //滚动截屏模块
│  jampublic.py //公共引用
│  jamresourse.py //转化的资源文件
│  jamtoolsbuild.py //一键构建脚本,调用该脚本即可自动分析项目引用,自动配置项目文件,自动编译/打包等
│  setjam.py //附加编译脚本,如在构建脚本中设置了编译,则会调用该脚本将所有库转化为c文件后编译
│  cv2.cp37-win_amd64.pyd //windows下编译的opencv库,如需扩展功能,请自行安装opencv-contrib-python==3.4.2.17
│  opencv_world341.dll
│  cv2.cpython-37m-darwin.so //macos下编译的opencv库
│  libopencv_world.3.4.1.dylib
│  cv2.so //linux下编译的opencv库
│  libopencv_world.so.3.4.1
│  PyQt5CoreModels.py //中间文件,运行一键构建脚本时将主源码复制到此
│  requirement.txt //依赖列表
│  audio_sniffer-x64.dll //windows下录音驱动
│  screen-capture-recorder-x64.dll //windows下录屏驱动
│  voice_and_text.py //已弃用,语音合成+语音转文字+播放模块,由于api调用完了,暂不支持,如需使用可自行替换api
│  txpythonsdk.py //已弃用,腾讯Ai平台的sdk改写
│  log.log //日志文件
│  README.md
│  LICENSE
│  
├─bin
│  ├─darwin
│  │     ... //macos下存放ffmpeg和gifsicle可执行文件的文件夹,请自行下载,下同
│  │      
│  ├─linux
│  │     ... //linux下的...
│  │      
│  └─win32
│         ... //window下的..
│          
├─html //网页前端
│  │  favicon.ico
│  │  index.html //登录界面
│  │  jamlistdir.html //下载页面
│  │  jamupload.html //上传页面
│  │  test.html //测试
│  │  
│  ├─fonts //字体
│  │      fontawesome-webfont.eot
│  │      fontawesome-webfont.svg
│  │      fontawesome-webfont.ttf
│  │      fontawesome-webfont.woff
│  │      fontawesome-webfont.woff2
│  │      FontAwesome.otf
│  │      
│  ├─jamcss //css文件夹
│  │      font-awesome.css
│  │      JamTools.css
│  │      login.css
│  │      
│  ├─jamhtmlpic //图标文件夹
│  │      jamdowload.png
│  │      
│  └─jamjs //存放js的文件夹
│          jquery-1.11.0.js
│          jquery.cookie.js
│          spark-md5.js
│          
├─imagefiles //存放图片的文件夹,
│  │  jamresourse.py //转化后的的资源文件
│  │  jamresourse.qrc //资源文件列表
│  │  setjamresourse.py //资源文件一键打包脚本,用于将图片文件转化为py文件,需要pyrcc支持
│  │  ... //图片文件
│  │  ...
│  │  ...
│  │  
│          
├─src //fbs打包的项目文件夹,通过一键构建脚本即可自动配置该目录
│  ├─build
│  │  └─settings //打包信息
│  │          base.json
│  │          linux.json
│  │          mac.json
│  │          
│  ├─installer
│  │  └─windows
│  │          Installer.nsi //Windows下的nsis构建脚本
│  │          
│  └─main
│      ├─icons //图标文件夹
│      │  │  Icon.ico
│      │  │  README.md
│      │  ├─base
│      │  │      512.png
│      │  ├─linux
│      │  │      512.png
│      │  └─mac
│      │         512.png
│      │          
│      ├─python //存放源码的文件夹
│      │  │  clientFilesTransmitter.py
│      │  │  jamcontroller.py
│      │  │  jampublic.py
│      │  │  jamresourse.py
│      │  │  jamroll_screenshot.py
│      │  │  jamscreenshot.py
│      │  │  main.py
│      │  │  PyQt5CoreModels.py
│      │  │  WEBFilesTransmitter.py
│      │  │  
│      │  └─__pycache__
│      │          main.cpython-37.pyc
│      │          
│      └─resources //存放附加资源的文件夹
│          └─base
└─target //fbs打包输出文件夹
│
│
└─testfiles //测试文件存放的文件夹,功能如名,只是用来测试最小例子
        ffmpegtest.py
        text2audio.py
        win32end2.py
        全局快捷键.py
        图片遮罩.py
        拼接部分相同图片(暴力遍历法).py
        比较相同.py
        泛洪填充.py
        滚动截屏2.0.py
        滚动截屏2.1.py
        滚动截屏3.0.py
        滚动截屏demo.py
        特征提取test.py
        相似拼接cv.py
        连接测试.py
        透视变换test.py
        透视裁剪test.py
            
```


# 使用及依赖
测试环境python3.7.8
```c
Wheel
Pillow
pynput
fbs 
qrcode
requests
PyInstaller==3.4
baidu-aip
PyQt5==5.15.2
PyQt5-sip==12.8.1
PyQt5-stubs==5.14.2.2
numpy
opencv-contrib-python==3.4.2.17//如果需要完整cv2支持,则安装这个版本的包,一定是这个版本;如果需要更小体积的cv2,则可以从[这里](https://github.com/fandesfyf/JamTools/releases/tag/0.12.5)下载删减版
Cython==0.29.21//如果需要编译
#PyAudio//如果需要机器人声音
#SpeechRecognition//如果需要机器人声音
#tencentcloud-sdk-python//如果需要机器人声音
setuptools==50.3.0
```
也可以通过```  pip3 install -r requirement.txt```安装所有依赖

此外,需要自行下载ffmpeg(用于录屏和多媒体处理)和gifsicle(用于gif压缩)可执行文件放到bin目录对应操作系统的文件夹下,方可使用对应功能.

配置好以上环境后,可以通过运行jamtoolsbuild.py文件一键打包对应平台下的包,然后通过fbs install命令构建安装程序,详情请看[这里](https://github.com/mherrmann/fbs-tutorial)


