#!/usr/bin/env python3
# @file purpose: 数据存取仓储，包含表结构、清理与写入
"""
提供 rapper_performances 表的初始化、清理过期与插入方法。
"""

from typing import List, Dict, Any, Optional
from datetime import date

from .connection import get_connection


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `rapper_performances` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `rapper_name` VARCHAR(50) NOT NULL COMMENT '歌手名字',
  `performance_date` DATE NOT NULL COMMENT '演出日期(用于过期清理)',
  `performance_time_text` VARCHAR(100) NULL COMMENT '时间原文(如有时段/范围)',
  `venue` VARCHAR(255) NOT NULL COMMENT '演出场地',
  `address` VARCHAR(255) NOT NULL COMMENT '演出地址',
  `price_presale` DECIMAL(10,2) NULL COMMENT '预售价格',
  `price_regular` DECIMAL(10,2) NULL COMMENT '正价',
  `price_vip` DECIMAL(10,2) NULL COMMENT 'VIP价格',
  `purchase_url` VARCHAR(512) NOT NULL COMMENT '购买链接',
  `guests_json` JSON NULL COMMENT '嘉宾(JSON数组，如 ["A","B"])',
  `source` VARCHAR(32) NOT NULL DEFAULT 'showstart' COMMENT '数据来源',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_rapper_date` (`rapper_name`, `performance_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
"""


def init_schema() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)


def cleanup_expired_by_rapper(rapper_name: str) -> int:
    """删除今天之前的记录，返回删除行数"""
    sql = (
        "DELETE FROM `rapper_performances` "
        "WHERE `rapper_name`=%s AND `performance_date` < CURDATE()"
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            rows = cur.execute(sql, (rapper_name,))
        return rows


def insert_performance_row(row: Dict[str, Any]) -> int:
    """插入一条演出记录（不去重）。返回受影响行数。"""
    sql = (
        "INSERT INTO `rapper_performances` ("
        "`rapper_name`, `performance_date`, `performance_time_text`, "
        "`venue`, `address`, `price_presale`, `price_regular`, `price_vip`, "
        "`purchase_url`, `guests_json`, `source`"
        ") VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, CAST(%s AS JSON), %s"
        ")"
    )
    params = (
        row.get("rapper_name"),
        row.get("performance_date"),
        row.get("performance_time_text"),
        row.get("venue"),
        row.get("address"),
        row.get("price_presale"),
        row.get("price_regular"),
        row.get("price_vip"),
        row.get("purchase_url"),
        row.get("guests_json", "[]"),
        row.get("source", "showstart"),
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            affected = cur.execute(sql, params)
        return affected


def insert_performances(performances: List[Dict[str, Any]], rapper_name: str) -> int:
    """批量插入，返回插入条数。"""
    count = 0
    for perf in performances:
        count += insert_performance_row(perf)
    return count


