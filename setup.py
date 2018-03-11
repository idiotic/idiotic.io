import os
import sys
from setuptools import setup, find_packages

def read_license():
    with open("LICENSE") as f:
        return f.read()

data_files = [
    ('/share/idiotic.io/templates/', os.listdir('idioticio/templates')),
    ('/share/idiotic.io/static/', os.listdir('idioticio/static')),
]

if 'bdist_rpm' in sys.argv:
    data_files.extend([
        ('/etc/idiotic.io/', ['contrib/conf.yaml']),
        ('/usr/lib/systemd/system/', ['contrib/idiotic.service']),
    ])

setup(
    name='idiotic',
    packages=find_packages(exclude=['etc', 'contrib']),
    version='0.0.1',
    description='idiotic home automation controller managemnet thingy',
    long_description="""Provides an Internet-facing server that provides a proxy
    for incoming OAuth requests and management for individual idiotic instances.
    """,
    license=read_license(),
    author='Dylan Whichard',
    author_email='dylan@whichard.com',
    url='https://github.com/idiotic/idiotic.io',
    keywords=[
        'home automation', 'iot', 'internet of things'
    ],
    classifiers=[
        'Framework :: Flask',
        'Development Status :: 3 - Alpha',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Home Automation',
    ],
    install_requires=[
        'aiohttp',
        'flask',
        'sqlalchemy',
        'requests_oauthlib',
        'passlib',
        'bcrypt',
        'PyYAML',
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'idioticio=idioticio.__main__:main',
        ]
    },
)
