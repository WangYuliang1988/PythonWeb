#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 使用Fabric实现本地工程打包并上传服务器进行部署
import os, tarfile, re, getpass

from datetime import datetime
from invoke import task
from fabric import Connection

_LOCAL_DIR_PATH = os.path.abspath('.')
_LOCAL_PKG_PATH = os.path.join(_LOCAL_DIR_PATH, 'dist')
_LOCAL_WWW_PATH = os.path.join(_LOCAL_DIR_PATH, 'www')

_TAR_FILE = 'dist-pythonweb.tar.gz'

_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/srv/pythonweb'

# 打包
@task
def build(c):
    tgz = tarfile.open(os.path.join(_LOCAL_PKG_PATH, _TAR_FILE), 'w:gz')
    for root, dirs, files in os.walk(_LOCAL_WWW_PATH):
        if root == os.path.join(_LOCAL_WWW_PATH, '__pycache__'):
            continue
        # 切换到当前（即www）目录
        os.chdir(_LOCAL_WWW_PATH)
        root = root.replace(_LOCAL_WWW_PATH, '').replace(os.sep, '', 1)
        for file in files:
            # 打包时排除config_local.py，以实现生产环境使用config_remote.py中的配置
            if file != 'config_local.py':
                tgz.add(os.path.join(root, file))
    tgz.close()

# 上传
@task
def deploy(c):
    # 手动输入服务器地址、用户名及密码
    host = input('host:')
    user = input('user:')
    password = getpass.getpass('password:')
    # 连接服务器
    conn = Connection(host=host, port='22', user=user, connect_kwargs={'password': password})
    # 删除服务器上老版本的tar文件
    conn.run('rm -f %s' % _REMOTE_TMP_TAR)
    # 上传新版本的tar文件
    conn.put(os.path.join(_LOCAL_PKG_PATH, _TAR_FILE), _REMOTE_TMP_TAR)
    # 在服务器上创建新目录
    newdir = 'www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')
    with conn.cd(_REMOTE_BASE_DIR):
        conn.run('mkdir %s' % newdir)
    # 解压tar文件至新目录
    with conn.cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
        conn.run('tar -xzvf %s' % _REMOTE_TMP_TAR)
    # 重置软链接
    with conn.cd(_REMOTE_BASE_DIR):
        conn.run('rm -f www')
        conn.run('ln -s %s www' % newdir)
    # 将app.py设置为可执行
    conn.run('chmod a+x %s/www/app.py' % _REMOTE_BASE_DIR)
    # 重启Python服务和Nginx服务
    conn.run('supervisorctl stop pythonweb')
    conn.run('supervisorctl start pythonweb')
    conn.run('/etc/init.d/nginx reload')

_RE_LINE_BREAK = re.compile('\r?\n')

# 回退
@task
def rollback(c):
    # 手动输入服务器地址、用户名及密码
    host = input('host:')
    user = input('user:')
    password = getpass.getpass('password:')
    # 连接服务器
    conn = Connection(host=host, port='22', user=user, connect_kwargs={'password': password})
    # 回退
    with conn.cd(_REMOTE_BASE_DIR):
        # 获取所有名称以"www-"开头的目录列表，列表按目录名称倒排序
        r = conn.run('ls -p -1').stdout
        files = [s[:-1] for s in _RE_LINE_BREAK.split(r) if s.startswith('www-') and s.endswith('/')]
        files.sort(reverse=True)

        # 获取当前"www"软链接指向的目录
        r = conn.run('ls -l www').stdout
        L = r.replace("\n", '').split(' -> ')
        if len(L) != 2:
            print('Error: \'www\' is not a symbol link.')
            return
        current = L[1]
        print('Found current symbol link points to %s' % current)

        # 获取上一个版本对应的目录
        try:
             index = files.index(current)
        except ValueError:
            print('Error: symbol link is invalid.')
            return
        if len(files) == index + 1:
            print('Error: alreay the oldest version.')
            return
        old = files[index + 1]

        # 要求确认是否进行回退操作
        print ('==================================================')
        for f in files:
            if f == current:
                print ('Current        ---> %s' % current)
            elif f == old:
                print ('Rollback to    ---> %s' % old)
        print ('==================================================')
        yn = input('continue? Y/N ')
        if yn != 'y' and yn != 'Y':
            print ('Rollback cancelled.')
            return
        
        # 重置软链接
        print ('Rollbacking...')
        conn.run('rm -f www')
        conn.run('ln -s %s www' % old)
        # 将app.py设置为可执行
        conn.run('chmod a+x %s/www/app.py' % _REMOTE_BASE_DIR)

        # 删除当前版本对应目录
        conn.run('rm -rf %s' % current)

        # 重启Python服务和Nginx服务
        conn.run('supervisorctl stop pythonweb')
        conn.run('supervisorctl start pythonweb')
        conn.run('/etc/init.d/nginx reload')
        print ('Rollback OK.')