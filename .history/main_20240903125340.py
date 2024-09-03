# main.py
import time
from typing import Dict, Any, Optional
from nonebot import on_message, on_notice, get_driver, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupIncreaseNoticeEvent, MessageSegment
from nonebot.typing import T_State
from .config import Config
from .llm_generator import llm_generator
from .message_processor import process_message
from .trigger_manager import check_trigger
from .memory_manager import memory_manager
from .behavior_engine import decide_behavior
from .message_sender import send_message
from .group_config_manager import group_config_manager, GroupConfig
from .message_builder import MessageBuilder
from .character_manager import CharacterManager
# 获取 logger 对象
import logging
logger = logging.getLogger(__name__)
# 加载配置
global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
# 初始化组件
character_manager = CharacterManager(character_cards_dir=plugin_config.character_cards_dir)
llm_generator.init()
# 消息处理器
message_handler = on_message(priority=5)
@message_handler.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    group_config: GroupConfig = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return  # 如果没有配置角色，则不处理消息
    # 1. 消息接收与解析
    message = process_message(event)
    # 2. 触发机制检查
    if check_trigger(group_id, message, group_config):
        # 3. 记忆检索
        memory = memory_manager.retrieve_memory(group_id, message)
        # 4. 行为决策
        behavior = decide_behavior(message, memory, character_manager.get_character_info(character_id))
        # 5. LLM 调用与响应生成
        context = {"user": event.sender.nickname, "char": character_manager.get_character_info(character_id, "name")}
        message_builder = MessageBuilder(
            preset_file=group_config.preset_path,
            world_info_files=group_config.world_info_paths,
            character_id=character_id
        )
        response = await process_message(event, memory_manager.get_recent_messages(group_id), message_builder)
        # 6. 消息发送
        if response:
            await send_message(bot, event, response)
    # 7. 更新记忆
    memory_manager.update_memory(group_id, message)
# 欢迎新成员
welcome_handler = on_notice(priority=5)
@welcome_handler.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = event.group_id
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return  # 如果没有配置角色，则不处理消息
    new_member = event.get_user_id()
    context = {"user": event.user_id, "char": character_manager.get_character_info(character_id, "name")}
    message_builder = MessageBuilder(
        preset_file=group_config.preset_path,
        world_info_files=group_config.world_info_paths,
        character_id=character_id
    )
    welcome_msg = await process_message(event, [], message_builder)
    if welcome_msg:
        await send_message(bot, event, welcome_msg)
# 定时任务：每日问候
scheduler = require("nonebot_plugin_apscheduler").scheduler
@scheduler.scheduled_job("cron", hour=8, minute=0)
async def morning_greeting():
    bot = get_driver().bots.values()[0]  # 获取第一个机器人实例
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        if not character_id:
            continue
        context = {"user": "群友", "char": character_manager.get_character_info(character_id, "name")}
        message_builder = MessageBuilder(
            preset_file=group_config.preset_path,
            world_info_files=group_config.world_info_paths,
            character_id=character_id
        )
        greeting = await process_message({"group_id": group_id}, [], message_builder)
        if greeting:
            await send_message(bot, {"group_id": group_id}, greeting)
# 冷场检测和响应
@scheduler.scheduled_job("interval", minutes=30)
async def check_inactive_chats():
    bot = get_driver().bots.values()[0]
    current_time = time.time()
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        if not character_id:
            continue
        last_message_time = memory_manager.get_last_message_time(group_id)
        if current_time - last_message_time > group_config.inactive_threshold:
            context = {"user": "群友", "char": character_manager.get_character_info(character_id, "name")}
            message_builder = MessageBuilder(
                preset_file=group_config.preset_path,
                world_info_files=group_config.world_info_paths,
                character_id=character_id
            )
            revival_msg = await process_message({"group_id": group_id}, [], message_builder)
            if revival_msg:
                await send_message(bot, {"group_id": group_id}, revival_msg)
# 其他功能和事件处理器可以在这里添加
