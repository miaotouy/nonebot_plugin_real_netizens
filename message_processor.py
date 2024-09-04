# message_processor.py
import logging
from typing import Any, Dict, Optional

from nonebot import get_driver
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .character_manager import character_manager
from .config import Config
from .db.database import get_recent_messages
from .group_config_manager import group_config_manager
from .image_processor import image_processor
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_builder import MessageBuilder

plugin_config = Config.parse_obj(get_driver().config)
logger = logging.getLogger(__name__)


class MessageProcessor:
    def __init__(self):
        self.message_builder = MessageBuilder()

    async def process(self, event: GroupMessageEvent) -> Optional[str]:
        group_id = event.group_id
        user_id = event.user_id
        message_content = event.get_plaintext().strip()
        if not message_content:
            logger.warning(
                f"Received empty message from user {user_id} in group {group_id}")
            return None
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        try:
            context = await self._build_context(group_id, user_id, character_id)
            messages = self.message_builder.build_message(context)
            messages.append({"role": "user", "content": message_content})
            response = await self._generate_llm_response(messages)

            if response:
                await self._update_memory(group_id, user_id, character_id, message_content, response)
                return response
            else:
                logger.warning(
                    f"LLM returned empty response for group {group_id}")
                return None
        except Exception as e:
            logger.error(
                f"Error processing message in group {group_id}: {str(e)}")
            return f"处理消息时发生错误，请稍后再试。"

    async def _build_context(self, group_id: int, user_id: int, character_id: str) -> Dict[str, Any]:
        recent_messages = await get_recent_messages(group_id, limit=plugin_config.CONTEXT_MESSAGE_COUNT)
        user_info = await memory_manager.get_user_info(user_id)
        character_info = character_manager.get_character_info(character_id)
        user_impression = await memory_manager.get_impression(group_id, user_id, character_id)
        return {
            "user": user_info,
            "character": character_info,
            "impression": user_impression,
            "recent_messages": recent_messages
        }

    async def _generate_llm_response(self, messages: list) -> Optional[str]:
        for attempt in range(plugin_config.MAX_RETRIES):
            try:
                response = await llm_generator.generate_response(
                    messages=messages,
                    model=plugin_config.LLM_MODEL,
                    temperature=plugin_config.LLM_TEMPERATURE,
                    max_tokens=plugin_config.LLM_MAX_TOKENS
                )
                return response.strip() if response else None
            except Exception as e:
                logger.error(
                    f"Error during LLM generation (attempt {attempt + 1}): {str(e)}")
                if attempt == plugin_config.MAX_RETRIES - 1:
                    raise

    async def _update_memory(self, group_id: int, user_id: int, character_id: str, user_message: str, ai_response: str):
        await memory_manager.add_message(group_id, user_id, user_message)
        await memory_manager.add_message(group_id, plugin_config.BOT_ID, ai_response)
        await memory_manager.update_impression(group_id, user_id, character_id, user_message, ai_response)

    async def process(self, event: GroupMessageEvent, character_id: str) -> Optional[str]:
        group_id = event.group_id
        user_id = event.user_id
        message = event.message
        text_content = ""
        image_content = []
        for segment in message:
            if segment.type == "text":
                text_content += segment.data['text']
            elif segment.type == "image":
                is_new, image_info = await image_processor.process_image(segment)
                image_content.append(image_info)
        if not text_content and not image_content:
            logger.warning(
                f"Received empty message from user {user_id} in group {group_id}")
            return None
        try:
            context = await self._build_context(group_id, user_id, character_id)
            messages = self.message_builder.build_message(context)
            if text_content:
                messages.append({"role": "user", "content": text_content})
            for image in image_content:
                messages.append({
                    "role": "user",
                    "content": f"[图片描述: {image['description']}]{'（这是一个表情包）' if image['is_meme'] else ''}"
                })
            response = await self._generate_llm_response(messages)
            if response:
                await self._update_memory(group_id, user_id, character_id, str(message), response)
                return response
            else:
                logger.warning(
                    f"LLM returned empty response for group {group_id}")
                return None
        except Exception as e:
            logger.error(
                f"Error processing message in group {group_id}: {str(e)}")
            return f"处理消息时发生错误，请稍后再试。"


message_processor = MessageProcessor()
