from datetime import datetime

from sqlalchemy import (Column, DateTime, ForeignKey, Index, Integer, String,
                        Text)
from sqlalchemy.orm import relationship


def init_models(plugin_data):
    db = plugin_data.database

    class User(db.Model):  # type: ignore
        __tablename__ = 'users'
        user_id = Column(Integer, primary_key=True, autoincrement=False)
        nickname = Column(String(64))
        avatar = Column(String(255))
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
    return User, Group, GroupUser, Message
