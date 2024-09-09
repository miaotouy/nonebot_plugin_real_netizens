#nonebot_plugin_real_netizens\db\user_info_service.py
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Optional
from nonebot.log import logger
if TYPE_CHECKING:
    from .models import User, Group, GroupUser
import aiohttp
from PIL import Image
from nonebot.adapters import Bot, Event
from nonebot_plugin_datastore import get_session
from nonebot_plugin_userinfo import UserInfo, get_user_info
from ..image_processor import image_processor
from .database import (
    create_group,
    create_group_user,
    create_user,
    get_group,
    get_group_user,
    get_user,
    update_user,
)
from .models import Group, GroupUser, User
async def save_user_info(bot: Bot, event: Event):
    """保存用户信息到数据库"""
    user_id = event.get_user_id()
    async with get_session() as session:
        user_info: UserInfo = await get_user_info(bot, event, user_id)
        user: Optional[User] = await get_user(session, int(user_id))  # type: ignore
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
            # 确保 user 不为 None
            if user:
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
            else:
                logger.warning(f"User {user_id} not found in database.")
        # 处理头像描述
        if user_info.user_avatar:
            await update_user_avatar_description(session, int(user_id), user_info.user_avatar.get_url())
        # 检查 event 是否有 group_id 和 group_name 属性
        if hasattr(event, 'group_id') and hasattr(event, 'group_name'):
            group_id = event.group_id
            group: Optional[Group] = await get_group(session, int(group_id))  # type: ignore
            if not group:
                group = await create_group(session, int(group_id), event.group_name)
            # 确保 group 和 user 都不是 None
            if group and user:
                group_user: Optional[GroupUser] = await get_group_user(session, group.group_id, user.user_id)  # type: ignore
                if not group_user:
                    await create_group_user(session, group.group_id, user.user_id, user_info.user_displayname)
            else:
                logger.warning(f"Group {group_id} or user {user_id} not found in database.")
        # 如果是消息事件，更新用户的最新消息
        if hasattr(event, 'get_message') and user:
            message = event.get_message()
            await update_user(session, user, last_message=str(message), last_message_time=datetime.now())
async def update_user_avatar_description(session, user_id: int, avatar_url: str):
    """更新用户头像描述"""
    try:
        image_data = await download_image(avatar_url)
        if image_data:
            image = Image.open(BytesIO(image_data))
            # 计算图像哈希值并保存到数据库（如果不存在）
            image_hash = image_processor.calculate_image_hash(image)
            # 生成图像描述（如果不存在）
            _, image_info = await image_processor.process_image("", image_hash)
            # 更新用户头像描述
            user = await session.get(User, user_id)
            if user:
                user.avatar_description = image_info['description']
                await session.commit()
    except Exception as e:
        logger.error(
            f"Error updating avatar description for user {user_id}: {str(e)}")

async def download_image(url: str) -> Optional[bytes]:
    """下载图片"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}")
    return None
