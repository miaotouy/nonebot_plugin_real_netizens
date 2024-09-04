from nonebot import get_driver, require
from nonebot.adapters.onebot.v11 import Bot
from nonebot.plugin import PluginMetadata

# 导入其他模块
from .character_manager import CharacterManager
# 导入配置
from .config import Config
# 导入数据库相关模块
from .db.database import init_database
from .db.user_info_service import save_user_info
from .group_config_manager import group_config_manager
from .handlers import message_handler, welcome_handler
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_processor import process_message
from .schedulers import check_inactive_chats, morning_greeting

# 声明插件元数据
__plugin_meta__ = PluginMetadata(
    name="AI虚拟群友",
    description="基于大语言模型的AI虚拟群友插件",
    usage="自动参与群聊，无需额外命令",
    config=Config,
)
# 加载配置
global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
# 加载依赖插件
require("nonebot_plugin_datastore")
require("nonebot_plugin_txt2img")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_userinfo")
# 初始化组件
character_manager = CharacterManager(
    character_cards_dir=plugin_config.CHARACTER_CARDS_DIR)
llm_generator.init()
# 插件初始化函数


@get_driver().on_startup
async def init_plugin():
    # 初始化数据库
    await init_database()

    # 初始化群组配置
    await group_config_manager.load_configs()

    # 初始化角色管理器
    await character_manager.load_characters()

    # 设置机器人ID（假设只有一个机器人实例）
    bot = list(get_driver().bots.values())[0]
    await memory_manager.set_bot_id(bot)

    # 其他初始化逻辑...
    print("AI虚拟群友插件初始化完成")
# 注册事件处理器
get_driver().on_message()(message_handler)
get_driver().on_notice()(welcome_handler)
# 注册定时任务
scheduler = require("nonebot_plugin_apscheduler").scheduler
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
]
