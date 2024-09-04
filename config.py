# config.py
from typing import List

import yaml
from nonebot import get_driver
from pydantic import BaseSettings, Field


class Config(BaseSettings):
    # API 配置
    LLM_API_BASE: str = Field(
        default="https://api.openai.com", env="LLM_API_BASE")
    LLM_API_KEY: str = Field(default="", env="LLM_API_KEY")
    LLM_PROXY_SERVER: str = Field(default="", env="LLM_PROXY_SERVER")
    # LLM 模型配置
    LLM_MODEL: str = "gemini-1.5-pro-001"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7
    RESPONSE_TIMEOUT: int = 30  # API 调用超时时间（秒）
    # 触发配置
    TRIGGER_PROBABILITY: float = 0.5
    TRIGGER_MESSAGE_INTERVAL: int = 5
    CONTEXT_MESSAGE_COUNT: int = 30
    # 用户和群组配置
    SUPERUSERS: List[str] = Field(default_factory=list, env="SUPERUSERS")
    ENABLED_GROUPS: List[int] = Field(
        default_factory=list, env="ENABLED_GROUPS")
    # 资源目录配置
    CHARACTER_CARDS_DIR: str = "res/character"
    PRESET_DIR: str = "res/preset"
    WORLD_INFO_DIR: str = "res/world"
    # 其他配置项
    DEFAULT_CHARACTER_ID: str = "default"
    INACTIVE_THRESHOLD: int = 3600  # 群聊不活跃阈值（秒）
    MORNING_GREETING_TIME: str = "08:00"
    DATABASE_URL: str = Field(
        default="sqlite:///friend_bot.db", env="DATABASE_URL")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    CHAT_HISTORY_LIMIT: int = 1000  # 聊天历史记录最大保存条数
    # 新增配置项
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    RETRY_INTERVAL: float = Field(default=1.0, env="RETRY_INTERVAL")  # 单位: 秒
    IMPRESSION_UPDATE_INTERVAL: int = 3600  # 更新用户印象的时间间隔（秒）
    MAX_IMPRESSION_LENGTH: int = 500  # 用户印象的最大长度限制
    CHAT_COOLDOWN: int = 10  # 两次回复之间的冷却时间（秒）
    MAX_DAILY_INTERACTIONS: int = 100  # 每日最大交互次数限制
    LLM_AVAILABLE_MODELS: List[str] = ["gpt-3.5-turbo", "gemini-1.5-pro-001"]
    VERSION: str = "1.0.0"
    DEBUG_MODE: bool = Field(default=False, env="DEBUG_MODE")

    @classmethod
    def from_yaml(cls, file_path: str = "config/friend_config.yml") -> "Config":
        # 先创建一个默认配置对象
        config = cls()
        # 尝试从YAML文件加载配置
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    # 更新配置
                    for key, value in yaml_data.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
        except FileNotFoundError:
            print(f"配置文件 {file_path} 未找到，使用默认配置。")
        except yaml.YAMLError as e:
            print(f"解析配置文件 {file_path} 时出错：{e}")
        # 从环境变量加载配置，这将覆盖YAML中的配置
        env_config = cls.parse_obj(get_driver().config)
        for field in cls.__fields__:
            if field in env_config.__dict__:
                setattr(config, field, getattr(env_config, field))
        # 将当前配置写回YAML文件
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(config.dict(), f)
        except Exception as e:
            print(f"写入配置文件时出错：{e}")
        return config


# 全局配置对象
plugin_config = Config.from_yaml()
