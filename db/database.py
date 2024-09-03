# database.py
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 从你的项目中引入数据库会话获取函数和模型定义
from nonebot_plugin_datastore import get_session
from .models import User, Group, GroupUser
async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    """根据用户ID获取用户信息"""
    stmt = select(User).where(User.user_id == user_id)
    result = await session.scalars(stmt)
    return result.first()
async def create_user(session: AsyncSession, user_id: int, nickname: str, avatar: str,
                       displayname: str = None, remark: str = None, gender: str = 'unknown', last_message: str = None, last_message_time: datetime = None) -> User:
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
async def get_group_user(
    session: AsyncSession,
    group_id: int,
    user_id: int
) -> Optional[GroupUser]:
    """根据用户ID和群组ID获取用户在群组中的信息"""
    stmt = select(GroupUser).where(
        GroupUser.group_id == group_id, GroupUser.user_id == user_id
    )
    result = await session.scalars(stmt)
    return result.first()
async def create_group_user(
    session: AsyncSession,
    group_id: int,
    user_id: int,
    nickname: str,
    role: str = 'member'
) -> GroupUser:
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
