'''Setup file for building a pip for a module.

Local Install Process:

Build Pip Distributable: py -m build --wheel from the /PythonTools/ directory with this setup.py in it. Then install from the .whl file.
INSTRUCTIONS FOR BUILDING A PIP https://pip.pypa.io/en/stable/cli/pip_wheel/
OR
Developer Install: "py -m pip install -e ." from this folder.

Publish a Pip Version to PyPi:
0. Create an account https://pypi.org/account/register/
1. Install Prequisites: py -m pip install --upgrade pip setuptools wheel twine build
2. py setup.py sdist bdist_wheel
3. py -m twine upload dist/*


setuptools reference guide: https://docs.python.org/3/distutils/setupscript.html#installing-package-data
'''
import os
from distutils.core import setup

required_dependencies = [
    'tk',
    'pathlib'
]
scripts = [
]

#Using distutils.core over setuptools since package data was not specified correctly, needing the manifest.in file
setup(
    name = 'ra_fetch_de',
    version = os.getenv('PACKAGE_VERSION', '1.1.1'),
    author = 'Richard Albee',
    author_email='Ralbee1@iwu.edu',
    packages=['five_card_draw','five_card_draw.data'],
    package_dir={'five_card_draw': 'five_card_draw'},
    package_data={'five_card_draw': ['data/*.png','*.txt']},
    scripts=None,
    url = "https://github.com/richardalbee/fetch_data_engineer",
    license='LICENSE.txt',
    description='Fetch Job Application Assessment',
    long_description_content_type = 'text/markdown',
    long_description=open('README.md', encoding='utf-8').read(),
    install_requires=required_dependencies
)
