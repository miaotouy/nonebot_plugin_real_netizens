# db\database.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from nonebot_plugin_datastore import get_session
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import Group, GroupUser, Image, Impression, Message, User


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    """根据用户ID获取用户信息"""
    stmt = select(User).where(User.user_id == user_id)
    result = await session.scalars(stmt)
    return result.first()


async def create_user(session: AsyncSession, user_id: int, nickname: str, avatar: str,
                      displayname: str = None, remark: str = None, gender: str = 'unknown',
                      last_message: str = None, last_message_time: datetime = None) -> User:
    """创建新用户"""
    user = User(
        user_id=user_id,
        nickname=nickname,
        avatar=avatar,
        last_active_time=datetime.now(),
        displayname=displayname,
        remark=remark,
        gender=gender,
        last_message=last_message,
        last_message_time=last_message_time
    )
    session.add(user)
    await session.commit()
    return user


async def update_user(session: AsyncSession, user: User, **kwargs):
    """更新用户信息"""
    for key, value in kwargs.items():
        setattr(user, key, value)
    session.add(user)
    await session.commit()


async def get_group(session: AsyncSession, group_id: int) -> Optional[Group]:
    """根据群组ID获取群组信息"""
    stmt = select(Group).where(Group.group_id == group_id)
    result = await session.scalars(stmt)
    return result.first()


async def create_group(session: AsyncSession, group_id: int, group_name: str) -> Group:
    """创建新群组"""
    group = Group(group_id=group_id, group_name=group_name)
    session.add(group)
    await session.commit()
    return group


async def get_group_user(session: AsyncSession, group_id: int, user_id: int) -> Optional[GroupUser]:
    """根据用户ID和群组ID获取用户在群组中的信息"""
    stmt = select(GroupUser).where(
        GroupUser.group_id == group_id, GroupUser.user_id == user_id
    )
    result = await session.scalars(stmt)
    return result.first()


async def create_group_user(session: AsyncSession, group_id: int, user_id: int, nickname: str, role: str = 'member') -> GroupUser:
    """创建用户在群组中的记录"""
    group_user = GroupUser(
        group_id=group_id,
        user_id=user_id,
        nickname=nickname,
        role=role,
        join_time=datetime.now()
    )
    session.add(group_user)
    await session.commit()
    return group_user


async def add_message(session: AsyncSession, group_id: int, user_id: int, content: str) -> Message:
    """添加新消息"""
    message = Message(group_id=group_id, user_id=user_id, content=content)
    session.add(message)
    await session.commit()
    return message


async def get_recent_messages(session: AsyncSession, group_id: int, limit: int = 10) -> List[Message]:
    """获取最近的消息"""
    stmt = select(Message).where(Message.group_id == group_id).order_by(
        Message.timestamp.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_old_messages(session: AsyncSession, days: int = 30):
    """删除旧消息"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    stmt = delete(Message).where(Message.timestamp < cutoff_date)
    await session.execute(stmt)
    await session.commit()


async def get_impression(session: AsyncSession, group_id: int, user_id: int, character_id: str) -> Optional[Impression]:
    """获取用户印象"""
    stmt = select(Impression).where(
        Impression.group_id == group_id,
        Impression.user_id == user_id,
        Impression.character_id == character_id
    )
    result = await session.scalars(stmt)
    return result.first()


async def update_impression(session: AsyncSession, group_id: int, user_id: int, character_id: str, content: str) -> Impression:
    """更新或创建用户印象"""
    impression = await get_impression(session, group_id, user_id, character_id)
    if impression:
        impression.content = content
        impression.updated_at = datetime.utcnow()
    else:
        impression = Impression(
            group_id=group_id,
            user_id=user_id,
            character_id=character_id,
            content=content
        )
        session.add(impression)
    await session.commit()
    return impression


async def get_last_message_time(session: AsyncSession, group_id: int) -> Optional[datetime]:
    """获取群组最后一条消息的时间"""
    stmt = select(Message.timestamp).where(Message.group_id ==
                                           group_id).order_by(Message.timestamp.desc()).limit(1)
    result = await session.execute(stmt)
    last_message = result.scalar_one_or_none()
    return last_message


async def add_image_record(image_info: Dict):
    async with get_session() as session:
        new_image = Image(**image_info)
        session.add(new_image)
        await session.commit()


async def get_image_by_hash(image_hash: str) -> Optional[Dict]:
    async with get_session() as session:
        query = select(Image).where(Image.hash == image_hash)
        result = await session.execute(query)
        image = result.scalar_one_or_none()
        if image:
            return {
                'file_path': image.file_path,
                'file_name': image.file_name,
                'hash': image.hash,
                'description': image.description,
                'is_meme': image.is_meme,
                'emotion_tag': image.emotion_tag
            }
        return None

