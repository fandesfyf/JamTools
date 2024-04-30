# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import shutil
VERSON = "0.14.5B"
pack_datas=[("icon.ico", "."),("icon.png", ".",),("html","."),("LICENSE", "."),
           ("log.log","."),("fake_useragent_0.1.11.json","."),("PaddleOCRModel","PaddleOCRModel")]  # 额外的数据文件
if sys.platform == "win32":
    pack_datas.append(("bin/win32","bin/win32"))
    pack_datas.extend([("screen-capture-recorder-x64.dll","."),("audio_sniffer-x64.dll",".")])
elif sys.platform == "darwin":
    pack_datas.append(("bin/darwin","bin/darwin"))
else:
    pack_datas.append(("bin/linux","bin/linux"))
    
    if os.path.exists("libopencv_world.so.3.4") and os.path.exists("cv2.so"):
        print("found cv2.so")
        pack_datas.extend([("libopencv_world.so.3.4","."),("cv2.so",".")])

a = Analysis(
    ['main.py'],  # 包含的文件
    pathex=[],  # 额外的搜索路径
    binaries=[],  # 依赖的二进制文件
    datas = pack_datas,  # 额外的数据文件
    hiddenimports=['pynput.keyboard._xorg', 'pynput.mouse._xorg',"pynput.keyboard._win32","pynput.mouse._win32"],  # 需要隐式导入的模块
    hookspath=[],  # 钩子路径
    hooksconfig={},  # 钩子配置
    runtime_hooks=[],  # 运行时钩子
    excludes=[],  # 被排除的模块
    noarchive=False,  # 不使用归档文件
    # optimize=0,  # 优化级别
)
pyz = PYZ(a.pure)  # 纯Python字节码

exe = EXE(
    pyz,  # 打包的纯Python字节码
    a.scripts,  # 执行的脚本
    [],  # 其他参数
    exclude_binaries=True,  # 排除依赖的二进制文件
    name='JamTools',  # 可执行文件的名称
    debug=False,  # 是否启用调试模式
    bootloader_ignore_signals=False,  # 引导加载程序是否忽略信号
    strip=False,  # 是否删除调试信息
    upx=True,  # 是否使用UPX压缩
    console=False,  # 是否显示控制台
    disable_windowed_traceback=False,  # 是否禁用窗口化回溯
    argv_emulation=False,  # 是否启用参数仿真
    target_arch=None,  # 目标架构
    codesign_identity=None,  # 签名标识
    entitlements_file=None,  # 权限文件
    icon='./icon.ico',  # 图标文件
)

coll = COLLECT(
    exe,  # 可执行文件
    a.binaries,  # 所需的二进制文件
    a.datas,  # 所需的数据文件
    strip=False,  # 是否删除调试信息
    upx=True,  # 是否使用UPX压缩
    upx_exclude=[],  # 要排除的UPX压缩文件
    name='JamTools',  # 最终输出的程序名称
)


print("build success")
if sys.platform == "win32":
    destination_folder = "build/JamTools"
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    shutil.copytree("dist/JamTools", destination_folder)
    print("copy to build folder success, please use NSIS with build/windows/install.nsi to build installer")
    nsisfile_path = "build/windows/Installer.nsi"
    if os.path.exists(nsisfile_path):
        """重写windows下的nsis配置文件版本号"""
        with open(nsisfile_path, "r", encoding="ansi") as nsisfile:
            ns = nsisfile.readlines()
        for i, line in enumerate(ns):
            if "!define PRODUCT_VERSION" in line:
                print("找到版本号{}".format(line))
                v = line.split('"')[-2]
                if v != VERSON:
                    print(f"版本号不同{v}->{VERSON}")
                    ns[i] = '!define PRODUCT_VERSION "{}"\n'.format(VERSON)
                    with open(nsisfile_path, "w", encoding="ansi") as nsisfile:
                        nsisfile.writelines(ns)
                break
