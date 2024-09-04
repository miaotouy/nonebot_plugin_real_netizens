# memory_manager.py

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_datastore import get_session
from sqlalchemy import desc, select

from .config import Config
from .db.models import Impression, Message

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self):
        self.bot_id = None
        self.config = Config.parse_obj({})
        self.message_cache = defaultdict(list)
        self.impression_cache = {}
        self.cache_expiry = timedelta(minutes=30)  # 缓存过期时间

    async def set_bot_id(self, bot: Bot):
        self.bot_id = int(bot.self_id)
        logger.info(f"Bot ID set to {self.bot_id}")

    async def get_recent_messages(self, group_id: int, limit: int = 5) -> List[Dict]:
        if self.bot_id is None:
            logger.error("Bot ID not set. Please call set_bot_id() first.")
            return []
        # 检查缓存
        cached_messages = self.message_cache.get(group_id, [])
        if len(cached_messages) >= limit:
            return cached_messages[:limit]
        try:
            async with get_session() as session:
                query = select(Message).where(Message.group_id == group_id).order_by(
                    desc(Message.timestamp)).limit(limit)
                result = await session.execute(query)
                messages = result.scalars().all()
                formatted_messages = [{"role": "user" if msg.user_id != self.bot_id else "assistant",
                                       "content": msg.content} for msg in reversed(messages)]

                # 更新缓存
                self.message_cache[group_id] = formatted_messages
                return formatted_messages
        except Exception as e:
            logger.error(f"Error retrieving recent messages: {str(e)}")
            return []

    async def update_memory(self, group_id: int, user_id: int, content: str):
        try:
            async with get_session() as session:
                new_message = Message(
                    group_id=group_id, user_id=user_id, content=content)
                session.add(new_message)
                await session.commit()

            # 更新缓存
            cache_entry = {"role": "user" if user_id !=
                           self.bot_id else "assistant", "content": content}
            self.message_cache[group_id].insert(0, cache_entry)
            self.message_cache[group_id] = self.message_cache[group_id][:self.config.CONTEXT_MESSAGE_COUNT]
            logger.debug(
                f"Memory updated for group {group_id}, user {user_id}")
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")

    async def get_impression(self, group_id: int, user_id: int, character_id: str) -> Optional[str]:
        cache_key = (group_id, user_id, character_id)
        if cache_key in self.impression_cache:
            return self.impression_cache[cache_key]
        try:
            async with get_session() as session:
                impression = await session.execute(
                    select(Impression).where(
                        Impression.group_id == group_id,
                        Impression.user_id == user_id,
                        Impression.character_id == character_id,
                        Impression.is_active == True
                    )
                ).scalar_one_or_none()

                if impression:
                    self.impression_cache[cache_key] = impression.content
                    return impression.content
                return None
        except Exception as e:
            logger.error(f"Error getting impression: {str(e)}")
            return None

    async def update_impression(self, group_id: int, user_id: int, character_id: str, new_impression: str):
        async with get_session() as session:
            impression = await session.execute(
                select(Impression).where(
                    Impression.group_id == group_id,
                    Impression.user_id == user_id,
                    Impression.character_id == character_id
                )
            ).scalar_one_or_none()
            if impression:
                impression.content = new_impression
            else:
                impression = Impression(
                    group_id=group_id, user_id=user_id, character_id=character_id, content=new_impression)
                session.add(impression)
            impression.updated_at = datetime.utcnow()
            await session.commit()
        # 更新缓存
        self.impression_cache[(
            group_id, user_id, character_id)] = new_impression

    async def get_impression(self, group_id: int, user_id: int, character_id: str) -> Optional[str]:
        try:
            async with get_session() as session:
                impression = await session.execute(
                    select(Impression).where(
                        Impression.group_id == group_id,
                        Impression.user_id == user_id,
                        Impression.character_id == character_id,
                        Impression.is_active == True
                    )
                ).scalar_one_or_none()
                return impression.content if impression else None
        except Exception as e:
            logger.error(f"Error getting impression: {str(e)}")
            return None

    async def deactivate_impression(self, group_id: int, user_id: int, character_id: str):
        try:
            async with get_session() as session:
                impression = await session.execute(
                    select(Impression).where(
                        Impression.group_id == group_id,
                        Impression.user_id == user_id,
                        Impression.character_id == character_id
                    )
                ).scalar_one_or_none()
                if impression:
                    impression.is_active = False
                    impression.deactivated_at = datetime.utcnow()
                    await session.commit()
                    logger.info(
                        f"Impression deactivated for group {group_id}, user {user_id}, character {character_id}")
                else:
                    logger.warning(
                        f"No impression found to deactivate for group {group_id}, user {user_id}, character {character_id}")
        except Exception as e:
            logger.error(f"Error deactivating impression: {str(e)}")

    async def reactivate_impression(self, group_id: int, user_id: int, character_id: str):
        try:
            async with get_session() as session:
                impression = await session.execute(
                    select(Impression).where(
                        Impression.group_id == group_id,
                        Impression.user_id == user_id,
                        Impression.character_id == character_id
                    )
                ).scalar_one_or_none()
                if impression:
                    impression.is_active = True
                    impression.deactivated_at = None
                    await session.commit()
                    logger.info(
                        f"Impression reactivated for group {group_id}, user {user_id}, character {character_id}")
                else:
                    logger.warning(
                        f"No impression found to reactivate for group {group_id}, user {user_id}, character {character_id}")
        except Exception as e:
            logger.error(f"Error reactivating impression: {str(e)}")

    async def clear_cache(self):
        """清理过期的缓存"""
        current_time = datetime.now()
        for group_id in list(self.message_cache.keys()):
            if current_time - self.message_cache[group_id][-1].get('timestamp', current_time) > self.cache_expiry:
                del self.message_cache[group_id]

        for key in list(self.impression_cache.keys()):
            if current_time - self.impression_cache[key].get('timestamp', current_time) > self.cache_expiry:
                del self.impression_cache[key]


memory_manager = MemoryManager()