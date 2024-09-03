#models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from nonebot_plugin_datastore import PluginData
db = PluginData(__name__).database
class User(db.Model):  # type: ignore
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    nickname = Column(String(64))
    avatar = Column(String(255))
    last_active_time = Column(DateTime)
    displayname = Column(String(64))
    remark = Column(String(64))
    gender = Column(String(16), default='unknown')
    last_message = Column(Text, default=None)
    last_message_time = Column(DateTime, default=None)
    groups = relationship('GroupUser', back_populates='user')
class Group(db.Model):  # type: ignore
    __tablename__ = 'groups'
    group_id = Column(Integer, primary_key=True, autoincrement=False)
    group_name = Column(String(64))
    users = relationship('GroupUser', back_populates='group')
class GroupUser(db.Model):  # type: ignore
    __tablename__ = 'group_users'
    group_id = Column(Integer, ForeignKey('groups.group_id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    nickname = Column(String(64))
    role = Column(String(64), default='member')
    join_time = Column(DateTime)
    user = relationship('User', back_populates='groups')
    group = relationship('Group', back_populates='users')
