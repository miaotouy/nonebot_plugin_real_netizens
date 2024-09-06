# message_processor.py
import hashlib
import os
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
import aiohttp
from db.database import add_image_record, get_image_by_hash
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import (GroupMessageEvent, Message,
                                         MessageSegment)

from .character_manager import character_manager
from .config import Config
from .group_config_manager import group_config_manager
from .image_processor import image_processor
from .llm_generator import llm_generator
from .logger import logger
from .memory_manager import memory_manager
from .message_builder import MessageBuilder

plugin_config = Config.parse_obj(get_driver().config)



async def process_message(event: GroupMessageEvent, recent_messages: List[Dict], message_builder: MessageBuilder, context: Dict) -> Optional[str]:
    """处理群组消息事件，生成AI回复。
    Args:
        event: 群组消息事件。
        recent_messages: 最近的聊天记录。
        message_builder: 消息构建器。
        context: 上下文信息。
    Returns:
        AI回复文本，如果生成失败则返回 None。
    """
    group_id = event.group_id
    user_id = event.user_id
    message = event.message
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
    # 更新上下文
    context["message"] = full_content
    # 构建消息
    messages = message_builder.build_message(context)
    messages.append({"role": "user", "content": full_content})
    # 生成回复
    response = await llm_generator.generate_response(
        messages=messages,
        model=plugin_config.LLM_MODEL,
        temperature=plugin_config.LLM_TEMPERATURE,
        max_tokens=plugin_config.LLM_MAX_TOKENS
    )
    if response:
        return response.strip()
    else:
        logger.warning(
            f"LLM returned empty response for group {group_id}")
        return None


async def download_and_process_image(image_url: str) -> Optional[Dict]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    raise aiohttp.ClientError(
                        f"Failed to download image: HTTP {resp.status}")
                image_data = await resp.read()
    except aiohttp.ClientError as e:
        logger.error(f"Error downloading image from {image_url}: {e}")
        return None
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
