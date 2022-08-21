# -*- coding:utf-8 -*-
import setuptools, os
from distutils.core import setup
from Cython.Build import cythonize
from jamtoolsbuild import jamfilelist

print("start compiler")
for file in jamfilelist:
    setup(
        name='Jamtools',
        ext_modules=cythonize("{}.py".format(file), compiler_directives={'language_level': 3}),
    )

print('Compiler end')

