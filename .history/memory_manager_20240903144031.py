# memory_manager.py
from sqlalchemy import select
from nonebot_plugin_datastore import get_session
from nonebot.adapters.onebot.v11 import Bot
from .models import Message
from typing import List, Dict
import logging
logger = logging.getLogger(__name__)
class MemoryManager:
    def __init__(self):
        self.bot_id = None
    async def set_bot_id(self, bot: Bot):
        self.bot_id = int(bot.self_id)
        logger.info(f"Bot ID set to {self.bot_id}")
    async def get_recent_messages(self, group_id: int, limit: int = 5) -> List[Dict]:
        if self.bot_id is None:
            logger.error("Bot ID not set. Please call set_bot_id() first.")
            return []
        try:
            async with get_session() as session:
                query = select(Message).where(Message.group_id == group_id).order_by(Message.create_time.desc()).limit(limit)
                result = await session.execute(query)
                messages = result.scalars().all()
                return [{"role": "user" if msg.user_id != self.bot_id else "assistant", "content": msg.content} for msg in reversed(messages)]
        except Exception as e:
            logger.error(f"Error retrieving recent messages: {str(e)}")
            return []
    async def update_memory(self, group_id: int, user_id: int, content: str):
        try:
            async with get_session() as session:
                new_message = Message(group_id=group_id, user_id=user_id, content=content)
                session.add(new_message)
                await session.commit()
            logger.debug(f"Memory updated for group {group_id}, user {user_id}")
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
    async def get_last_message_time(self, group_id: int) -> float:
        try:
            async with get_session() as session:
                query = select(Message.create_time).where(Message.group_id == group_id).order_by(Message.create_time.desc()).limit(1)
                result = await session.execute(query)
                last_message = result.scalar_one_or_none()
                return last_message.timestamp() if last_message else 0
        except Exception as e:
            logger.error(f"Error getting last message time: {str(e)}")
            return 0
    async def clear_old_messages(self, days: int = 30):
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            async with get_session() as session:
                await session.execute(Message.__table__.delete().where(Message.create_time < cutoff_date))
                await session.commit()
            logger.info(f"Cleared messages older than {days} days")
        except Exception as e:
            logger.error(f"Error clearing old messages: {str(e)}")
memory_manager = MemoryManager()
