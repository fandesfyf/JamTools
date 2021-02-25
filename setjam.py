# -*- coding:utf-8 -*-
import setuptools, os
from distutils.core import setup
from Cython.Build import cythonize
from jamtoolsbuild import jamfilelist
# print("copy test.py->PyQt5CoreModels.py")
# testsize=os.path.getsize("test.py")
# coresize=os.path.getsize("PyQt5CoreModels.py")
# if testsize !=coresize:
#     with open("test.py", "r", encoding="utf-8")as f:
#         with open("PyQt5CoreModels.py", "w", encoding="utf-8")as mo:
#             mo.write(f.read())
print("start compiler")
for file in jamfilelist:
    setup(
        name='Jamtools',
        ext_modules=cythonize("{}.py".format(file), compiler_directives={'language_level': 3}),
    )

print('Compiler end')
# if os.path.exists("controller.c"):
#     os.remove("controller.c")
# if os.path.exists("PyQt5CoreModels.c"):
#     os.remove("PyQt5CoreModels.c")
# if os.path.exists("WEBFilesTransmitter.c"):
#     os.remove("WEBFilesTransmitter.c")
# python setjam.py build_ext --inplace   编译命令
# 注意要把main.py移动到目标文件夹
