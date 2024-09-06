# main.py
import hashlib
import json
import os
import random
import time
from typing import Dict, List, Optional

import aiofiles
import aiohttp
from nonebot import get_driver, on_command, on_message, on_notice, require
from nonebot.adapters.onebot.v11 import (Bot, GroupIncreaseNoticeEvent,
                                         GroupMessageEvent, MessageSegment)
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot_plugin_datastore import get_session

from .admin_commands import *
from .admin_commands import handle_admin_command
from .behavior_decider import decide_behavior
from .character_manager import CharacterManager
from .config import plugin_config
from .db.database import (add_image_record, add_message, delete_old_messages,
                          get_image_by_hash)
from .group_config_manager import GroupConfig, group_config_manager
from .image_processor import image_processor
from .llm_generator import llm_generator
from .logger import logger
from .memory_manager import memory_manager
from .message_builder import MessageBuilder
from .message_processor import message_processor, preprocess_message
from .schedulers import scheduler

# 初始化组件
character_manager = CharacterManager(
    character_cards_dir=plugin_config.CHARACTER_CARDS_DIR)
llm_generator.init()
# 消息处理器
message_handler = on_message(priority=5)


async def download_and_process_image(image_url: str) -> Optional[Dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Failed to download image: HTTP {resp.status}")
            image_data = await resp.read()
    # 计算图片哈希
    image_hash = hashlib.md5(image_data).hexdigest()
    # 检查数据库中是否存在相同哈希的图片
    existing_image = await get_image_by_hash(image_hash)
    if existing_image:
        return existing_image  # 直接返回已存在的图片信息
    # 如果是新图片,保存并处理
    image_file = f"{image_hash}.jpg"
    # 创建保存图片的目录
    os.makedirs(plugin_config.IMAGE_SAVE_PATH, exist_ok=True)
    image_path = os.path.join(plugin_config.IMAGE_SAVE_PATH, image_file)
    async with aiofiles.open(image_path, mode="wb") as f:
        await f.write(image_data)
    # 使用 image_processor 处理新图片
    success, image_info = await image_processor.process_image(image_path, image_hash)
    if success:
        # 保存新图片信息到数据库
        await add_image_record(image_info)
        return image_info  # 返回处理后的图片信息
    else:
        return None


@message_handler.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    user_id = event.user_id

    # 检查是否为启用的群聊
    if group_id not in plugin_config.ENABLED_GROUPS:
        return

    # 获取群组配置
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id or plugin_config.DEFAULT_CHARACTER_ID

    # 处理消息中的文本和图片
    full_content, image_descriptions = await process_message_content(event.get_message())

    # 保存消息到数据库
    await add_message(group_id, user_id, full_content)

    # 触发机制检查
    if await check_trigger(group_id, full_content, group_config):
        await process_ai_response(bot, event, group_id, user_id, character_id, full_content, group_config)


async def process_message_content(message):
    text_content = ""
    image_descriptions = []
    for segment in message:
        if segment.type == "text":
            text_content += segment.data['text']
        elif segment.type == "image":
            image_url = segment.data['url']
            try:
                image_info = await download_and_process_image(image_url)
                if image_info:
                    description = f"[图片描述: {image_info['description']}]"
                    if image_info['is_meme']:
                        description += f"[表情包情绪: {image_info['emotion_tag']}]"
                    image_descriptions.append(description)
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")

    return text_content + " ".join(image_descriptions), image_descriptions


async def process_ai_response(bot, event, group_id, user_id, full_content, group_config):
    # 获取用户印象
    user_impression = await memory_manager.get_impression(group_id, user_id)
    # 获取最近的消息
    recent_messages = await memory_manager.get_recent_messages(group_id, limit=plugin_config.CONTEXT_MESSAGE_COUNT)
    # 从角色管理器获取最新的角色信息
    character_info = character_manager.get_character_info(group_id)
    # 构建消息
    message_builder = MessageBuilder(
        preset_name=group_config.preset_name,
        worldbook_names=group_config.worldbook_names,
        character_id=character_info['character_id'] or plugin_config.DEFAULT_CHARACTER_ID
    )
    # 决策行为
    behavior_decision = await decide_behavior(full_content, recent_messages, message_builder, user_id, group_id)
    if behavior_decision["should_reply"]:
        context = {
            "user": event.sender.nickname,
            "char": character_info.get("name"),
            "user_impression": user_impression,
            "reply_type": behavior_decision["reply_type"],
            "priority": behavior_decision["priority"]
        }
        # 处理消息
        response = await message_processor(event, recent_messages, message_builder, context)
        try:
            parsed_response = json.loads(response)
            await bot.send(event=event, message=parsed_response["response"])
            new_impression = parsed_response["impression_update"]
            await memory_manager.update_impression(group_id, user_id, parsed_response['character_id'], new_impression)
            logger.debug(
                f"Internal thoughts: {parsed_response['internal_thoughts']}")
            logger.debug(
                f"Behavior decision reason: {behavior_decision['reason']}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {response}")
    # 更新记忆
    await memory_manager.update_memory(group_id, user_id, parsed_response['character_id'], full_content, response)


async def check_trigger(group_id, full_content, group_config):
    # 实现触发机制检查的逻辑
    return True  # 临时返回值，需要根据实际逻辑修改


# 管理命令处理器
admin_command = on_command("admin", permission=SUPERUSER, priority=1)


# 管理命令处理器
admin_commands = {
    "设置角色卡": on_command("设置角色卡", permission=SUPERUSER, priority=1),
    "切换预设": on_command("切换预设", permission=SUPERUSER, priority=1),
    "启用世界书": on_command("启用世界书", permission=SUPERUSER, priority=1),
    "禁用世界书": on_command("禁用世界书", permission=SUPERUSER, priority=1),
    "查看配置": on_command("查看配置", permission=SUPERUSER, priority=1),
    "清除印象": on_command("清除印象", permission=SUPERUSER, priority=1),
    "恢复印象": on_command("恢复印象", permission=SUPERUSER, priority=1),
    "查看印象": on_command("查看印象", permission=SUPERUSER, priority=1),
}


# 通用的管理命令处理函数
async def admin_command_handler(bot: Bot, event: GroupMessageEvent):
    if event.group_id not in plugin_config.ENABLED_GROUPS:
        await bot.send(event, "此群未启用管理命令功能。")
        return
    args = str(event.get_message()).strip().split()
    command = event.raw_command.strip()  # 获取原始命令名
    if len(args) < 2:
        await bot.send(event, f"缺少目标群号。正确格式：{command} <目标群号> [其他参数]")
        return
    try:
        target_group = int(args[1])
    except ValueError:
        await bot.send(event, f"无效的群号 '{args[1]}'。请提供一个有效的数字群号。")
        return
    # 针对不同命令检查参数数量
    if command in ["设置角色卡", "切换预设", "启用世界书", "禁用世界书"]:
        if len(args) < 3:
            await bot.send(event, f"命令 '{command}' 缺少必要参数。正确格式：{command} <目标群号> <参数名>")
            return
    # 调用handle_admin_command处理命令
    await handle_admin_command(bot, event, [command] + args)
# 为每个管理命令注册处理函数
for cmd, matcher in admin_commands.items():
    matcher.handle()(admin_command_handler)


# 入群欢迎消息
welcome_handler = on_notice(priority=5)
@welcome_handler.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = event.group_id
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    # 如果没有设置角色，则使用默认角色
    if not character_id:
        character_id = plugin_config.DEFAULT_CHARACTER_ID
    new_member = event.get_user_id()
    context = {"user": new_member, "char": character_manager.get_character_info(
        character_id, "name")}
    # 获取预设名称和世界书名称列表
    preset_name = group_config.preset_name
    worldbook_names = group_config.worldbook_names
    message_builder = MessageBuilder(
        preset_name=preset_name,
        worldbook_names=worldbook_names,
        character_id=character_id
    )
    welcome_msg = await message_processor(event, [], message_builder, context)
    if welcome_msg:
        await bot.send(event=event, message=welcome_msg)


@scheduler.scheduled_job("cron", hour=int(plugin_config.MORNING_GREETING_TIME.split(":")[0]), minute=int(plugin_config.MORNING_GREETING_TIME.split(":")[1]))
async def morning_greeting():
    bot = get_driver().bots.values()[0]
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        # 如果没有设置角色，则使用默认角色
        if not character_id:
            character_id = plugin_config.DEFAULT_CHARACTER_ID
        context = {"user": "群友", "char": character_manager.get_character_info(
            character_id, "name")}
        # 获取预设名称和世界书名称列表
        preset_name = group_config.preset_name
        worldbook_names = group_config.worldbook_names
        message_builder = MessageBuilder(
            preset_name=preset_name,
            worldbook_names=worldbook_names,
            character_id=character_id
        )
        greeting = await message_processor(None, [], message_builder, context)
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
            context = {"user": "群友", "char": character_manager.get_character_info(
                character_id, "name")}
            # 获取预设名称和世界书名称列表
            preset_name = group_config.preset_name
            worldbook_names = group_config.worldbook_names
            message_builder = MessageBuilder(
                preset_name=preset_name,
                worldbook_names=worldbook_names,
                character_id=character_id
            )
            revival_msg = await message_processor(None, [], message_builder, context)
            if revival_msg:
                await bot.send_group_msg(group_id=group_id, message=revival_msg)


@scheduler.scheduled_job("cron", hour=3)
async def clean_old_messages():
    async with get_session() as session:
        await delete_old_messages(session, days=30)


# 触发机制检查
async def check_trigger(group_id: int, message: str, group_config: GroupConfig) -> bool:
    return random.random() < plugin_config.TRIGGER_PROBABILITY
