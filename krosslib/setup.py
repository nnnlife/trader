import pathlib
import re

import setuptools


root_dir = pathlib.Path(__file__).parent

description = 'Kross Library'

long_description = 'Kross Library'
#long_description = (root_dir / 'README.md').read_text(encoding='utf-8')

# PyPI disables the "raw" directive.
#long_description = re.sub(
#    r"^\.\. raw:: html.*?^(?=\w)",
#    "",
#    long_description,
#    flags=re.DOTALL | re.MULTILINE,
#)

exec((root_dir / 'krosslib' / 'version.py').read_text(encoding='utf-8'))

packages = ['krosslib']

setuptools.setup(
    name='krosslib',
    version=version,
    description=description,
    long_description=long_description,
    url='',
    author='KrossTrading',
    author_email='nnnlife@gmail.com',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    package_dir = {'': '.'},
    packages=packages,
    include_package_data=True,
    package_data={'': ['data/*.xls']},
    zip_safe=False,
    python_requires='>=3.7',
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    #test_loader='pytest',
)

