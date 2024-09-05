# main.py
import hashlib
import json
import logging
import os
import random
import time
from typing import Dict, List, Optional

import aiofiles
import aiohttp
from nonebot import get_driver, on_command, on_message, on_notice, require
from nonebot.adapters.onebot.v11 import (Bot, GroupIncreaseNoticeEvent,
                                         GroupMessageEvent)
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot_plugin_datastore import get_session

from .character_manager import CharacterManager
from .config import plugin_config
from .db.database import (add_image_record, add_message, delete_old_messages,
                          get_image_by_hash)
from .group_config_manager import GroupConfig, group_config_manager
from .image_processor import image_processor
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_builder import MessageBuilder
from .message_processor import message_processor
from .schedulers import scheduler

logger = logging.getLogger(__name__)
# 初始化组件
character_manager = CharacterManager(
    character_cards_dir=plugin_config.CHARACTER_CARDS_DIR)
llm_generator.init()
# 消息处理器
message_handler = on_message(priority=5)


async def decide_behavior(message: str, recent_messages: List[Dict], character_info: Dict, user_impression: str) -> Dict:
    prompt = f"""
    请分析以下情况，并以JSON格式回复是否应该回复用户的消息：
    1. 最近的对话历史: \n\n{recent_messages}
    2. 用户消息: \n{message}\n\n
    3. 角色设定: \n{character_info}
    4. 用户印象: \n{user_impression}
    请返回如下格式的JSON：
    {{
        "should_reply": true/false,
        "reason": "解释为什么做出这个决定",
        "reply_type": "可能的回复类型，例如：普通回复、提问、表情等",
        "priority": 0-10之间的数字，表示回复的优先级
    }}
    """
    response = await llm_generator.generate_response(
        messages=[{"role": "user", "content": prompt}],
        model=plugin_config.LLM_MODEL,
        temperature=plugin_config.LLM_TEMPERATURE,
        max_tokens=plugin_config.LLM_MAX_TOKENS
    )
    try:
        decision = json.loads(response)
        return decision
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response as JSON: {response}")
        return {"should_reply": False, "reason": "解析错误", "reply_type": "none", "priority": 0}


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
    image_path = os.path.join(plugin_config.IMAGE_SAVE_PATH, image_file)
    async with aiofiles.open(image_path, mode='wb') as f:
        await f.write(image_data)
    # 使用 image_processor 处理新图片
    image_info = await image_processor.process_image(image_path, image_hash)
    # 保存新图片信息到数据库
    await add_image_record(image_info)
    return image_info  # 返回处理后的图片信息


@message_handler.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    user_id = event.user_id
    # 检查是否为启用的群聊
    if group_id not in plugin_config.ENABLED_GROUPS:
        return
    # 获取群组配置
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    # 如果没有设置角色，则使用默认角色
    if not character_id:
        character_id = plugin_config.DEFAULT_CHARACTER_ID
    message = event.get_message()
    text_content = ""
    image_descriptions = []
    # 处理消息中的文本和图片
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
                logger.error(
                    f"Error downloading or processing image: {str(e)}")
    # 合并文本内容和图片描述
    full_content = text_content + " ".join(image_descriptions)
    # 保存消息到数据库
    await add_message(group_id, user_id, full_content)
    # 触发机制检查
    if await check_trigger(group_id, full_content, group_config):
        user_impression = await memory_manager.get_impression(group_id, user_id, character_id)
        recent_messages = await memory_manager.get_recent_messages(group_id, limit=plugin_config.CONTEXT_MESSAGE_COUNT)
        # 行为决策
        behavior_decision = await decide_behavior(full_content, recent_messages, character_manager.get_character_info(character_id), user_impression)
        if behavior_decision["should_reply"]:
            context = {
                "user": event.sender.nickname,
                "char": character_manager.get_character_info(character_id, "name"),
                "user_impression": user_impression,
                "reply_type": behavior_decision["reply_type"],
                "priority": behavior_decision["priority"]
            }
            # 获取预设名称和世界书名称列表
            preset_name = group_config.preset_name
            worldbook_names = group_config.worldbook_names
            message_builder = MessageBuilder(
                preset_name=preset_name,
                worldbook_names=worldbook_names,
                character_id=character_id
            )
            response = await message_processor(event, recent_messages, message_builder, context)
            try:
                parsed_response = json.loads(response)
                # 发送实际回复
                await bot.send(event=event, message=parsed_response["response"])
                # 更新印象
                new_impression = parsed_response["impression_update"]
                await memory_manager.update_impression(group_id, user_id, character_id, new_impression)
                # 可以选择记录内部想法和行为决策理由
                logger.debug(
                    f"Internal thoughts: {parsed_response['internal_thoughts']}")
                logger.debug(
                    f"Behavior decision reason: {behavior_decision['reason']}")
            except json.JSONDecodeError:
                logger.error(
                    f"Failed to parse LLM response as JSON: {response}")
    # 更新记忆
    await memory_manager.update_memory(group_id, user_id, full_content)


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


# 印象更新函数
async def update_impression(old_impression: str, impression_update: str, character_id: str) -> str:
    # 只保留最新的印象
    return impression_update.strip()


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
