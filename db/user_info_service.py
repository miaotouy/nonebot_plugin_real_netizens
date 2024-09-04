from datetime import datetime
from typing import Optional

from nonebot.adapters import Bot, Event
from nonebot_plugin_datastore import get_session
from nonebot_plugin_userinfo import UserInfo, get_user_info

from . import Group, GroupUser, User
from .database import (create_group, create_group_user, create_user, get_group,
                       get_group_user, get_user, update_user)


async def save_user_info(bot: Bot, event: Event):
    """保存用户信息到数据库"""
    user_id = event.get_user_id()
    session = get_session()
    async with session.begin():
        user_info: UserInfo = await get_user_info(bot, event, user_id)
        user: Optional[User] = await get_user(session, int(user_id))
        if not user:
            user = await create_user(
                session,
                int(user_id),
                user_info.user_name,
                user_info.user_avatar.get_url() if user_info.user_avatar else None,
                user_info.user_displayname,
                user_info.user_remark,
                user_info.user_gender
            )
        else:
            await update_user(
                session,
                user,
                nickname=user_info.user_name,
                avatar=user_info.user_avatar.get_url() if user_info.user_avatar else None,
                last_active_time=datetime.now(),
                displayname=user_info.user_displayname,
                remark=user_info.user_remark,
                gender=user_info.user_gender
            )

        # 检查 event 是否有 group_id 和 group_name 属性，避免 AttributeError
        if hasattr(event, 'group_id') and hasattr(event, 'group_name'):
            group_id = event.group_id
            group: Optional[Group] = await get_group(session, int(group_id))
            if not group:
                group = await create_group(session, int(group_id), event.group_name)
            group_user: Optional[GroupUser] = await get_group_user(session, group.group_id, user.user_id)
            if not group_user:
                await create_group_user(session, group.group_id, user.user_id, user_info.user_displayname)

        # 如果是消息事件，更新用户的最新消息
        if hasattr(event, 'get_message'):
            message = event.get_message()
            await update_user(session, user, last_message=str(message), last_message_time=datetime.now())
