from typing import Dict, Any
from pydantic import BaseSettings, Field
from nonebot import get_driver

import yaml
class Config(BaseSettings):
    LLM_API_BASE: str = "https://api.openai.com"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-pro-001"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7
    # 角色设定
    CHARACTER_CONFIG: Dict[str, Any] = {
        "personality": "友好、幽默、略带调皮",
        "interests": "科技、动漫、美食"
    }
    # 触发概率（0 到 1 之间）
    TRIGGER_PROBABILITY: float = 0.5
    # 触发消息数量间隔
    TRIGGER_MESSAGE_INTERVAL: int = 5
    # 保留的上下文消息数量
    CONTEXT_MESSAGE_COUNT: int = 3
    @classmethod
    def from_yaml(cls, file_path: str = "config/friend_config.yml") -> "Config":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return cls.parse_obj(data)
        except FileNotFoundError:
            print(f"配置文件 {file_path} 未找到，使用默认配置。")
            return cls()
        except yaml.YAMLError as e:
            print(f"解析配置文件 {file_path} 时出错：{e}")
            return cls()
