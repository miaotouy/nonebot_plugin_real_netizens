# schedulers.py
import time

from nonebot import get_driver, require

from .character_manager import character_manager
from .config import Config
from .group_config_manager import group_config_manager
from .memory_manager import memory_manager
from .message_builder import MessageBuilder
from .message_processor import MessageProcessor, message_processor

# 获取调度器实例
scheduler = require("nonebot_plugin_apscheduler").scheduler
plugin_config = Config.parse_obj(get_driver().config)
@scheduler.scheduled_job("cron", hour=int(plugin_config.MORNING_GREETING_TIME.split(":")[0]), minute=int(plugin_config.MORNING_GREETING_TIME.split(":")[1]))
async def morning_greeting():
    bot = get_driver().bots.values()[0]  # 获取第一个机器人实例
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        # 如果没有设置角色，则使用默认角色
        if not character_id:
            character_id = plugin_config.DEFAULT_CHARACTER_ID
        # 获取预设名称和世界书名称列表
        preset_name = group_config.preset_name
        worldbook_names = group_config.worldbook_names
        message_builder = MessageBuilder(
            preset_name=preset_name,
            worldbook_names=worldbook_names,
            character_id=character_id
        )
        greeting = await MessageProcessor(None, [], message_builder,  {"user": "群友", "char": character_manager.get_character_info(
            character_id, "name")})
        if greeting:
            await bot.send_group_msg(group_id=group_id, message=greeting)
@scheduler.scheduled_job("interval", minutes=30)
async def check_inactive_chats():
    bot = get_driver().bots.values()[0]
    current_time = time.time()
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        # 如果没有设置角色，则使用默认角色
        if not character_id:
            character_id = plugin_config.DEFAULT_CHARACTER_ID
        last_message_time = await memory_manager.get_last_message_time(group_id)
        if current_time - last_message_time > group_config.inactive_threshold:
            # 获取预设名称和世界书名称列表
            preset_name = group_config.preset_name
            worldbook_names = group_config.worldbook_names
            message_builder = MessageBuilder(
                preset_name=preset_name,
                worldbook_names=worldbook_names,
                character_id=character_id
            )
            # 调用 message_processor 实例的 process 方法
            revival_msg = await message_processor.process(None, [], message_builder, {"user": "群友", "char": character_manager.get_character_info(
                character_id, "name")})
            if revival_msg:
                await bot.send_group_msg(group_id=group_id, message=revival_msg)
