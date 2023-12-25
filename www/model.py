#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from orm import Model, StringField, BooleanField, FloatField, TextField

import time, uuid

def gen_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=gen_id, column_type='varchar(64)')
    email = StringField(column_type='varchar(128)')
    passwd = StringField(column_type='varchar(64)')
    admin = BooleanField()
    name = StringField(column_type='varchar(64)')
    image = StringField(column_type='varchar(512)')
    create_time = FloatField(default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=gen_id, column_type='varchar(64)')
    user_id = StringField(column_type='varchar(64)')
    user_name = StringField(column_type='varchar(64)')
    user_image = StringField(column_type='varchar(512)')
    name = StringField(column_type='varchar(64)')
    author = StringField(column_type='varchar(64)')
    dynasty = StringField(column_type='varchar(16)')
    summary = StringField(column_type='varchar(256)')
    content = TextField()
    create_time = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=gen_id, column_type='varchar(64)')
    blog_id = StringField(column_type='varchar(64)')
    user_id = StringField(column_type='varchar(64)')
    user_name = StringField(column_type='varchar(64)')
    user_image = StringField(column_type='varchar(512)')
    content = TextField()
    create_time = FloatField(default=time.time)

# Model对应的数据库表通过手动方式进行创建
# 依次在MySQL命令行执行以下语句完成表的创建操作
#
# 创建用户
#   create user 'mufc'@'localhost' identified by 'ferguson';
# 
# 创建数据库
#   create database if not exists web;
#
# 使用数据库
#   use web;
#
# 给数据库用户赋权
#   grant select, insert, update, delete on web.* to 'mufc'@'localhost';
#
# 创建users表
#   create table users (
#       `id` varchar(64) not null,
#       `email` varchar(128) not null,
#       `passwd` varchar(64) not null,
#       `admin` bool not null,
#       `name` varchar(64) not null,
#       `image` varchar(512) not null,
#       `create_time` real not null,
#       unique key `idx_email` (`email`),
#       key `idx_create_time` (`create_time`),
#       primary key (`id`)
#   ) engine=innodb default charset=utf8;
# 
# 创建blogs表
#   create table blogs (
#       `id` varchar(64) not null,
#       `user_id` varchar(64) not null,
#       `user_name` varchar(64) not null,
#       `user_image` varchar(512) not null,
#       `name` varchar(64) not null,
#       `author` varchar(64) not null,
#       `dynasty` varchar(16) not null,
#       `summary` varchar(256) not null,
#       `content` mediumtext not null,
#       `create_time` real not null,
#       key `idx_create_time` (`create_time`),
#       primary key (`id`)
#   ) engine=innodb default charset=utf8;
#
# 创建comments表
#   create table comments (
#       `id` varchar(64) not null,
#       `blog_id` varchar(64) not null,
#       `user_id` varchar(64) not null,
#       `user_name` varchar(64) not null,
#       `user_image` varchar(512) not null,
#       `content` mediumtext not null,
#       `create_time` real not null,
#       key `idx_create_time` (`create_time`),
#       primary key (`id`)
#   ) engine=innodb default charset=utf8;

# 通过以下代码测试数据库、Model和ORM
#
# from config import configs
#
# import orm, asyncio
#
# async def check(loop):
#     await orm.create_pool(loop, host=configs['db']['host'], port=configs['db']['port'], user=configs['db']['user'], password=configs['db']['password'], database=configs['db']['database'])
#     # # 测试保存
#     u = User(name='ww', email='mail@cc.com', passwd='123456', image='no')
#     print(await u.save())
#     # 测试查找全部记录
#     u_list = await User.findAll()
#     print(u_list)
#     # 测试查找单条记录
#     u_ww = u_list[0]
#     print(await User.find(u_ww.id))
#     # 测试更新
#     u_ww.name='mm'
#     print(await u_ww.update())
#     # 测试删除
#     print(await u_ww.remove())
# loop = asyncio.get_event_loop()
# loop.run_until_complete(check(loop))
