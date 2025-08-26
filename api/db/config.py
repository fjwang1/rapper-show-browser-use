#!/usr/bin/env python3
# @file purpose: 数据库配置读取与封装
"""
提供MySQL配置读取能力，默认从环境变量读取；供API模块使用。
"""

import os
from dataclasses import dataclass


@dataclass
class MySQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"


def get_mysql_config() -> MySQLConfig:
    return MySQLConfig(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "rapper"),
        charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    )


