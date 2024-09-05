# config.py
from typing import List

import yaml
from nonebot import get_driver
from pydantic import BaseSettings, Field


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
        description="LLM API的代理服务器地址（如果需要）"
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
    # 其他配置项
    DEFAULT_CHARACTER_ID: str = Field(
        default="default",
        description="默认角色ID"
    )
    INACTIVE_THRESHOLD: int = Field(
        default=3600,
        description="群聊不活跃阈值（秒）"
    )
    MORNING_GREETING_TIME: str = Field(
        default="08:00",
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
    # 新增配置项
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
