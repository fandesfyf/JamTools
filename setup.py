from cx_Freeze import setup, Executable
import numpy
import os
import sys
from cx_Freeze import setup, Executable
# from cx_Freeze.util import get_default_include_path
from cx_Freeze.finder import ModuleFinder
import shutil
'''运行`python setup.py build`即可打包'''

jamfilelist = ["CoreModels", "jamcontroller", "WEBFilesTransmitter", "clientFilesTransmitter",
               "jamscreenshot", "jampublic", "jamroll_screenshot", "Logger", "jamspeak",
               "jamWidgets", "jam_transtalater","PaddleOCRModel/PaddleOCRModel"]
print("说明:main.py为存放引入库的文件(无需管), cx_Freeze打包输出到build目录下.\n"
      "运行本文件打包时,会自动解析所有jamfilelist中源码的引入库,"
      "并将所有需要的库格式化后写入main.py文件中,从而让pyinstaller可以找到(否则可能有找不到库的错误)"
      "同时会自动配置scr项目目录,然后通过命令行运行打包程序实现自动打包,如需生成安装文件Windows下需要nsis环境,请自行探索..\n"
      "通过更改下面的WithCompile 和Debug变量可以调整是否编译和是否debug模式.\n"
      "需要编译时会将所有源码文件编译为c然后编译为pyd文件,可以实现源码保护,而且运行速度略有提升,需要自行配置好c和cython环境\n"
      "debug模式下运行打包文件将会有命令行窗口")
if __name__ == "__main__":
    import os
    import sys
    import shutil
    import subprocess, setuptools
    
    # from CoreModels import VERSON
    WithCompile = 0  # 是否编译
    Debug = 0  # 是否debug模式
    VERSON = "0.14.1B"

    if WithCompile:
        Compiler = subprocess.Popen('python setjam.py build_ext --inplace', shell=True,stderr=subprocess.PIPE)
        Compiler.wait()
        error=Compiler.stderr.read().decode("utf-8")
        print(">>>>>{}\n><<<<<<".format(error))
        if "error"in error:
            raise Exception("Compiler fail!\n{}".format(error))
        if sys.platform == "win32":
            ext = ".pyd"
            suffix = ".cp37-win_amd64"
        else:
            ext = ".so"
            suffix = ".cpython-37m-darwin"
    else:
        ext = ".py"
        suffix = ""
    
    ### gen main.py
    file_tips = "\n####### 本文件由setup.py 打包脚本自动生成 ######\n\n"
    # with open('main.py', "w", encoding="utf-8") as mainf:
    #     importfilelist = ["# !usr/bin/python3\n","# -*- coding: utf-8 -*-\n","import os\n","os.environ['DISPLAY'] = ':0'\n",
    #                       file_tips,"import pynput.keyboard\n", "import pynput.mouse\n"]
    #     for file in jamfilelist:
    #         print("explaining {}".format(file))
    #         with open("{}.py".format(file), "r", encoding="utf-8") as soursef:
    #             line = soursef.readline()
    #             while line:
    #                 if line[:6] == "import" or (line[:4] == "from" and "import" in line):
    #                     if "PyQt5" in line or "pynput" in line:
    #                         if "from" in line:
    #                             line = "import " + line.split(" ")[1] + "\n"
    #                         elif " as " in line:
    #                             line = line.split(" as ")[0] + "\n"
    #                     if "jampublic" in line: line = "import jampublic\n"
    #                     while line[-2] == "\\":  # 多行
    #                         if line not in importfilelist:
    #                             importfilelist.append(line)
    #                         line = soursef.readline()
    #                     if line not in importfilelist:
    #                         importfilelist.append(line)
    #                 line = soursef.readline()

    #     mainf.writelines(importfilelist)
    #     mainf.writelines(["from CoreModels import main\n", "main()\n\n",file_tips])
    

    
    
    # 需要包含的资源目录和文件
    if sys.platform=='win32':
        bin_files = "bin/win32"
    else:
        bin_files = "bin/linux" if sys.platform=='linux' else "bin/darwin"
    
    include_files = [
        (bin_files,"lib/"+bin_files),
        ("html/","lib/html"),
        ("LICENSE","LICENSE"),
        ("fake_useragent_0.1.11.json","lib/fake_useragent_0.1.11.json")
    ]
    if sys.platform == "win32":
        include_files.extend(
            [("screen-capture-recorder-x64.dll","screen-capture-recorder-x64.dll"),
             ("audio_sniffer-x64.dll","audio_sniffer-x64.dll")]
        )
    
    # exit()
    # Dependencies are automatically detected, but it might need
    # fine tuning.
    build_options = {'packages': ["Xlib","pynput"], 
                     'zip_include_packages':["PyQt5","numpy"],
                     "includes": ["atexit"],
                     'excludes': ["setuptools","tk8.6","scipy","numpy.libs","notebook","PySide2",
                                "tkinter","Cython","fbs_runtime",
                                "lib2to3","multiprocessing","packaging",
                                "pkg_resources","test",
                                    ],
                     "include_files": include_files,
                      }

    import sys
    if Debug:
        base = None
    elif sys.platform=='win32':
        base = 'Win32GUI'
    else:
        base = None
    exe_name = "JamTools"
    executables = [
        Executable('main.py', base=base, target_name = exe_name,icon="./icon.ico")
    ]

    setup(name=exe_name,
        version = VERSON,
        description = 'JamTools是一个完全开源的跨平台的小工具集类软件，支持Windows7/8/10/11、Macos、ubuntu系统(其他系统可以直接从源码编译打包)。包含了(滚动/区域)截屏、录屏、文字识别、多种语言互译、多媒体格式转换、鼠标键盘动作录制播放、局域网文件传输、聊天机器人等功能。github链接：https://github.com/fandesfyf/JamTools',
        options = {'build_exe': build_options,},
        executables = executables)
    # for filename in os.listdir("./build/"):
    #     if filename.startswith("exe."):
    #         destination_dir = f"./build/Jamtools"
    #         if os.path.exists(destination_dir):
    #             shutil.rmtree(destination_dir)
    #         shutil.copytree(f"./build/{filename}", destination_dir)
    #         print(f"move ./build/{filename} -> {destination_dir}")
    #         if os.path.exists("./build/Jamtools/lib/PyQt5/Qt/Qt5/plugins"):
    #             shutil.move("./build/Jamtools/lib/PyQt5/Qt/Qt5/plugins", "./build/Jamtools/lib/PyQt5/Qt/plugins")
    #         else:
    #             print("PyQt5/Qt/Qt5/plugins not found")
    # nsisfile_path = "build/installer/Installer.nsi"
    # if sys.platform == "win32" and os.path.exists(nsisfile_path):
    #     """重写windows下的nsis配置文件版本号"""
    #     with open(nsisfile_path, "r", encoding="ansi") as nsisfile:
    #         ns = nsisfile.readlines()
    #     for i, line in enumerate(ns):
    #         if "!define PRODUCT_VERSION" in line:
    #             print("找到版本号{}".format(line))
    #             v = line.split('"')[-2]
    #             if v != VERSON:
    #                 print(f"版本号不同{v}->{VERSON}")
    #                 ns[i] = '!define PRODUCT_VERSION "{}"\n'.format(VERSON)
    #                 with open(nsisfile_path, "w", encoding="ansi") as nsisfile:
    #                     nsisfile.writelines(ns)
    #             break
