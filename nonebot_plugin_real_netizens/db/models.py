# nonebot_plugin_real_netizens\db\models.py
from datetime import datetime, timezone
from nonebot_plugin_datastore import get_plugin_data
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base, relationship
# 使用 declarative_base() 定义基类
Base = declarative_base()
# 定义模型类


class User(Base):
    __tablename__ = "real_netizens_users"
    __table_args__ = (
        Index("idx_user_last_active", "last_active_time"),
    )
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

    @hybrid_property
    def last_message_content(self):
        return self.messages[-1].content if self.messages else None


class Group(Base):
    __tablename__ = "real_netizens_groups"
    __table_args__ = (
        Index("idx_group_name", "group_name"),
    )
    group_id = Column(Integer, primary_key=True, autoincrement=False)
    group_name = Column(String(64))
    users = relationship("GroupUser", back_populates="group")
    messages = relationship("Message", back_populates="group")


class GroupUser(Base):
    __tablename__ = "real_netizens_group_users"
    __table_args__ = (
        Index("idx_group_user", "group_id", "user_id"),
    )
    group_id = Column(Integer, ForeignKey(
        "real_netizens_groups.group_id"), primary_key=True)
    user_id = Column(Integer, ForeignKey(
        "real_netizens_users.user_id"), primary_key=True)
    nickname = Column(String(64))
    role = Column(String(64), default="member")
    join_time = Column(DateTime)
    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="users")


class Message(Base):
    __tablename__ = "real_netizens_messages"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("real_netizens_groups.group_id"))
    user_id = Column(Integer, ForeignKey("real_netizens_users.user_id"))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(
        timezone.utc), index=True)
    group = relationship("Group", back_populates="messages")
    user = relationship("User", back_populates="messages")


class Impression(Base):
    __tablename__ = "real_netizens_impressions"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    character_id = Column(String, index=True)
    content = Column(Text)
    is_active = Column(Boolean, default=True)
    deactivated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )


class Image(Base):
    __tablename__ = "real_netizens_images"
    id = Column(Integer, primary_key=True)
    file_path = Column(String(255), unique=True, nullable=False)
    file_name = Column(String(255), nullable=False)
    hash = Column(
        String(64), unique=True, nullable=False, index=True
    )  # 添加索引
    description = Column(Text)
    is_meme = Column(Boolean, default=False)
    emotion_tag = Column(String(255))  # 添加 emotion_tag 字段
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class GroupConfig(Base):
    __tablename__ = "real_netizens_group_configs"
    group_id = Column(Integer, primary_key=True, autoincrement=False)
    character_id = Column(String(255))
    preset_name = Column(String(255))
    inactive_threshold = Column(Integer, default=3600)
    worldbooks = relationship("GroupWorldbook", back_populates="group_config")


class GroupWorldbook(Base):
    __tablename__ = "real_netizens_group_worldbooks"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey(
        "real_netizens_group_configs.group_id"))
    worldbook_name = Column(String(255))
    enabled = Column(Boolean, default=False)
    group_config = relationship("GroupConfig", back_populates="worldbooks")
# 初始化模型


def init_models(plugin_data):
    # plugin_data.Model = Base  # 将 Base 设置为插件的模型基类
    return {
        "User": User,
        "Group": Group,
        "GroupUser": GroupUser,
        "Message": Message,
        "Impression": Impression,
        "Image": Image,
        "GroupConfig": GroupConfig,
        "GroupWorldbook": GroupWorldbook,
    }


# 插件初始化
plugin_data = get_plugin_data("nonebot_plugin_real_netizens")
db_models = init_models(plugin_data)
User = db_models["User"]
Group = db_models["Group"]
GroupUser = db_models["GroupUser"]
Message = db_models["Message"]
Impression = db_models["Impression"]
Image = db_models["Image"]
GroupConfig = db_models["GroupConfig"]
GroupWorldbook = db_models["GroupWorldbook"]
