import time

jamfilelist = ["PyQt5CoreModels", "jamcontroller", "WEBFilesTransmitter", "clientFilesTransmitter",
               "jamscreenshot", "jampublic", "jamroll_screenshot", "Logger", "jamspeak"]
print("说明:test.py文件为主文件,main.py为存放引入库的文件(无需管),scr文件夹是fbs打包的项目目录.\n"
      "运行本文件打包时,会自动将test.py文件覆盖到PyQt5CoreModels.py(这是前期为了防反编译搞的hh)中,然后会自动解析所有jamfilelist中源码的引入库,"
      "并将所有需要的库格式化后写入main.py文件中,从而让pyinstall可以找到(否则可能有找不到库的错误)"
      "同时会自动配置scr项目目录,然后通过命令行运行打包程序实现自动打包,如需生成安装文件Windows下需要nsis环境,请自行探索..\n"
      "通过更改下面的WithCompile 和Debug变量可以调整是否编译和是否debug模式.\n"
      "需要编译时会将所有源码文件编译为c然后编译为pyd文件,可以实现源码保护,而且运行速度略有提升,需要自行配置好c和cython环境\n"
      "debug模式下运行打包文件将会有命令行窗口")
# "voice_and_text","txpythonsdk"这两个是机器人语音合成的库,由于tx的api改为付费的了,所以不能播放声音(作者没钱了qaq),
# 如需使用可以在test.py中引入相关的包(已注释掉)然后在voice_and_text和txpythonsdk中修改api即可
if __name__ == '__main__':
    import os
    import shutil
    import subprocess, setuptools
    from jampublic import PLATFORM_SYS
    from test import VERSON

    WithCompile = False  # 是否编译
    Debug = 0  # 是否debug模式
    print("copy test.py->PyQt5CoreModels.py")
    testsize = os.path.getsize("test.py")
    coresize = os.path.getsize("PyQt5CoreModels.py")
    if testsize != coresize:
        with open("test.py", "r", encoding="utf-8") as f:
            with open("PyQt5CoreModels.py", "w", encoding="utf-8") as mo:
                mo.write(f.read())

    if WithCompile:
        Compiler = subprocess.Popen('python3 setjam.py build_ext --inplace', shell=True)
        Compiler.wait()
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
            if os.path.exists('src/main/python/{}{}'.format(file, ext)):
                os.remove('src/main/python/{}{}'.format(file, ext))
                print('removed src/main/python/{}{}'.format(file, ext))
            shutil.copy2('{}{}{}'.format(file, suffix, ext), 'src/main/python/{}{}'.format(file, ext))
            if WithCompile:
                os.remove("{}{}{}".format(file, suffix, ext))
            print('copy {}{}'.format(file, ext))
        else:
            raise OSError

    with open('main.py', "w", encoding="utf-8") as mainf:
        importfilelist = ["import pynput.keyboard\n", "import pynput.mouse\n"]
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
        mainf.writelines(["from PyQt5CoreModels import main\n", "main()\n\n"])
    shutil.copy2('main.py', 'src/main/python/main.py')
    print('copy main.py')
    shutil.copy2('imagefiles/jamresourse.py', 'src/main/python/jamresourse.py')
    print('copy jamresourse.py')
    if os.path.exists("src/main/resources/base"):
        shutil.rmtree("src/main/resources/base")
    os.makedirs("src/main/resources/base/bin")
    includedir = ["html", "bin/" + PLATFORM_SYS]
    includefiles = ["log.log", "LICENSE"]
    if PLATFORM_SYS == "win32":
        includefiles.extend(["screen-capture-recorder-x64.dll", "audio_sniffer-x64.dll"])
    elif PLATFORM_SYS == "linux":
        includefiles.extend(["libopencv_world.so.3.4"])
    for d in includedir:
        td = "src/main/resources/base/" + d
        if os.path.exists(d):
            if os.path.exists(td):
                shutil.rmtree(td)
                print("移除", td)
            shutil.copytree(d, td)
            print("copy{}->{}".format(d, td))
        else:
            print("不存在:", d)

    for f in includefiles:
        td = "src/main/resources/base/" + f
        if os.path.exists(f):
            if os.path.exists(td):
                os.remove(td)
                print("移除", td)
            shutil.copy2(f, td)
            print("copy{}->{}".format(f, td))
        else:
            print("不存在", f)

    if PLATFORM_SYS == "win32":
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

    print('finished all')
