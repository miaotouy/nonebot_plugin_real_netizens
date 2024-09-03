# schedulers.py
import time
from nonebot import require, get_driver
from .config import Config
from .group_config_manager import group_config_manager
from .message_builder import MessageBuilder
from .character_manager import character_manager
from .message_processor import process_message
from .memory_manager import memory_manager
scheduler = require("nonebot_plugin_apscheduler").scheduler
plugin_config = Config.parse_obj(get_driver().config)
@scheduler.scheduled_job("cron", hour=8, minute=0)
async def morning_greeting():
    bot = get_driver().bots.values()[0]  # 获取第一个机器人实例
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        if not character_id:
            continue
        message_builder = MessageBuilder(
            preset_file=group_config.preset_path,
            world_info_files=group_config.world_info_paths,
            character_id=character_id
        )
        greeting, _ = await process_message({"group_id": group_id}, message_builder, character_manager)
        if greeting:
            await bot.send_group_msg(group_id=group_id, message=greeting)
@scheduler.scheduled_job("interval", minutes=30)
async def check_inactive_chats():
    bot = get_driver().bots.values()[0]
    current_time = time.time()
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        if not character_id:
            continue
        last_message_time = await memory_manager.get_last_message_time(group_id)
        if current_time - last_message_time > group_config.inactive_threshold:
            message_builder = MessageBuilder(
                preset_file=group_config.preset_path,
                world_info_files=group_config.world_info_paths,
                character_id=character_id
            )
            revival_msg, _ = await process_message({"group_id": group_id}, message_builder, character_manager)
            if revival_msg:
                await bot.send_group_msg(group_id=group_id, message=revival_msg)
