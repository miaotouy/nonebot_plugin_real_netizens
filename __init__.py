# __init__.py
from nonebot import get_driver, on_startup
from nonebot.adapters.onebot.v11 import Bot

from .character_manager import CharacterManager
from .config import Config
from .group_config_manager import group_config_manager
from .handlers import message_handler, welcome_handler
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_processor import process_message
from .schedulers import check_inactive_chats, morning_greeting

# 加载配置
plugin_config = Config.parse_obj(get_driver().config)
# 初始化组件
character_manager = CharacterManager(
    character_cards_dir=plugin_config.character_cards_dir)
llm_generator.init()


@on_startup
async def init_plugin():
    # 获取第一个 Bot 实例并设置 bot_id
    bot = list(get_driver().bots.values())[0]
    await memory_manager.set_bot_id(bot)
    # 初始化其他需要在启动时设置的组件
    # 例如：加载群组配置、初始化角色管理器等
    await group_config_manager.load_configs()
    await character_manager.load_characters()
