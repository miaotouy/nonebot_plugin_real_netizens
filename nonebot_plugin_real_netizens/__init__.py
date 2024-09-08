# nonebot_plugin_real_netizens/__init__.py
# 禁止自动格式化！！！
from nonebot import get_driver, require

require("nonebot_plugin_localstore")
require("nonebot_plugin_datastore")
require("nonebot_plugin_txt2img")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_userinfo")
require("nonebot_plugin_saa")

import nonebot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from .config import Config, plugin_config
from .character_manager import character_manager
from .group_config_manager import group_config_manager
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_processor import message_processor
from .db.user_info_service import save_user_info
from .main import init_plugin


__plugin_meta__ = PluginMetadata(
    name="AI虚拟群友",
    description="基于大语言模型的AI虚拟群友插件",
    usage="自动参与群聊，无需额外命令",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "1.0.0",
        "author": "miaotouy",
    },
)
# 版本检查
if not nonebot.__version__.startswith("2."):
    raise ValueError("本插件仅支持 Nonebot2")

driver = get_driver()
driver.on_startup(init_plugin)
