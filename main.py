# main.py
import logging
import random
import time
from typing import Any, Dict, List, Optional

from nonebot import get_driver, on_command, on_message, on_notice, require
from nonebot.adapters.onebot.v11 import (Bot, GroupIncreaseNoticeEvent,
                                         GroupMessageEvent, MessageSegment)
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot_plugin_datastore import get_session

from .character_manager import CharacterManager
from .config import Config
from .db.database import add_message, delete_old_messages, get_recent_messages
from .group_config_manager import GroupConfig, group_config_manager
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_builder import MessageBuilder
from .message_processor import process_message

logger = logging.getLogger(__name__)
global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
character_manager = CharacterManager(
    character_cards_dir=plugin_config.character_cards_dir)
llm_generator.init()
message_handler = on_message(priority=5)


@message_handler.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    user_id = event.user_id
    group_config: GroupConfig = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return
    message = event.get_message()
    # 保存消息到数据库
    async with get_session() as session:
        await add_message(session, group_id, user_id, str(message))
    # 触发机制检查
    if await check_trigger(group_id, message, group_config):
        # 记忆检索
        recent_messages = await memory_manager.get_recent_messages(group_id)
        # 行为决策
        should_reply = await decide_behavior(message, recent_messages, character_manager.get_character_info(character_id))
        if should_reply:
            context = {"user": event.sender.nickname,
                       "char": character_manager.get_character_info(character_id, "name")}
            message_builder = MessageBuilder(
                preset_file=group_config.preset_path,
                world_info_files=group_config.world_info_paths,
                character_id=character_id
            )
            response = await process_message(event, recent_messages, message_builder)
            if response:
                await send_message(bot, event, response)
    # 更新记忆
    await memory_manager.update_memory(group_id, user_id, str(message))


async def check_trigger(group_id: int, message: str, group_config: GroupConfig) -> bool:
    return random.random() < plugin_config.TRIGGER_PROBABILITY


async def decide_behavior(message: str, recent_messages: List[Dict], character_info: Dict) -> bool:
    # 实现行为决策逻辑
    return True


async def send_message(bot: Bot, event: GroupMessageEvent, message: str):
    await bot.send(event=event, message=message)
welcome_handler = on_notice(priority=5)


@welcome_handler.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = event.group_id
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return
    new_member = event.get_user_id()
    context = {"user": new_member, "char": character_manager.get_character_info(
        character_id, "name")}
    message_builder = MessageBuilder(
        preset_file=group_config.preset_path,
        world_info_files=group_config.world_info_paths,
        character_id=character_id
    )
    welcome_msg = await process_message(event, [], message_builder)
    if welcome_msg:
        await send_message(bot, event, welcome_msg)
scheduler = require("nonebot_plugin_apscheduler").scheduler


@scheduler.scheduled_job("cron", hour=8, minute=0)
async def morning_greeting():
    bot = get_driver().bots.values()[0]
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        if not character_id:
            continue
        context = {"user": "群友", "char": character_manager.get_character_info(
            character_id, "name")}
        message_builder = MessageBuilder(
            preset_file=group_config.preset_path,
            world_info_files=group_config.world_info_paths,
            character_id=character_id
        )
        greeting = await process_message({"group_id": group_id}, [], message_builder)
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
            context = {"user": "群友", "char": character_manager.get_character_info(
                character_id, "name")}
            message_builder = MessageBuilder(
                preset_file=group_config.preset_path,
                world_info_files=group_config.world_info_paths,
                character_id=character_id
            )
            revival_msg = await process_message({"group_id": group_id}, [], message_builder)
            if revival_msg:
                await bot.send_group_msg(group_id=group_id, message=revival_msg)


@scheduler.scheduled_job("cron", hour=3)
async def clean_old_messages():
    async with get_session() as session:
        await delete_old_messages(session, days=30)
# 管理员命令
list_presets = on_command("预设列表", rule=to_me(),
                          permission=SUPERUSER, priority=5)


@list_presets.handle()
async def handle_list_presets(bot: Bot, event: GroupMessageEvent):
    presets = character_manager.get_preset_list()
    message = "可用的预设列表：\n" + "\n".join(presets)
    await list_presets.finish(message)
switch_preset = on_command(
    "切换预设", rule=to_me(), permission=SUPERUSER, priority=5)


@switch_preset.handle()
async def handle_switch_preset(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await switch_preset.finish("使用方法：切换预设 <预设名称>")
    preset_name = args[1]
    group_id = event.group_id
    if await group_config_manager.set_preset(group_id, preset_name):
        await switch_preset.finish(f"成功切换到预设：{preset_name}")
    else:
        await switch_preset.finish(f"切换预设失败，请检查预设名称是否正确")
list_worldbooks = on_command(
    "世界书列表", rule=to_me(), permission=SUPERUSER, priority=5)


@list_worldbooks.handle()
async def handle_list_worldbooks(bot: Bot, event: GroupMessageEvent):
    worldbooks = character_manager.get_worldbook_list()
    message = "可用的世界书列表：\n" + "\n".join(worldbooks)
    await list_worldbooks.finish(message)
enable_worldbook = on_command(
    "启用世界书", rule=to_me(), permission=SUPERUSER, priority=5)


@enable_worldbook.handle()
async def handle_enable_worldbook(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await enable_worldbook.finish("使用方法：启用世界书 <世界书名称>")
    worldbook_name = args[1]
    group_id = event.group_id
    if await group_config_manager.enable_worldbook(group_id, worldbook_name):
        await enable_worldbook.finish(f"成功启用世界书：{worldbook_name}")
    else:
        await enable_worldbook.finish(f"启用世界书失败，请检查世界书名称是否正确")
disable_worldbook = on_command(
    "禁用世界书", rule=to_me(), permission=SUPERUSER, priority=5)


@disable_worldbook.handle()
async def handle_disable_worldbook(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await disable_worldbook.finish("使用方法：禁用世界书 <世界书名称>")
    worldbook_name = args[1]
    group_id = event.group_id
    if await group_config_manager.disable_worldbook(group_id, worldbook_name):
        await disable_worldbook.finish(f"成功禁用世界书：{worldbook_name}")
    else:
        await disable_worldbook.finish(f"禁用世界书失败，请检查世界书名称是否正确")
set_character = on_command("设置角色卡", rule=to_me(),
                           permission=SUPERUSER, priority=5)


@set_character.handle()
async def handle_set_character(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await set_character.finish("使用方法：设置角色卡 <角色名称>")
    character_name = args[1]
    group_id = event.group_id
    if await group_config_manager.set_character(group_id, character_name):
        await set_character.finish(f"成功设置角色卡：{character_name}")
    else:
        await set_character.finish(f"设置角色卡失败，请检查角色名称是否正确")
view_config = on_command("查看配置", rule=to_me(),
                         permission=SUPERUSER, priority=5)


@view_config.handle()
async def handle_view_config(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    config = await group_config_manager.get_group_config(group_id)
    message = f"当前群配置：\n预设：{config.preset_path}\n角色卡：{config.character_id}\n世界书：{', '.join(config.world_info_paths)}"
    await view_config.finish(message)
