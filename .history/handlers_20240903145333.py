# handlers.py
import random
from nonebot import on_message, on_notice, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupIncreaseNoticeEvent
from nonebot.typing import T_State
from .config import Config
from .message_processor import process_message
from .memory_manager import memory_manager
from .group_config_manager import group_config_manager
from .message_builder import MessageBuilder
from .character_manager import character_manager
plugin_config = Config.parse_obj(get_driver().config)
# 消息处理器
message_handler = on_message(priority=5)
@message_handler.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return  # 如果没有配置角色，则不处理消息
    message_builder = MessageBuilder(
        preset_file=group_config.preset_path,
        world_info_files=group_config.world_info_paths,
        character_id=character_id
    )
    response, should_reply = await process_message(event, message_builder, character_manager)
    # 根据概率和消息数量间隔触发回复
    if should_reply and random.random() < plugin_config.TRIGGER_PROBABILITY and event.message_id % plugin_config.TRIGGER_MESSAGE_INTERVAL == 0:
        await bot.send(event=event, message=response)
# 欢迎新成员
welcome_handler = on_notice(priority=5)
@welcome_handler.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = event.group_id
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return  # 如果没有配置角色，则不处理消息
    message_builder = MessageBuilder(
        preset_file=group_config.preset_path,
        world_info_files=group_config.world_info_paths,
        character_id=character_id
    )
    welcome_msg, _ = await process_message(event, message_builder, character_manager)
    if welcome_msg:
        await bot.send(event=event, message=welcome_msg)
