# schedulers.py
import time

from nonebot import get_driver, require

from .character_manager import character_manager
from .config import Config, plugin_config
from .group_config_manager import group_config_manager
from .memory_manager import memory_manager
from .message_builder import MessageBuilder
from .message_processor import process_message

scheduler = require("nonebot_plugin_apscheduler").scheduler


@scheduler.scheduled_job("cron", hour=int(plugin_config.MORNING_GREETING_TIME.split(":")[0]), minute=int(plugin_config.MORNING_GREETING_TIME.split(":")[1]))
async def morning_greeting():
    """早安问候定时任务"""
    if plugin_config.ENABLE_SCHEDULER:
        # 遍历所有机器人实例
        for bot_id, bot in get_driver().bots.items():
            for group_id in group_config_manager.get_all_groups():
                group_config = group_config_manager.get_group_config(group_id)
                character_id = group_config.character_id
                if not character_id:
                    continue
                message_builder = MessageBuilder(
                    preset_name=group_config.preset_name,
                    worldbook_names=group_config.worldbook_names,
                    character_id=character_id
                )
                greeting, _ = await process_message({"group_id": group_id}, message_builder, character_manager)
                if greeting:
                    await bot.send_group_msg(group_id=group_id, message=greeting)


@scheduler.scheduled_job("interval", minutes=30)
async def check_inactive_chats():
    """冷场检测定时任务"""
    if plugin_config.ENABLE_SCHEDULER:
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
                    preset_name=group_config.preset_name,
                    worldbook_names=group_config.worldbook_names,
                    character_id=character_id
                )
                revival_msg, _ = await process_message({"group_id": group_id}, message_builder, character_manager)
                if revival_msg:
                    await bot.send_group_msg(group_id=group_id, message=revival_msg)
