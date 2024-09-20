# nonebot_plugin_real_netizens/__init__.py
import nonebot
from nonebot import get_driver, require

require("nonebot_plugin_localstore")
require("nonebot_plugin_datastore")
require("nonebot_plugin_txt2img")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_userinfo")
require("nonebot_plugin_saa")

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="AI虚拟群友",
    description="基于大语言模型驱动的AI虚拟群友插件",
    usage="自动参与群聊，无需额外命令",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "1.0.0",
        "author": "miaotouy",
    },
)

from .main import init_plugin

# 其他必要的导入
from .character_manager import character_manager
from .group_config_manager import group_config_manager
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_processor import message_processor

if not nonebot.__version__.startswith("2."):
    raise ValueError("本插件仅支持 NoneBot2")

driver = get_driver()


