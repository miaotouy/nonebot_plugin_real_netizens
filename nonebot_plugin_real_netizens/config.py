# config.py
import os
from pathlib import Path
from typing import List

import yaml
from nonebot import get_driver
from pydantic import BaseSettings, Field

from .logger import logger


class Config(BaseSettings):
    # API 配置
    LLM_API_BASE: str = Field(
        default="https://api.openai.com", env="LLM_API_BASE",
        description="LLM API的基础URL"
    )
    LLM_API_KEY: str = Field(
        default="", env="LLM_API_KEY",
        description="LLM API的访问密钥"
    )
    LLM_PROXY_SERVER: str = Field(
        default="", env="LLM_PROXY_SERVER",
        description="LLM API的代理服务器地址（如果需要）(但是暂未实现该功能)"
    )
    # LLM 模型配置
    LLM_MODEL: str = Field(
        default="gemini-1.5-pro-001",
        description="使用的LLM模型名称"
    )
    LLM_MAX_TOKENS: int = Field(
        default=4096,
        description="LLM生成的最大token数"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        description="LLM生成的温度参数，控制输出的随机性（0.0-1.0）"
    )
    RESPONSE_TIMEOUT: int = Field(
        default=30,
        description="API调用超时时间（秒）"
    )
    # 触发配置
    TRIGGER_PROBABILITY: float = Field(
        default=0.5,
        description="AI主动发言的概率（0.0-1.0）"
    )
    TRIGGER_MESSAGE_INTERVAL: int = Field(
        default=5,
        description="触发AI主动发言的消息间隔数"
    )
    CONTEXT_MESSAGE_COUNT: int = Field(
        default=30,
        description="保留的上下文消息数量"
    )
    # 用户和群组配置
    SUPERUSERS: List[str] = Field(
        default_factory=list, env="SUPERUSERS",
        description="超级用户的QQ号列表"
    )
    ENABLED_GROUPS: List[int] = Field(
        default_factory=list, env="ENABLED_GROUPS",
        description="启用插件的群号列表"
    )
    # 资源目录配置
    CHARACTER_CARDS_DIR: str = Field(
        default="res/character",
        description="角色卡片目录路径"
    )
    PRESET_DIR: str = Field(
        default="res/preset",
        description="预设文件目录路径"
    )
    WORLD_INFO_DIR: str = Field(
        default="res/world",
        description="世界信息文件目录路径"
    )
    IMAGE_SAVE_PATH: str = Field(
        default="data/images",
        description="图片保存路径"
    )
    # 默认资源配置
    DEFAULT_WORLDBOOK: str = Field(
        default="世界书条目示例", description="默认世界书名称"
    )
    DEFAULT_PRESET: str = Field(
        default="预设示例", description="默认预设名称"
    )
    DEFAULT_CHARACTER_ID: str = Field(
        default="nolll", description="默认角色ID"
    )
    # 定时任务开关
    ENABLE_SCHEDULER: bool = Field(
        default=True, description="是否启用定时任务"
    )
    # 其他配置项
    INACTIVE_THRESHOLD: int = Field(
        default=3600,
        description="群聊不活跃阈值（秒）"
    )
    MORNING_GREETING_TIME: str = Field(
        default="08:30",
        description="早安问候时间"
    )
    DATABASE_URL: str = Field(
        default="sqlite:///friend_bot.db", env="DATABASE_URL",
        description="数据库连接URL"
    )
    LOG_LEVEL: str = Field(
        default="INFO", env="LOG_LEVEL",
        description="日志级别"
    )
    CHAT_HISTORY_LIMIT: int = Field(
        default=3000,
        description="聊天历史记录最大保存条数"
    )
    MAX_RETRIES: int = Field(
        default=3, env="MAX_RETRIES",
        description="API调用最大重试次数"
    )
    RETRY_INTERVAL: float = Field(
        default=1.0, env="RETRY_INTERVAL",
        description="API调用重试间隔（秒）"
    )
    CACHE_EXPIRY_TIME: int = Field(
        default=1800,
        description="缓存过期时间（秒）(未实装)"
    )
    CHAT_COOLDOWN: int = Field(
        default=10,
        description="两次回复之间的冷却时间（秒）(未实装)"
    )
    MAX_DAILY_INTERACTIONS: int = Field(
        default=100,
        description="每日最大交互次数限制(未实装)"
    )
    VERSION: str = Field(
        default="1.0.0",
        description="插件版本号"
    )
    DEBUG_MODE: bool = Field(
        default=False, env="DEBUG_MODE",
        description="是否启用调试模式"
    )
    # 日志相关配置
    LOG_TO_FILE: bool = Field(
        default=False, 
        env="LOG_TO_FILE", 
        description="是否将日志输出到文件"
    )
    LOG_DIR: Path = Field(
        default=Path(os.getcwd()) / "logs",
        env="LOG_DIR",
        description="日志文件存储目录"
    )
    LOG_FILE_NAME: str = Field(
        default="nonebot_plugin_real_netizens.log",
        env="LOG_FILE_NAME",
        description="日志文件名"
    )
    LOG_FILE_MAX_SIZE: int = Field(
        default=10,
        env="LOG_FILE_MAX_SIZE",
        description="单个日志文件的最大大小（MB）"
    )
    LOG_FILE_BACKUP_COUNT: int = Field(
        default=5,
        env="LOG_FILE_BACKUP_COUNT",
        description="保留的日志文件备份数量"
    )

    @classmethod
    def from_yaml(cls, file_path: str = "config/friend_config.yml") -> "Config":
        """从 YAML 文件加载配置。"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {file_path} 未找到，使用默认配置。")
            yaml_data = {}
        except yaml.YAMLError as e:
            logger.error(f"解析配置文件 {file_path} 时出错：{e}")
            yaml_data = {}
        # 使用默认配置初始化
        config = cls()
        # 使用yaml_data更新配置值
        if yaml_data:
            for field in cls.__fields__.values():
                # 如果yaml_data中没有该字段，则写入默认值和注释
                if field.name not in yaml_data and field.name not in ["LLM_API_KEY", "LLM_API_BASE"]:
                    yaml_data[field.name] = field.default
                    # 将字段描述信息作为注释添加到YAML
                    if field.description:
                        yaml_data[field.name] = f"# {field.description}\n{yaml_data[field.name]}"
            # 使用更新后的yaml_data更新配置对象
            config = config.copy(update=yaml_data)
            config.update_forward_refs()
        # 从环境变量加载配置，这将覆盖YAML中的配置
        env_config = cls.parse_obj(get_driver().config)
        for field in cls.__fields__:
            if field in env_config.__dict__:
                setattr(config, field, getattr(env_config, field))
        # 将当前配置写回YAML文件（不包括API配置）
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                export_data = {k: v for k,
                               v in config.dict().items() if k not in ["LLM_API_KEY", "LLM_API_BASE"]}
                yaml.dump(export_data, f)
        except Exception as e:
            print(f"写入配置文件时出错：{e}")
        return config

    @property
    def LOG_FILE_PATH(self) -> str:
        return str(self.LOG_DIR / self.LOG_FILE_NAME)

    class Config:
        extra = "allow"


def get_plugin_config() -> Config:
    return plugin_config


# 全局配置对象
plugin_config = Config.from_yaml()
