#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 将所有URL处理函数集中定义到一个模块内
from coroweb import get, post
from model import User, Blog, Comment, gen_id
from apis import Page, APIError, APIValueError, APIPermissionError, APIResourceNotFoundError
from config import configs
from aiohttp import web

import logging; logging.basicConfig(level=logging.INFO)
import asyncio, time, re, hashlib, json, random

COOKIE_NAME = 'pythonwebsession'
_COOKIE_KEY = configs['session']['secret']

# 检查用户是不是博主
def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

# 获取分页索引
def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError:
        logging.info('invalid page index: %s', page_str)
    if p < 1:
        p = 1
    return p

# 将文本转换为HTML
def text2html(text):
    func = lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&rt;')
    lines = map(func, filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

# HTTP协议是一种无状态协议，服务器如果想要跟踪用户状态，只能通过cookie实现。
# 大多数Web框架提供了Session功能来封装保存用户状态的cookie，Session的优点是简单易用，缺点是Session需要服务器在内从中维护一个映射表存储用户登录信息，如果有多台服务器，就需要对Session做集群，因此使用Session的Web App很难扩展。
# 此处采用直接读取cookie的方式来验证用户登录，每次用户访问任意url，都会对cookie进行验证，方便服务器扩展。由于cookie是在登录成功后由服务器生成并发送给客户端的，因此要通过一个单向加密算法（如sha1）保证cookie不会被客户端伪造出来。
def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie):
    '''
    Parse cookie and load user if cookie is valid
    '''
    if not cookie:
        return None
    try:
        L = cookie.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

@get('/')
def index():
    return {
        '__template__': 'index.html'
    }

@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

@get('/login')
def login():
    return {
        '__template__': 'login.html'
    }

@get('/logout')
def logout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

@get('/blog/{id}')
def get_blog(id):
    return {
        '__template__': 'blog.html',
        'id': id
    }

@get('/manage/')
def manage():
    return 'redirect:/manage/blogs/create'

@get('/manage/comments')
def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html'
    }

@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html'
    }

@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': ''
    }

@get('/manage/blogs/edit')
def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id
    }

@get('/manage/users')
def manage_users(*, page="1"):
    return {
        '__template__': 'manage_users.html'
    }

_RE_EMAIL = re.compile(r'^[a-zA-Z0-9\.\-_]+@[a-zA-Z0-9\-_]+(\.[a-zA-Z0-9\-_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[a-fA-F0-9]{40}$')

@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    # 客户端传递过来的用户密码是经过SHA1计算后的40位Hash字符串
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('regiter:failed', 'email', 'Email is already in use.')
    
    # 保存用户信息
    user = User(name=name.strip(), email=email, passwd=hashlib.sha1(passwd.encode('utf-8')).hexdigest(), image='/static/images/profile-%s.jpg' % random.randint(1, 9))
    await user.save()

    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    # 注意：dumps方法返回一个str，而dump方法是将JSON写入file-like Object
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/api/users')
async def api_get_users(*, page="1"):
    page_index = get_page_index(page)
    num = await User.findCount('id')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderby='create_time desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)

@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]

    if user.passwd != hashlib.sha1(passwd.encode('utf-8')).hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findCount('id')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderby='create_time desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    check_admin(request)

    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    return (await blog.save())

@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    blog.html_content = text2html(blog.content)
    comments = await Comment.findAll('blog_id=?', [id], orderby='create_time desc')
    for c in comments:
        c.html_content = text2html(c.content)
    return dict(blog=blog, comments=comments)

@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content):
    check_admin(request)

    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog

@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)

    blog = await Blog.find(id)
    await blog.remove()
    return dict(id=id)

@get('/api/comments')
async def api_comments(*, page="1"):
    page_index = get_page_index(page)

    num = await Comment.findCount('id')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderby="create_time desc", limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image, content = content.strip())
    await comment.save()
    return comment

@post('/api/comments/{id}/delete')
async def api_delete_comments(id, request):
    check_admin(request)

    c = await Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    await c.remove()
    return dict(id=id)