# nonebot_plugin_real_netizens\message_processor.py
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
from nonebot.log import logger
from .memory_manager import memory_manager
from .message_builder import MessageBuilder

plugin_config = Config.parse_obj(get_driver().config)


class MessageProcessor:
    def __init__(self):
        self.config_cache: Dict[int, Any] = {}
        group_config_manager.register_observer(self.on_config_change)

    def on_config_change(self, group_id: int):
        if group_id in self.config_cache:
            del self.config_cache[group_id]

    async def process_message(self, event: GroupMessageEvent, recent_messages: List[Dict], context: Dict) -> Optional[str]:
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
        # 获取或更新群组配置
        if group_id not in self.config_cache:
            group_config = group_config_manager.get_group_config(group_id)
            self.config_cache[group_id] = group_config
        else:
            group_config = self.config_cache[group_id]
        message_builder = MessageBuilder(
            preset_name=group_config.preset_name,
            worldbook_names=group_config.worldbook_names,
            character_id=group_config.character_id or plugin_config.DEFAULT_CHARACTER_ID
        )
        message = event.message
        full_content, image_descriptions = await self.process_message_content(message)
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
            logger.warning(f"LLM returned empty response for group {group_id}")
            return None

    async def process_message_content(self, message: Message) -> Tuple[str, List[str]]:
        """处理消息内容，提取文本和图片描述。"""
        text_content = ""
        image_descriptions = []
        for segment in message:
            if segment.type == "text":
                text_content += segment.data['text']
            elif segment.type == "image":
                image_url = segment.data['url']
                try:
                    image_info = await self.download_and_process_image(image_url)
                    if image_info:
                        description = f"[图片描述: {image_info['description']}]"
                        if image_info['is_meme']:
                            description += f"[表情包情绪: {image_info['emotion_tag']}]"
                        image_descriptions.append(description)
                except Exception as e:
                    logger.error(
                        f"Error downloading or processing image: {str(e)}")
        full_content = text_content + " ".join(image_descriptions)
        return full_content, image_descriptions

    async def download_and_process_image(self, image_url: str) -> Optional[Dict]:
        """下载并处理图片。"""
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
        image_hash = hashlib.md5(image_data).hexdigest()
        existing_image = await get_image_by_hash(image_hash)
        if existing_image:
            return existing_image
        image_file = f"{image_hash}.jpg"
        os.makedirs(plugin_config.IMAGE_SAVE_PATH, exist_ok=True)
        image_path = os.path.join(plugin_config.IMAGE_SAVE_PATH, image_file)
        async with aiofiles.open(image_path, mode="wb") as f:
            await f.write(image_data)
        success, image_info = await image_processor.process_image(image_path, image_hash)
        if success:
            await add_image_record(image_info)
            return image_info
        else:
            return None


message_processor = MessageProcessor()
