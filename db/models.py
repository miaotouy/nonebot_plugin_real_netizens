from datetime import datetime

from nonebot_plugin_datastore import get_plugin_data
from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Index, Integer,
                        String, Text)
from sqlalchemy.orm import relationship


def init_models(plugin_data):
    db = plugin_data.database

    class User(db.Model):  # type: ignore
        __tablename__ = 'users'
        user_id = Column(Integer, primary_key=True, autoincrement=False)
        nickname = Column(String(64))
        avatar = Column(String(255))
        avatar_description = Column(Text)
        last_active_time = Column(DateTime)
        displayname = Column(String(64))
        remark = Column(String(64))
        gender = Column(String(16), default='unknown')
        last_message = Column(Text)
        last_message_time = Column(DateTime)
        groups = relationship('GroupUser', back_populates='user')
        messages = relationship('Message', back_populates='user')
        __table_args__ = (
            Index('idx_user_last_active', 'last_active_time'),
        )

    class Group(db.Model):  # type: ignore
        __tablename__ = 'groups'
        group_id = Column(Integer, primary_key=True, autoincrement=False)
        group_name = Column(String(64))
        users = relationship('GroupUser', back_populates='group')
        messages = relationship('Message', back_populates='group')
        __table_args__ = (
            Index('idx_group_name', 'group_name'),
        )

    class GroupUser(db.Model):  # type: ignore
        __tablename__ = 'group_users'
        group_id = Column(Integer, ForeignKey(
            'groups.group_id'), primary_key=True)
        user_id = Column(Integer, ForeignKey(
            'users.user_id'), primary_key=True)
        nickname = Column(String(64))
        role = Column(String(64), default='member')
        join_time = Column(DateTime)
        user = relationship('User', back_populates='groups')
        group = relationship('Group', back_populates='users')
        __table_args__ = (
            Index('idx_group_user', 'group_id', 'user_id'),
        )

    class Message(db.Model):  # type: ignore
        __tablename__ = 'messages'
        id = Column(Integer, primary_key=True)
        group_id = Column(Integer, ForeignKey('groups.group_id'))
        user_id = Column(Integer, ForeignKey('users.user_id'))
        content = Column(Text)
        timestamp = Column(DateTime, default=datetime.utcnow)
        group = relationship('Group', back_populates='messages')
        user = relationship('User', back_populates='messages')
        __table_args__ = (
            Index('idx_message_timestamp', 'timestamp'),
        )

    class Impression(db.Model):
        __tablename__ = 'impressions'
        id = Column(Integer, primary_key=True)
        group_id = Column(Integer, index=True)
        user_id = Column(Integer, index=True)
        character_id = Column(String, index=True)
        content = Column(Text)
        is_active = Column(Boolean, default=True)
        deactivated_at = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)
    
    class Image(db.Model):
        __tablename__ = 'images'
        id = Column(Integer, primary_key=True)
        file_path = Column(String(255), unique=True, nullable=False)
        file_name = Column(String(255), nullable=False)
        hash = Column(String(64), unique=True, nullable=False)
        description = Column(Text)
        is_meme = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    return User, Group, GroupUser, Message, Impression, Image

plugin_data = get_plugin_data()
User, Group, GroupUser, Message, Impression, Image = init_models(plugin_data)