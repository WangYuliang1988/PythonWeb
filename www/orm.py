#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 由于Web框架使用的是基于协程的异步模型aiohttp，在协程中，通过一个线程服务所有用户，协程的执行速度必须非常快，才能处理大量用户的请求
# 因此耗时的IO操作不能在协程中以同步的方式调用，否则系统在等待一个耗时的IO操作时，将无法响应其他用户的请求
# 
# aiomysql为MySQL数据库提供了异步IO的驱动

from config import configs

import logging; logging.basicConfig(level=logging.INFO)
import aiomysql

# 创建一个全局的连接池，每个HTTP请求都可以从连接池中直接获取数据库连接，避免频繁的打开和关闭数据库连接
async def create_pool(loop, **kw):
    logging.info('create database connection pool')

    # 连接池由全局变量__pool存储
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', configs['db']['host']),
        port=kw.get('port', configs['db']['port']),
        user=kw['user'],
        password=kw['password'],
        db=kw['database'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

# 查询方法，执行SELECT语句
async def select(sql, args, size=None):
    logging.info('SQL: %s with args: %s' % (sql, args))

    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        # SQL语句的占位符是?，而MySQL的占位符是%s，需要进行替换
        await cur.execute(sql.replace('?', '%s'), args or ())
        # 如果传入size参数，则获取指定数量的记录，否则获取所有记录
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

# 执行INSERT、UPDATE、DELETE语句，这3种语句需要相同的参数，返回结果也都是一个表示影响行数的整数
async def execute(sql, args):
    logging.info('SQL: %s with args: %s' % (sql, args))

    with (await __pool) as conn:
        cur = await conn.cursor()
        await cur.execute(sql.replace('?', '%s'), args)
        affeted = cur.rowcount
        await cur.close()
        # 返回影响的结果行数
        return affeted

# 设计ORM（Object Relational Mapping，对象映射关系）需要从上层调用者的角度进行设计
# 编写ORM框架，所有的类都只能动态定义（metaclass），因为只有使用者才能根据表的结构定义出对应的类来

# metaclass直译为元类
# 对于面向对象编程来说，一般都是先定义类，然后创建实例
# 元类允许你先定义metaclass，然后通过metaclass创建类，最后再通过类创建实例
# metaclass的理论基础是动态语言的类不是在编译时定义的，而是在运行时创建的

# 按照默认习惯，metaclass的类名总是以Metaclass结尾，以便清楚地表示这是一个metaclass
# metaclass是类的模板，因此必须从'type'类型派生
class ModelMetaclass(type):
    # cls，当前准备创建的类的对象
    # name，类的名字
    # bases，类继承的父类集合
    # attrs，类的属性和方法集合
    def __new__(cls, name, bases, attrs):
        # 如果是创建Model类本身，则直接创建
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        
        # 获取表名，没有的话使用类名作为表名
        tablename = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tablename))
        # 遍历类的属性，其中Field属性对应数据库表中的字段：属性名称对应字段名称，属性值包含字段类型、默认值等信息
        mappings = dict()
        fields = []
        primarykey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 如果主键已经存在，则报异常
                    if primarykey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    else:
                        primarykey = k
                else:
                    fields.append(k)
        # 限制必须有主键
        if not primarykey:
            raise RuntimeError('Primary key not found.')
        # 删除类属性中的Field属性，否则容易造成运行时错误（实例的属性会遮盖类的同名属性）
        for k in mappings.keys():
            attrs.pop(k)
        
        # 对Field进行转义，``是MySQL的转义符，可以避免列名、表名与MySQL自身的关键字冲突
        # map(function, iterable, ...)语法，依次将iterable中的每个元素传入function并执行，返回包含每次执行结果的迭代器
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        
        attrs['__table__'] = tablename
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primarykey
        attrs['__fields__'] = fields

        # 构造默认的SELECT、INSERT、UPDATE、DELETE语句
        # 注意数据库表的创建是单独进行的，ORM不进行处理
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primarykey, ', '.join(escaped_fields), tablename)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tablename, ', '.join(escaped_fields), primarykey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tablename, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primarykey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tablename, primarykey)

        return type.__new__(cls, name, bases, attrs)

# 构建一个形如"?, ?, ?"的字符串，num表示其中的'?'个数
def create_args_string(num):
    L = []
    while num > 0:
        L.append('?')
        num -= 1
    return ', '.join(L)

# Field类，负责保存数据库表的字段名、字段类型、是否主键、默认值等信息
class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

# 在Field的基础上，进一步定义各种类型的Field
class StringField(Field):
    def __init__(self, name=None, column_type='varchar(256)', primary_key=False, default=None):
        super().__init__(name, column_type, primary_key, default)

class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

# 定义ORM映射的基类Model
# 定义类时，传入关键字metaclass，指示Python在创建Model时，要通过ModelMetaclass.__new__()来创建
class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def getValue(self, key):
        return getattr(self, key, None)
    
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.info('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value
    
    # 获取所有满足条件的记录
    # @classmethod修饰的函数可以通过类或实例调用，第一个参数cls表示类本身，可以用来调用类的属性、方法，也可以用来实例化对象
    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderby = kw.get('orderby', None)
        if orderby:
            sql.append('order by')
            sql.append(orderby)
        limit = kw.get('limit', None)
        if limit:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                # extend()函数用于在列表末尾添加另一列表中的所有值
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        # cls(**r)用来创建类的实例，cls代表类本身，因此cls(**r)相当于Model(**r)
        # **可以将dict中的所有key-value作为关键字参数进行传递，因此(**r)相当于(x=1, y=2, ...)
        # cls(**r)最终相当于Model(x=1, y=2, ...)，满足Model类__init__()方法对参数的要求，可以创建出Model类的实例
        return [cls(**r) for r in rs]
    
    # 获取单条满足主键的记录
    @classmethod
    async def find(cls, pk):
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
    
    # 获取满足条件的记录数
    @classmethod
    async def findCount(cls, selectField, where=None, args=None):
        sql = ['select count(`%s`) _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return 0
        return rs[0]['_num_']
    
    # 保存数据
    async def save(self):
        # 注意map(function, iterable, ...)函数的用法
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)
        return rows
    
    # 更新数据
    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)
        return rows
    
    # 删除数据
    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)
        return rows