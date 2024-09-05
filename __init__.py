# __init__.py
import nonebot
from nonebot import get_driver, require
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

# 导入其他模块
from .character_manager import CharacterManager
from .config import Config, plugin_config
from .db.database import init_database
from .db.user_info_service import save_user_info
from .group_config_manager import group_config_manager
from .handlers import message_handler, welcome_handler
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_processor import process_message
from .resource_loader import (character_card_loader, preset_loader,
                              worldbook_loader)
from .schedulers import check_inactive_chats, morning_greeting, scheduler

# 声明插件元数据
__plugin_meta__ = PluginMetadata(
    name="AI虚拟群友",
    description="基于大语言模型的AI虚拟群友插件",
    usage="自动参与群聊，无需额外命令",
    config=Config,
    extra={
        "version": "1.0.0",
        "author": "Your Name",
    },
)
# 加载配置
# 加载依赖插件
require("nonebot_plugin_datastore")
require("nonebot_plugin_txt2img")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_userinfo")
# 初始化组件
driver = get_driver()
character_manager = CharacterManager()
llm_generator.init()
# scheduler = require("nonebot_plugin_apscheduler").scheduler
# 版本检查
if not nonebot.__version__.startswith("2."):
    raise ValueError("本插件仅支持 Nonebot2")
# 插件初始化函数


@driver.on_startup
async def init_plugin():
    try:
        # 初始化数据库
        await init_database()
        # 初始化群组配置
        await group_config_manager.load_configs()
        # 初始化角色管理器
        await character_manager.load_characters()
        # 初始化世界书加载器
        worldbook_loader.load_resource("世界书条目示例")  # 加载默认世界书
        # 初始化预设加载器
        preset_loader.load_resource("预设示例")  # 加载默认预设
        # 设置机器人ID（假设只有一个机器人实例）
        bot = list(get_driver().bots.values())[0]
        await memory_manager.set_bot_id(bot)
        # 验证关键配置
        if not plugin_config.LLM_API_KEY:
            logger.warning("LLM API密钥未设置，部分功能可能无法正常工作")
        logger.info("AI虚拟群友插件初始化完成")
    except Exception as e:
        logger.error(f"AI虚拟群友插件初始化失败：{str(e)}")
        raise
# 注册事件处理器
driver.on_message()(message_handler)
driver.on_notice()(welcome_handler)
# # 注册定时任务
scheduler.add_job(morning_greeting, "cron", hour=8, minute=0)
scheduler.add_job(check_inactive_chats, "interval", minutes=30)
# 导出模块
__all__ = [
    "Config",
    "CharacterManager",
    "group_config_manager",
    "llm_generator",
    "memory_manager",
    "process_message",
    "save_user_info",
    "message_handler",
    "welcome_handler",
]
