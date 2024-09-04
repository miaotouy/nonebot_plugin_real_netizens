# config.py
from typing import List

import yaml
from nonebot import get_driver
from pydantic import BaseSettings, Field


class Config(BaseSettings):
    # 从 .env 文件获取 API 配置
    LLM_API_BASE: str = Field(default="https://api.openai.com", env="LLM_API_BASE")
    LLM_API_KEY: str = Field(default="", env="LLM_API_KEY")
    # 其他配置项保持不变
    LLM_MODEL: str = "gemini-1.5-pro-001"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7
    # 触发概率（0 到 1 之间）
    TRIGGER_PROBABILITY: float = 0.5
    # 触发消息数量间隔
    TRIGGER_MESSAGE_INTERVAL: int = 5
    # 保留的上下文消息数量
    CONTEXT_MESSAGE_COUNT: int = 30
    # 管理员账号获取
    superusers: List[str] = Field(default_factory=list, env="SUPERUSERS")
    @classmethod
    def from_yaml(cls, file_path: str = "config/friend_config.yml") -> "Config":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                # 从 .env 获取 API 配置
                env_config = cls.parse_obj(get_driver().config)
                data['LLM_API_BASE'] = env_config.LLM_API_BASE
                data['LLM_API_KEY'] = env_config.LLM_API_KEY
                return cls.parse_obj(data)
        except FileNotFoundError:
            print(f"配置文件 {file_path} 未找到，使用默认配置。")
            return cls()
        except yaml.YAMLError as e:
            print(f"解析配置文件 {file_path} 时出错：{e}")
            return cls()
# 全局配置对象
plugin_config = Config.parse_obj(get_driver().config)
