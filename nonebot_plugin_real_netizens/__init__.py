# nonebot_plugin_real_netizens/__init__.py
# 不要自动格式化
from nonebot import get_driver, require
import nonebot

# 初始化 NoneBot
nonebot.init()

# 声明依赖的插件
require("nonebot_plugin_localstore")
require("nonebot_plugin_datastore")
require("nonebot_plugin_txt2img")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_userinfo")
require("nonebot_plugin_saa")

from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .config import Config, plugin_config

# 从 nonebot_plugin_datastore.db 导入
from nonebot_plugin_datastore import get_plugin_data
from nonebot_plugin_datastore.db import post_db_init

# 获取 PluginData 对象
plugin_data = get_plugin_data("nonebot_plugin_real_netizens")

# 在此处调用 init_models
from .db.models import init_models
init_models(plugin_data)

# 现在可以安全地导入 character_manager 了
from .character_manager import character_manager, CharacterManager
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

if not nonebot.__version__.startswith("2."):
    raise ValueError("本插件仅支持 NoneBot2")

driver = get_driver()

@driver.on_bot_connect
async def _(bot: Bot):
    await init_plugin()

@post_db_init  # 使用 post_db_init 确保在数据库初始化后运行的函数
async def initialize_db():
    await plugin_data.Model.metadata.create_all(bind=plugin_data.engine)
