# nonebot_plugin_real_netizens\db\database.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from nonebot_plugin_datastore import get_session
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import db_models  # 导入 db_models 字典

async def get_user(session: AsyncSession, user_id: int) -> Optional[db_models["User"]]:
    """根据用户ID获取用户信息"""
    stmt = select(db_models["User"]).where(db_models["User"].user_id == user_id)
    result = await session.scalars(stmt)
    return result.first()
async def create_user(
    session: AsyncSession,
    user_id: int,
    nickname: str,
    avatar: str,
    displayname: str = None,
    remark: str = None,
    gender: str = "unknown",
    last_message: str = None,
    last_message_time: datetime = None,
) -> db_models["User"]:
    """创建新用户"""
    user = db_models["User"](
        user_id=user_id,
        nickname=nickname,
        avatar=avatar,
        last_active_time=datetime.now(),
        displayname=displayname,
        remark=remark,
        gender=gender,
        last_message=last_message,
        last_message_time=last_message_time,
    )
    session.add(user)
    await session.commit()
    return user
async def update_user(session: AsyncSession, user: db_models["User"], **kwargs):
    """更新用户信息"""
    for key, value in kwargs.items():
        setattr(user, key, value)
    session.add(user)
    await session.commit()
async def get_group(session: AsyncSession, group_id: int) -> Optional[db_models["Group"]]:
    """根据群组ID获取群组信息"""
    stmt = select(db_models["Group"]).where(db_models["Group"].group_id == group_id)
    result = await session.scalars(stmt)
    return result.first()
async def create_group(session: AsyncSession, group_id: int, group_name: str) -> db_models["Group"]:
    """创建新群组"""
    group = db_models["Group"](group_id=group_id, group_name=group_name)
    session.add(group)
    await session.commit()
    return group
async def get_group_user(
    session: AsyncSession, group_id: int, user_id: int
) -> Optional[db_models["GroupUser"]]:
    """根据用户ID和群组ID获取用户在群组中的信息"""
    stmt = select(db_models["GroupUser"]).where(
        db_models["GroupUser"].group_id == group_id, db_models["GroupUser"].user_id == user_id
    )
    result = await session.scalars(stmt)
    return result.first()
async def create_group_user(
    session: AsyncSession, group_id: int, user_id: int, nickname: str, role: str = "member"
) -> db_models["GroupUser"]:
    """创建用户在群组中的记录"""
    group_user = db_models["GroupUser"](
        group_id=group_id,
        user_id=user_id,
        nickname=nickname,
        role=role,
        join_time=datetime.now(),
    )
    session.add(group_user)
    await session.commit()
    return group_user
async def add_message(
    session: AsyncSession, group_id: int, user_id: int, content: str
) -> db_models["Message"]:
    """添加新消息"""
    message = db_models["Message"](group_id=group_id, user_id=user_id, content=content)
    session.add(message)
    await session.commit()
    return message
async def get_recent_messages(
    session: AsyncSession, group_id: int, limit: int = 10
) -> List[db_models["Message"]]:
    """获取最近的消息"""
    stmt = (
        select(db_models["Message"])
        .where(db_models["Message"].group_id == group_id)
        .order_by(db_models["Message"].timestamp.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
async def delete_old_messages(session: AsyncSession, days: int = 30):
    """删除旧消息"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    stmt = delete(db_models["Message"]).where(db_models["Message"].timestamp < cutoff_date)
    await session.execute(stmt)
    await session.commit()
async def get_impression(
    session: AsyncSession, group_id: int, user_id: int, character_id: str
) -> Optional[db_models["Impression"]]:
    """获取用户印象"""
    stmt = select(db_models["Impression"]).where(
        db_models["Impression"].group_id == group_id,
        db_models["Impression"].user_id == user_id,
        db_models["Impression"].character_id == character_id,
    )
    result = await session.scalars(stmt)
    return result.first()
async def update_impression(
    session: AsyncSession,
    group_id: int,
    user_id: int,
    character_id: str,
    content: str,
) -> db_models["Impression"]:
    """更新或创建用户印象"""
    impression = await get_impression(session, group_id, user_id, character_id)
    if impression:
        impression.content = content
        impression.updated_at = datetime.utcnow()
    else:
        impression = db_models["Impression"](
            group_id=group_id,
            user_id=user_id,
            character_id=character_id,
            content=content,
        )
        session.add(impression)
    await session.commit()
    return impression
async def get_last_message_time(
    session: AsyncSession, group_id: int
) -> Optional[datetime]:
    """获取群组最后一条消息的时间"""
    stmt = (
        select(db_models["Message"].timestamp)
        .where(db_models["Message"].group_id == group_id)
        .order_by(db_models["Message"].timestamp.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    last_message = result.scalar_one_or_none()
    return last_message
