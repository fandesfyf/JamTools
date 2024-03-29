import time

jamfilelist = ["CoreModels", "jamcontroller", "WEBFilesTransmitter", "clientFilesTransmitter",
               "jamscreenshot", "jampublic", "jamroll_screenshot", "Logger", "jamspeak",
               "jamWidgets", "jam_transtalater","PaddleOCRModel/PaddleOCRModel"]
print("说明:main.py为存放引入库的文件(无需管),scr文件夹是fbs打包的项目目录.\n"
      "运行本文件打包时,会自动解析所有jamfilelist中源码的引入库,"
      "并将所有需要的库格式化后写入main.py文件中,从而让pyinstaller可以找到(否则可能有找不到库的错误)"
      "同时会自动配置scr项目目录,然后通过命令行运行打包程序实现自动打包,如需生成安装文件Windows下需要nsis环境,请自行探索..\n"
      "通过更改下面的WithCompile 和Debug变量可以调整是否编译和是否debug模式.\n"
      "需要编译时会将所有源码文件编译为c然后编译为pyd文件,可以实现源码保护,而且运行速度略有提升,需要自行配置好c和cython环境\n"
      "debug模式下运行打包文件将会有命令行窗口")
if __name__ == '__main__':
    import os
    import shutil
    import subprocess, setuptools
    from jampublic import PLATFORM_SYS
    from CoreModels import VERSON

    WithCompile = 0  # 是否编译
    Debug = 0  # 是否debug模式


    if WithCompile:
        Compiler = subprocess.Popen('python setjam.py build_ext --inplace', shell=True,stderr=subprocess.PIPE)
        Compiler.wait()
        error=Compiler.stderr.read().decode("utf-8")
        print(">>>>>{}\n><<<<<<".format(error))
        if "error"in error:
            raise Exception("Compiler fail!\n{}".format(error))
        if PLATFORM_SYS == "win32":
            ext = ".pyd"
            suffix = ".cp37-win_amd64"
        else:
            ext = ".so"
            suffix = ".cpython-37m-darwin"
    else:
        ext = ".py"
        suffix = ""
    if os.path.exists("src/main/python"):
        print("清空目标文件夹")
        shutil.rmtree("src/main/python")
        time.sleep(0.1)
    os.mkdir("src/main/python")
    for file in jamfilelist:
        if os.path.exists('{}{}{}'.format(file, suffix, ext)):
            if "/" in file:
                path = 'src/main/python/{}'.format("/".join(os.path.split(file)[:-1]))
                if not os.path.exists(path):
                    print("创建文件夹{path}")
                    os.mkdir(path)
            if os.path.exists('src/main/python/{}{}'.format(file, ext)):
                os.remove('src/main/python/{}{}'.format(file, ext))
                print('removed src/main/python/{}{}'.format(file, ext))
            shutil.copy2('{}{}{}'.format(file, suffix, ext), 'src/main/python/{}{}'.format(file, ext))
            if WithCompile:
                os.remove("{}{}{}".format(file, suffix, ext))
            print('copy {}{}'.format(file, ext))
        else:
            raise OSError('{}{}{} not found'.format(file, suffix, ext))
    file_tips = "\n####### 本文件由jamtoolsbuild.py 打包脚本自动生成 ######\n\n"
    with open('main.py', "w", encoding="utf-8") as mainf:
        importfilelist = ["# !usr/bin/python3\n","# -*- coding: utf-8 -*-\n",
                          file_tips,"import pynput.keyboard\n", "import pynput.mouse\n"]
        for file in jamfilelist:
            print("explaining {}".format(file))
            with open("{}.py".format(file), "r", encoding="utf-8") as soursef:
                line = soursef.readline()
                while line:
                    if line[:6] == "import" or (line[:4] == "from" and "import" in line):
                        if "PyQt5" in line or "pynput" in line:
                            if "from" in line:
                                line = "import " + line.split(" ")[1] + "\n"
                            elif " as " in line:
                                line = line.split(" as ")[0] + "\n"
                        if "jampublic" in line: line = "import jampublic\n"
                        while line[-2] == "\\":  # 多行
                            if line not in importfilelist:
                                importfilelist.append(line)
                            line = soursef.readline()
                        if line not in importfilelist:
                            importfilelist.append(line)
                    line = soursef.readline()

        mainf.writelines(importfilelist)
        mainf.writelines(["from CoreModels import main\n", "main()\n\n",file_tips])
    shutil.copy2('main.py', 'src/main/python/main.py')
    print('copy main.py')
    shutil.copy2('imagefiles/jamresourse.py', 'src/main/python/jamresourse.py')
    print('copy jamresourse.py')
    if os.path.exists("src/main/resources/base"):
        shutil.rmtree("src/main/resources/base")
        
    resource_pack_dict={
        "dirs":{# from : to
            "bin/" + PLATFORM_SYS:"src/main/resources/base/bin/"+ PLATFORM_SYS,
            "html":"src/main/resources/base/html",
            "site-packages/qt_material":"src/main/resources/base/qt_material",
            "PaddleOCRModel/modelv3":"src/main/resources/base/PaddleOCRModel/modelv3"
            },
        "files":{# dir : files
            "src/main/resources/base":["log.log", "LICENSE","fake_useragent_0.1.11.json"]+\
                ["screen-capture-recorder-x64.dll", "audio_sniffer-x64.dll"]if PLATFORM_SYS == "win32" else [] + ["libopencv_world.so.3.4"] if PLATFORM_SYS == "linux" else [],
            "src/main/resources/base/PaddleOCRModel":["PaddleOCRModel/ppocr_keys_v1.txt"]
        }
    }
    os.makedirs("src/main/resources/base/bin")
    dirs = resource_pack_dict["dirs"]
    print("打包资源目录")
    for d in dirs:
        td = dirs[d]
        if os.path.exists(d):
            rd = "/".join(os.path.split(td)[:-1])
            if not os.path.exists(rd):
                print(f"+创建目录:{rd}")
                os.makedirs(rd)
            if os.path.exists(td):
                shutil.rmtree(td)
                print(f"-移除{td}")
            shutil.copytree(d, td)
            print(":copy{} -> {}".format(d, td))
        else:
            print("!不存在源路径:", d)
    files = resource_pack_dict["files"]
    print("打包资源文件")
    for td in files:
        fileslist = files[td]
        if not os.path.exists(td):
            print(f"+创建目录:{td}")
            os.makedirs(td)
        for file in fileslist:
            if os.path.exists(file):
                filename = os.path.split(file)[-1]
                to_dir_filename=os.path.join(td,filename)
                if os.path.exists(to_dir_filename):
                    os.remove(to_dir_filename)
                    print("-移除", to_dir_filename)
                shutil.copy2(file, to_dir_filename)
                print(":copy{} -> {}".format(file, to_dir_filename))
            else:
                print(f"!找不到源文件{file}")

    if PLATFORM_SYS == "win32" and os.path.exists("target/installer/Installer.nsi"):
        """重写windows下的nsis配置文件版本号"""
        with open("target/installer/Installer.nsi", "r", encoding="ansi") as nsisfile:
            ns = nsisfile.readlines()
        for i, line in enumerate(ns):
            if "!define PRODUCT_VERSION" in line:
                print("找到版本号{}".format(line))
                v = line.split('"')[-2]
                print(v)
                if v != VERSON:
                    print("版本号不同")
                    ns[i] = '!define PRODUCT_VERSION "{}"\n'.format(VERSON)
                    with open("target/installer/Installer.nsi", "w", encoding="ansi") as nsisfile:
                        nsisfile.writelines(ns)
                break
    print('start freeze')
    # fbs freeze --debug
    freezer = subprocess.Popen('fbs freeze {}'.format("--debug" if Debug else ""), shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    freezer.wait()
    print("freeze end")
    if PLATFORM_SYS != "win32":
        a = input("是否打包为安装文件,Y/N:(回车默认Y)")
        if "y" in a.lower() or len(a) == 0:
            print("开始打包镜像")
            freezer = subprocess.Popen('fbs installer', shell=True,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
            freezer.wait()
            print("打包完成")
            if PLATFORM_SYS == "linux":
                print("linux下自行运行sudo dpkg -i target/JamTools.deb安装")
    else:# win32下打包好之后的操作
        if os.path.exists("target/JamTools/cv2"):
            print("replace cv2 module")
            shutil.rmtree("target/JamTools/cv2")
        os.mkdir("target/JamTools/cv2")
        shutil.copy2("opencv_world341.dll", "target/JamTools/cv2/opencv_world341.dll")
        shutil.copy2("cv2.cp37-win_amd64.pyd", "target/JamTools/cv2/cv2.cp37-win_amd64.pyd")
        
    print('finished all')
    time.sleep(2)
