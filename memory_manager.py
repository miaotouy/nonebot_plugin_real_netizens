# memory_manager.py
import logging
from datetime import datetime
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

    async def set_bot_id(self, bot: Bot):
        self.bot_id = int(bot.self_id)
        logger.info(f"Bot ID set to {self.bot_id}")

    async def get_recent_messages(self, group_id: int, limit: int = 5) -> List[Dict]:
        if self.bot_id is None:
            logger.error("Bot ID not set. Please call set_bot_id() first.")
            return []
        try:
            async with get_session() as session:
                query = select(Message).where(Message.group_id == group_id).order_by(
                    desc(Message.timestamp)).limit(limit)
                result = await session.execute(query)
                messages = result.scalars().all()
                return [{"role": "user" if msg.user_id != self.bot_id else "assistant",
                         "content": msg.content} for msg in reversed(messages)]
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
            logger.debug(
                f"Memory updated for group {group_id}, user {user_id}")
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")

    async def get_last_message_time(self, group_id: int) -> float:
        try:
            async with get_session() as session:
                query = select(Message.timestamp).where(
                    Message.group_id == group_id).order_by(desc(Message.timestamp)).limit(1)
                result = await session.execute(query)
                last_message = result.scalar_one_or_none()
                return last_message.timestamp() if last_message else 0
        except Exception as e:
            logger.error(f"Error getting last message time: {str(e)}")
            return 0

    async def clear_old_messages(self, days: int = 30):
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            async with get_session() as session:
                await session.execute(Message.__table__.delete().where(Message.timestamp < cutoff_date))
                await session.commit()
            logger.info(f"Cleared messages older than {days} days")
        except Exception as e:
            logger.error(f"Error clearing old messages: {str(e)}")

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
                impression = Impression(group_id=group_id, user_id=user_id, character_id=character_id, content=new_impression)
                session.add(impression)

            impression.updated_at = datetime.utcnow()
            await session.commit()


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


memory_manager = MemoryManager()
