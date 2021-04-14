#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Web框架使用了基于asyncio的aiohttp，aiohttp是基于协程的异步模型
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from coroweb import add_routes, add_static
from handlers import cookie2user, COOKIE_NAME
from config import configs

import logging; logging.basicConfig(level=logging.INFO)
import asyncio, json, os, time, orm

# middleware是一种拦截器，一个url在被处理函数处理之前，可以先经过一系列middleware的处理
# middleware的作用在于把通用的功能从url处理函数中拿出来，集中到一个地方处理
#
# 用于记录url请求日志的拦截器
async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        return (await handler(request))
    return logger
#
# 用于解析登录状态cookie并绑定到request对象上的拦截器
async def auth_factory(app, handler):
    async def auth(request):
        logging.info('check user: %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie = request.cookies.get(COOKIE_NAME)
        if cookie:
            user = await cookie2user(cookie)
            if user:
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
        usr = request.__user__ 
        if request.path.startswith('/manage/') and (usr is None or not usr.admin):
            return web.HTTPFound('/login')
        return (await handler(request))
    return auth
#
# 用于处理响应结果的拦截器
async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda x: x.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(status=r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(status=t, reason=str(m))
        # 默认处理
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

# 初始化jinja2模板配置
def init_jinja2(app, **kw):
    logging.info('init jinja2')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env

# 时间过滤器，注册到jinja2中，在html中使用，将浮点数转换成日期字符串
def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

async def init(loop):
    # 创建Web服务
    app = web.Application(middlewares=[logger_factory, auth_factory, response_factory])
    # 创建数据库连接池
    await orm.create_pool(loop, user=configs['db']['user'], password=configs['db']['password'], database=configs['db']['database'])
    # 初始化jinja2模板配置
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    # 注册url处理函数，处理函数都放在名为'handlers'的模块中，即名为hadlers.py的文件中
    add_routes(app, 'handlers')
    # 注册静态资源
    add_static(app)
    return app

# 启动Web服务
loop = asyncio.get_event_loop()
app = init(loop)
web.run_app(app, host=configs['web']['host'], port=configs['web']['port'])