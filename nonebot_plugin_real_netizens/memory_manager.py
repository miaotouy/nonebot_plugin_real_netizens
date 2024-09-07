# memory_manager.py
from nonebot import require
require("nonebot_plugin_datastore")

from nonebot_plugin_datastore import get_session

from nonebot.adapters.onebot.v11 import Bot
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select

from .config import get_plugin_config
from .db.models import Impression, Message
from .logger import logger


class MemoryManager:
    def __init__(self):
        self.bot_id = None
        self.config = get_plugin_config()
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

    async def update_memory(self, group_id: int, user_id: int, user_message: str, ai_response: str, character_id: str):
        try:
            # 添加用户消息到数据库
            async with get_session() as session:
                new_message = Message(
                    group_id=group_id, user_id=user_id, content=user_message, timestamp=datetime.utcnow())  # 设置时间戳
                session.add(new_message)
                await session.commit()
            # 添加AI回复到数据库
            async with get_session() as session:
                new_message = Message(
                    group_id=group_id, user_id=self.bot_id, content=ai_response, timestamp=datetime.utcnow())  # 设置时间戳
                session.add(new_message)
                await session.commit()
            # 更新缓存
            user_cache_entry = {"role": "user", "content": user_message}
            ai_cache_entry = {"role": "assistant", "content": ai_response}
            self.message_cache[group_id].insert(0, user_cache_entry)
            self.message_cache[group_id].insert(0, ai_cache_entry)
            self.message_cache[group_id] = self.message_cache[group_id][:self.config.CONTEXT_MESSAGE_COUNT]
            # 更新印象
            await self.update_impression(group_id, user_id, character_id, ai_response)
            logger.debug(
                f"Memory updated for group {group_id}, user {user_id}")
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")

    async def get_impression(self, group_id: int, user_id: int, character_id: str) -> Optional[str]:
        """
        获取用户对角色的印象。
        """
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
            logger.error(
                f"Error getting impression for group {group_id}, user {user_id}, character {character_id}: {str(e)}")
            return None

    async def update_impression(self, group_id: int, user_id: int, character_id: str, new_impression: str):
        """
        更新或创建用户对角色的印象。
        """
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
                    impression.content = new_impression
                else:
                    impression = Impression(
                        group_id=group_id,
                        user_id=user_id,
                        character_id=character_id,
                        content=new_impression
                    )
                    session.add(impression)
                impression.updated_at = datetime.utcnow()
                await session.commit()
            # 更新缓存
            self.impression_cache[(
                group_id, user_id, character_id)] = new_impression
        except Exception as e:
            logger.error(
                f"Error updating impression for group {group_id}, user {user_id}, character {character_id}: {str(e)}")

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

    async def get_last_message_time(self, group_id: int) -> Optional[float]:
        if self.bot_id is None:
            logger.error("Bot ID not set. Please call set_bot_id() first.")
            return None
        try:
            async with get_session() as session:
                # 查询数据库中该群组的最后一条消息的时间戳
                result = await session.execute(
                    select(Message.timestamp).where(Message.group_id ==
                                                    group_id).order_by(Message.timestamp.desc()).limit(1)
                )
                last_message_time = result.scalar_one_or_none()
                if last_message_time:
                    return last_message_time.timestamp()  # 返回时间戳
                else:
                    return None
        except Exception as e:
            logger.error(
                f"Error getting last message time for group {group_id}: {str(e)}")
            return None

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
