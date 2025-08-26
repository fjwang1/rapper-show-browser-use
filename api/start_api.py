#!/usr/bin/env python3
# @file purpose: API服务启动脚本
"""
Rapper演出搜索API启动脚本

这个脚本用于启动FastAPI服务器，提供更灵活的配置选项和启动方式。
支持通过命令行参数或环境变量配置服务器。
"""

import argparse
import os
import sys
import uvicorn

from config import get_config


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="启动Rapper演出搜索API服务"
    )
    
    config = get_config()
    
    parser.add_argument(
        '--host',
        type=str,
        default=config.HOST,
        help=f'服务器主机地址 (默认: {config.HOST})'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=config.PORT,
        help=f'服务器端口 (默认: {config.PORT})'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        default=config.RELOAD,
        help='启用自动重载 (开发模式)'
    )
    
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='禁用自动重载 (生产模式)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
        default=config.LOG_LEVEL,
        help=f'日志级别 (默认: {config.LOG_LEVEL})'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='工作进程数量 (默认: 1)'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 处理reload参数
    reload = args.reload
    if args.no_reload:
        reload = False
    
    # 设置环境变量
    os.environ['HOST'] = args.host
    os.environ['PORT'] = str(args.port)
    os.environ['LOG_LEVEL'] = args.log_level
    os.environ['RELOAD'] = str(reload).lower()
    
    print(f"🎤 启动Rapper演出搜索API服务...")
    print(f"📍 地址: http://{args.host}:{args.port}")
    print(f"📋 API文档: http://{args.host}:{args.port}/docs")
    print(f"🔧 重载模式: {'开启' if reload else '关闭'}")
    print(f"📝 日志级别: {args.log_level}")
    
    if args.workers > 1:
        print(f"👥 工作进程: {args.workers}")
    
    print("=" * 50)
    
    try:
        # 启动服务器
        uvicorn.run(
            "main:app", # 加载main.py中的app对象
            host=args.host,
            port=args.port,
            reload=reload,
            log_level=args.log_level,
            workers=args.workers if not reload else 1,  # reload模式下不支持多worker
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动服务器时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
