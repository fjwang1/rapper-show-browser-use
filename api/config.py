# @file purpose: API服务配置文件
"""
API服务配置

这个文件定义了API服务的各种配置选项，包括DeepSeek API密钥、
服务器设置、超时配置等。
"""

import os

class Config:
    """API服务配置类"""
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = os.getenv(
        'DEEPSEEK_API_KEY', 
        'sk-cd4480658d354f9e91d96b66a47cda4a'
    )
    DEEPSEEK_BASE_URL: str = os.getenv(
        'DEEPSEEK_BASE_URL',
        'https://api.deepseek.com/v1'
    )
    DEEPSEEK_MODEL: str = os.getenv(
        'DEEPSEEK_MODEL',
        'deepseek-chat'
    )
    
    # 服务器配置
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8000'))
    RELOAD: bool = os.getenv('RELOAD', 'true').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'info')
    
    # 搜索配置
    DEFAULT_TIMEOUT_SECONDS: int = int(os.getenv('DEFAULT_TIMEOUT_SECONDS', '300'))
    MAX_TIMEOUT_SECONDS: int = int(os.getenv('MAX_TIMEOUT_SECONDS', '600'))
    MIN_TIMEOUT_SECONDS: int = int(os.getenv('MIN_TIMEOUT_SECONDS', '30'))
    
    # browser-use配置
    USE_VISION: bool = os.getenv('USE_VISION', 'false').lower() == 'true'
    SAVE_CONVERSATIONS: bool = os.getenv('SAVE_CONVERSATIONS', 'true').lower() == 'true'
    CONVERSATION_DIR: str = os.getenv('CONVERSATION_DIR', './conversations')
    
    # 日志配置
    BROWSER_USE_LOG_LEVEL: str = os.getenv('BROWSER_USE_LOG_LEVEL', 'info')


# 创建全局配置实例
config = Config()


def get_config() -> Config:
    """获取配置实例"""
    return config
