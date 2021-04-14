#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 一个Web App在运行时都需要读取配置文件，比如数据库的用户名、口令等
# 在不同的环境中运行时，Web App可以通过读取不同的配置文件来获得正确的配置
# 由于Python本身语法简单，可以直接用Python源代码来实现配置

# 本项目中配置文件包括config.py、config_local.py、config_remote.py三个
# config_local中包含开发环境配置，用于本地开发
# config_remote中包含正式环境配置，用于部署到服务器
# config处理配置的读取，先判断是否存在config_local.py，若存在则读取config_local配置，否则读取config_remote配置
# 工程部署服务器时会将config_local.py文件删除，以实现不同的环境读取不同的配置

import os, importlib

configs = {}
if os.path.exists('config_local.py'):
    local = importlib.import_module('config_local')
    configs = local.configs
else:
    remote = importlib.import_module('config_remote')
    configs = remote.configs