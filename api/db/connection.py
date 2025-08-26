#!/usr/bin/env python3
# @file purpose: MySQL 连接与简单连接池
"""
提供获取 MySQL 连接的函数；使用 PyMySQL 简化依赖。
"""

import threading
from contextlib import contextmanager
# 避免静态检查在未安装依赖时报错，改为函数内部延迟导入

from .config import get_mysql_config


_local = threading.local()


def _create_connection():
    cfg = get_mysql_config()
    pymysql_module = __import__('pymysql')
    DictCursor = getattr(getattr(pymysql_module, 'cursors'), 'DictCursor')
    return pymysql_module.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset=cfg.charset,
        autocommit=False,
        cursorclass=DictCursor,
    )


@contextmanager
def get_connection():
    conn = getattr(_local, "conn", None)
    created_here = False
    if conn is None or not conn.open:
        conn = _create_connection()
        _local.conn = conn
        created_here = True
    try:
        yield conn
        if created_here:
            conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if created_here and conn:
            conn.close()
            _local.conn = None


