# JamTools
JamTools一个小工具集,包含了截屏、录屏、文字识别、各种格式转换、鼠标键盘动作录制播放、文件传输、聊天机器人等功能

部分功能已整理开源：
截屏功能:https://github.com/fandesfyf/Jamscreenshot
滚动截屏功能：https://github.com/fandesfyf/roll_screenshot
视频播放器：https://github.com/fandesfyf/JamVideoPlayer
```c
目录结构:.
│  test.py//主程序文件.测试文件.
│  main.py//不是主程序,只是用来存放引入库的文件,防止打包出错
│  WEBFilesTransmitter.py//网页端传输模块
│  WEBFilesTransmittertest.py//网页端传输模块测试
│  clientFilesTransmitter.py//客户端传输模块
│  clientFilesTransmittertest.py//客户端传输测试
│  jamcontroller.py//酱控制模块
│  jamscreenshot.py//截屏模块
│  jamroll_screenshot.py//滚动截屏模块
│  jampublic.py//公共引用
│  jamresourse.py//转化的资源文件
│  jamtoolsbuild.py//一键构建脚本,调用该脚本即可自动配置项目文件,自动编译/打包等
│  setjam.py//附加编译脚本,如在构建脚本中设置了编译,则会调用该脚本将所有库转化为c文件后编译
│  cv2.cp37-win_amd64.pyd//windows下编译的opencv库,如需扩展功能,请自行安装opencv-contrib-python==3.4.2.17
│  opencv_world341.dll
│  cv2.cpython-37m-darwin.so//macos下编译的opencv库
│  libopencv_world.3.4.1.dylib
│  cv2.so//linux下编译的opencv库
│  libopencv_world.so.3.4.1
│  PyQt5CoreModels.py//中间文件,运行一键构建脚本时将主源码复制到此
│  requirement.txt//依赖列表
│  audio_sniffer-x64.dll//windows下录音驱动
│  screen-capture-recorder-x64.dll//windows下录屏驱动
│  voice_and_text.py//已弃用,语音合成与语音转文字模块,由于api调用完了,暂不支持,如需使用可自行替换api
│  txpythonsdk.py//已弃用,腾讯Ai平台的sdk改写
│  README.md
│  LICENSE
│  
├─bin
│  ├─darwin
│  │     ...//macos下存放ffmpeg和gifsicle可执行文件的文件夹,请自行下载,下同
│  │      
│  ├─linux
│  │     ...//linux下的...
│  │      
│  └─win32
│         ...//window下的..
│          
├─html//网页前端
│  │  favicon.ico
│  │  index.html//登录界面
│  │  jamlistdir.html//下载页面
│  │  jamupload.html//上传页面
│  │  test.html//测试
│  │  
│  ├─fonts//字体
│  │      fontawesome-webfont.eot
│  │      fontawesome-webfont.svg
│  │      fontawesome-webfont.ttf
│  │      fontawesome-webfont.woff
│  │      fontawesome-webfont.woff2
│  │      FontAwesome.otf
│  │      
│  ├─jamcss//css文件夹
│  │      font-awesome.css
│  │      JamTools.css
│  │      login.css
│  │      
│  ├─jamhtmlpic//图标文件夹
│  │      jamdowload.png
│  │      
│  └─jamjs//存放js的文件夹
│          jquery-1.11.0.js
│          jquery.cookie.js
│          spark-md5.js
│          
├─imagefiles//存放图片的文件夹,
│  │  jamresourse.py//转化后的的资源文件
│  │  jamresourse.qrc//资源文件列表
│  │  setjamresourse.py//资源文件一键打包脚本,用于将图片文件转化为py文件,需要pyrcc支持
│  │  ...//图片文件
│  │  ...
│  │  ...
│  │  
│          
├─src//fbs打包的项目文件夹,通过一键构建脚本即可自动配置该目录
│  ├─build
│  │  └─settings//打包信息
│  │          base.json
│  │          linux.json
│  │          mac.json
│  │          
│  ├─installer
│  │  └─windows
│  │          Installer.nsi//Windows下的nsis构建脚本
│  │          
│  └─main
│      ├─icons//图标文件夹
│      │  │  Icon.ico
│      │  │  README.md
│      │  │  
│      │  ├─base
│      │  │      512.png
│      │  │      
│      │  ├─linux
│      │  │      512.png
│      │  │      
│      │  └─mac
│      │          512.png
│      │          
│      ├─python//存放源码的文件夹
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
│      └─resources//存放附加资源的文件夹
│          └─base
       
└─target//fbs打包输出文件夹

```c
