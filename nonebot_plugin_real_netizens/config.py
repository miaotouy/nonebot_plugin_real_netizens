# nonebot_plugin_real_netizens\config.py

from pathlib import Path
import os
from typing import Any, Dict, List, Optional

from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseSettings, Field


class Config(BaseSettings):
    """插件配置类"""

    # --- API 配置 ---
    LLM_API_BASE: str = Field(
        default="https://api.openai.com", env="LLM_API_BASE",
        description="LLM API的基础URL"
    )
    LLM_API_KEY: str = Field(
        default="", env="LLM_API_KEY",
        description="LLM API的访问密钥"
    )
    MAX_RETRIES: int = Field(
        default=3, env="MAX_RETRIES",
        description="API调用最大重试次数"
    )
    RETRY_INTERVAL: float = Field(
        default=1.0, env="RETRY_INTERVAL",
        description="API调用重试间隔（秒）"
    )
    RESPONSE_TIMEOUT: int = Field(
        default=30,
        description="API调用超时时间（秒）"
    )

    # --- LLM 模型配置 ---
    LLM_MODEL: str = Field(
        default="gemini-1.5-pro-exp-0827",
        description="使用的LLM模型名称"
    )
    FAST_LLM_MODEL: str = Field(
        default="gemini-1.5-flash-exp-0827",
        description="用于快速回复的 LLM 模型"
    )
    VL_LLM_MODEL: str = Field(
        default="qwen2-vl-7b",
        description="用于图像识别的多模态 LLM 模型"
    )
    LLM_MAX_TOKENS: int = Field(
        default=2048,
        description="LLM生成的最大token数"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        description="LLM生成的温度参数，控制输出的随机性（0.0-2.0）",
        ge=0.0, le=2.0
    )
    MAX_IMAGE_SIZE: int = Field(
        default=512,
        description="发送给 LLM 的图片最大尺寸（像素）, 建议不超过 1024"
    )

    # --- 触发配置 ---
    TRIGGER_PROBABILITY: float = Field(
        default=0.5,
        description="AI主动发言的概率（0.0-1.0）",
        ge=0.0, le=1.0
    )
    TRIGGER_MESSAGE_INTERVAL: int = Field(
        default=5,
        description="触发AI主动发言的消息间隔数"
    )
    CONTEXT_MESSAGE_COUNT: int = Field(
        default=30,
        description="保留的上下文消息数量"
    )
    CHAT_HISTORY_LIMIT: int = Field(
        default=3000,
        description="聊天历史记录最大保存条数"
    )

    # --- 用户和群组配置 ---
    SUPERUSERS: List[str] = Field(
        default_factory=list, env="SUPERUSERS",
        description="超级用户的QQ号列表"
    )
    ENABLED_GROUPS: List[int] = Field(
        default_factory=list, env="ENABLED_GROUPS",
        description="启用插件的群号列表"
    )

    # --- 资源目录配置 ---
    RES_PATH: str = Field(
        default="res",
        description="资源文件根目录路径"
    )
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

    # --- 默认资源配置 ---
    DEFAULT_WORLDBOOK: str = Field(
        default="世界书条目示例", description="默认世界书名称"
    )
    DEFAULT_PRESET: str = Field(
        default="预设示例", description="默认预设名称"
    )
    DEFAULT_CHARACTER_ID: str = Field(
        default="nolll", description="默认角色ID"
    )

    # --- 定时任务配置 ---
    ENABLE_SCHEDULER: bool = Field(
        default=True, description="是否启用定时任务"
    )
    MORNING_GREETING_TIME: str = Field(
        default="08:30",
        description="早安问候时间"
    )

    # --- 其他配置 ---
    DATABASE_URL: str = Field(
        default="sqlite:///friend_bot.db", env="DATABASE_URL",
        description="数据库连接URL"
    )
    INACTIVE_THRESHOLD: int = Field(
        default=3600,
        description="群聊不活跃阈值（秒）"
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

    # --- 日志相关配置 ---
    LOG_LEVEL: str = Field(
        default="INFO", env="LOG_LEVEL",
        description="日志级别"
    )
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
    def from_yaml(cls, file_path: str = "nonebot_plugin_real_netizens/config/friend_config.yml", new_config: Optional[dict] = None, write_config: bool = False) -> "Config":
        config = cls()

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_data = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split(':', 1)
                        yaml_data[key.strip()] = value.strip()

            for key, value in yaml_data.items():
                if key in config.__fields__:
                    setattr(config, key, value)

        if new_config:
            for key, value in new_config.items():
                if key in config.__fields__:
                    setattr(config, key, value)

        if write_config:
            update_yaml_config(file_path, {field: getattr(
                config, field) for field in config.__fields__})

        return config

    @property
    def LOG_FILE_PATH(self) -> str:
        return str(self.LOG_DIR / self.LOG_FILE_NAME)

    class Config:  # type: ignore # noqa: F811
        extra = "allow"


def update_yaml_config(file_path: str, new_config: Dict[str, Any]):
    # 读取现有配置
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []

    # 创建一个新的配置内容
    new_lines = []
    processed_keys = set()

    # 处理现有行
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            new_lines.append(line)
        else:
            key = line.split(':')[0].strip()
            if key in new_config:
                new_lines.append(f"# {new_config[key].field_info.description}")
                new_lines.append(f"{key}: {format_value(new_config[key])}")
                processed_keys.add(key)
            else:
                new_lines.append(line)

    # 添加新的配置项
    for key, value in new_config.items():
        if key not in processed_keys:
            new_lines.append(f"# {value.field_info.description}")
            new_lines.append(f"{key}: {format_value(value)}")

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))


def format_value(value: Any) -> str:
    if isinstance(value, list):
        return '\n  - ' + '\n  - '.join(map(str, value))
    elif isinstance(value, str):
        return f"'{value}'"
    else:
        return str(value)


# 全局配置对象
plugin_config: Config = Config.from_yaml()
