import codecs
import os
import re

from setuptools import setup, find_packages

requirements = [
    "dockercloud-haproxy >= 1.6.7",
    "gevent==1.1.1"
]


def read(*parts):
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(
    name='acs-haproxy',
    version=find_version('acshaproxy', '__init__.py'),
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts':
            ['acs-haproxy = acshaproxy.main:main']
    },
    include_package_data=True,
    author='quanzhao.cqz',
    author_email='quanzhao.cqz@alibaba-inc.com',
    description='acs haproxy configured for aliyun container services',
    license='Apache v2',
    keywords='aliyun container service haproxy',
    url='http://cs.console.aliyun.com/',
)
