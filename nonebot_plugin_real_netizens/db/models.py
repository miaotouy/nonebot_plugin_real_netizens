#nonebot_plugin_real_netizens\db\models.py
from datetime import datetime
from typing import Dict, Optional

from nonebot_plugin_datastore import get_plugin_data, get_session
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.orm import relationship

db_models = {}  # 存储所有数据库模型类


def init_models(plugin_data):
    class User(plugin_data.Model):  # type: ignore
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True, autoincrement=False)
        nickname = Column(String(64))
        avatar = Column(String(255))
        avatar_description = Column(Text)
        last_active_time = Column(DateTime)
        displayname = Column(String(64))
        remark = Column(String(64))
        gender = Column(String(16), default="unknown")
        last_message = Column(Text)
        last_message_time = Column(DateTime)
        groups = relationship("GroupUser", back_populates="user")
        messages = relationship("Message", back_populates="user")
        __table_args__ = (Index("idx_user_last_active", "last_active_time"),)

    db_models["User"] = User

    class Group(plugin_data.Model):  # type: ignore
        __tablename__ = "groups"
        group_id = Column(Integer, primary_key=True, autoincrement=False)
        group_name = Column(String(64))
        users = relationship("GroupUser", back_populates="group")
        messages = relationship("Message", back_populates="group")
        __table_args__ = (Index("idx_group_name", "group_name"),)

    db_models["Group"] = Group

    class GroupUser(plugin_data.Model):  # type: ignore
        __tablename__ = "group_users"
        group_id = Column(Integer, ForeignKey("groups.group_id"), primary_key=True)
        user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
        nickname = Column(String(64))
        role = Column(String(64), default="member")
        join_time = Column(DateTime)
        user = relationship("User", back_populates="groups")
        group = relationship("Group", back_populates="users")
        __table_args__ = (Index("idx_group_user", "group_id", "user_id"),)

    db_models["GroupUser"] = GroupUser

    class Message(plugin_data.Model):  # type: ignore
        __tablename__ = "messages"
        id = Column(Integer, primary_key=True)
        group_id = Column(Integer, ForeignKey("groups.group_id"))
        user_id = Column(Integer, ForeignKey("users.user_id"))
        content = Column(Text)
        timestamp = Column(DateTime, default=datetime.utcnow, index=True)
        group = relationship("Group", back_populates="messages")
        user = relationship("User", back_populates="messages")

    db_models["Message"] = Message

    class Impression(plugin_data.Model):
        __tablename__ = "impressions"
        id = Column(Integer, primary_key=True)
        group_id = Column(Integer, index=True)
        user_id = Column(Integer, index=True)
        character_id = Column(String, index=True)
        content = Column(Text)
        is_active = Column(Boolean, default=True)
        deactivated_at = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(
            DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        )

    db_models["Impression"] = Impression

    class Image(plugin_data.Model):
        __tablename__ = "images"
        id = Column(Integer, primary_key=True)
        file_path = Column(String(255), unique=True, nullable=False)
        file_name = Column(String(255), nullable=False)
        hash = Column(
            String(64), unique=True, nullable=False, index=True
        )  # 添加索引
        description = Column(Text)
        is_meme = Column(Boolean, default=False)
        emotion_tag = Column(String(255))  # 添加 emotion_tag 字段
        created_at = Column(DateTime, default=datetime.utcnow)

        async def add_image_record(self, image_info: Dict):
            async with get_session() as session:
                new_image = Image(**image_info)
                session.add(new_image)
                await session.commit()

        async def get_image_by_hash(self, image_hash: str) -> Optional[Dict]:
            async with get_session() as session:
                query = select(Image).where(Image.hash == image_hash)
                result = await session.execute(query)
                image = result.scalar_one_or_none()
                if image:
                    return {
                        "file_path": image.file_path,
                        "file_name": image.file_name,
                        "hash": image.hash,
                        "description": image.description,
                        "is_meme": image.is_meme,
                        "emotion_tag": image.emotion_tag,
                    }
                return None

    db_models["Image"] = Image

    class GroupConfig(plugin_data.Model):  # type: ignore
        __tablename__ = "group_configs"
        group_id = Column(Integer, primary_key=True, autoincrement=False)
        character_id = Column(String(255))
        preset_name = Column(String(255))
        inactive_threshold = Column(Integer, default=3600)
        worldbooks = relationship("GroupWorldbook", back_populates="group_config")

    db_models["GroupConfig"] = GroupConfig

    class GroupWorldbook(plugin_data.Model):  # type: ignore
        __tablename__ = "group_worldbooks"
        id = Column(Integer, primary_key=True)
        group_id = Column(Integer, ForeignKey("group_configs.group_id"))
        worldbook_name = Column(String(255))
        enabled = Column(Boolean, default=True)
        group_config = relationship("GroupConfig", back_populates="worldbooks")

    db_models["GroupWorldbook"] = GroupWorldbook
    return db_models  # 返回 db_models 字典


plugin_data = get_plugin_data("nonebot_plugin_real_netizens")

(
    User,
    Group,
    GroupUser,
    Message,
    Impression,
    Image,
    GroupConfig,
    GroupWorldbook,
) = init_models(plugin_data)

