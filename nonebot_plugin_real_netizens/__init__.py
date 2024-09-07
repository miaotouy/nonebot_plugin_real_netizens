#nonebot_plugin_real_netizens\__init__.py
# 这个不要用自动格式化！！！
import nonebot
from nonebot import get_driver, require
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
# 声明插件元数据
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
# 声明依赖插件
require("nonebot_plugin_localstore")
require("nonebot_plugin_datastore")
require("nonebot_plugin_txt2img")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_userinfo")
from .character_manager import character_manager
from .config import Config, plugin_config
from .db.database import init_database
from .db.user_info_service import save_user_info
from .group_config_manager import group_config_manager
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_processor import message_processor
from .schedulers import check_inactive_chats, morning_greeting, scheduler
# 初始化组件
driver = get_driver()
# 版本检查
if not nonebot.__version__.startswith("2."):
    raise ValueError("本插件仅支持 Nonebot2")
# 插件初始化函数
@driver.on_startup
async def init_plugin():
    from .character_manager import character_manager
    from .group_config_manager import group_config_manager
    from .llm_generator import llm_generator
    from .memory_manager import memory_manager
    from .message_processor import message_processor
    from .resource_loader import (character_card_loader, preset_loader,
                                  worldbook_loader)
    try:
        await init_database()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败：{str(e)}")
        raise
    try:
        await group_config_manager.load_configs()
        logger.info("群组配置加载成功")
    except Exception as e:
        logger.error(f"群组配置加载失败：{str(e)}")
        raise
    try:
        await character_manager.load_characters()
        logger.info("角色管理器初始化成功")
    except Exception as e:
        logger.error(f"角色管理器初始化失败：{str(e)}")
        raise
    try:
        await worldbook_loader.load_resource("世界书条目示例")
        await preset_loader.load_resource("预设示例")
        logger.info("资源加载成功")
    except Exception as e:
        logger.error(f"资源加载失败：{str(e)}")
        raise
    try:
        bot = list(get_driver().bots.values())[0]
        await memory_manager.set_bot_id(bot)
        logger.info("机器人ID设置成功")
    except Exception as e:
        logger.error(f"机器人ID设置失败：{str(e)}")
        raise
    if not plugin_config.LLM_API_KEY:
        logger.warning("LLM API密钥未设置，部分功能可能无法正常工作")
    logger.info("AI虚拟群友插件初始化完成")
    # 注册事件处理器
    driver.on_message()(message_processor.process_message)
    # 注册定时任务
    if plugin_config.ENABLE_SCHEDULER:
        scheduler.add_job(morning_greeting, "cron", hour=int(
            plugin_config.MORNING_GREETING_TIME.split(":")[0]), minute=int(plugin_config.MORNING_GREETING_TIME.split(":")[1]))
        scheduler.add_job(check_inactive_chats, "interval", minutes=30)
# 导出模块
__all__ = [
    "Config",
    "character_manager",
    "group_config_manager",
    "llm_generator",
    "memory_manager",
    "message_processor",
    "save_user_info",
]
