#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 生产环境配置，使用Dict保存配置信息
configs = {
    'debug': False,
    'db': {
        'host': '127.0.0.1',
        'port': 3506,
        'user': 'mufc',
        'password': 'ferguson',
        'database': 'web'
    },
    'session': {
        'secret': 'pythonweb'
    },
    'web':{
        'host': '127.0.0.1',
        'port': '9527'
    }
}