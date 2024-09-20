# nonebot_plugin_real_netizens\group_config_manager.py

import os
from typing import Callable, Dict, List, Optional

from nonebot.log import logger
from nonebot_plugin_datastore import get_session
from pydantic import BaseModel
from sqlalchemy import delete, select

from .db.models import GroupConfig as DBGroupConfig
from .db.models import GroupWorldbook
from .resource_loader import character_card_loader, preset_loader, worldbook_loader


class GroupConfig(BaseModel):
    """
    群组配置模型。

    Attributes:
        group_id: 群组 ID。
        character_id: 角色卡 ID。
        preset_name: 预设名称。
        worldbook_names: 启用的世界书名称列表。
        inactive_threshold: 非活跃阈值（秒）。
    """
    group_id: int
    character_id: Optional[str] = None
    preset_name: Optional[str] = None
    worldbook_names: List[str] = []
    inactive_threshold: int = 3600  # 默认1小时


class GroupConfigManager:
    """
    群组配置管理器。

    负责加载、获取、更新和管理群组配置。
    """

    def __init__(self):
        """
        初始化群组配置管理器。
        """
        self.configs: Dict[int, GroupConfig] = {}
        # 获取 res 目录的绝对路径
        self.res_path = os.path.join(os.path.dirname(__file__), "res")
        self.observers: List[Callable[[int], None]] = []

    def register_observer(self, observer: Callable[[int], None]):
        """
        注册观察者。

        当群组配置更新时，会通知所有已注册的观察者。

        Args:
            observer: 观察者函数，接受一个参数：群组 ID。
        """
        self.observers.append(observer)

    def notify_observers(self, group_id: int):
        """
        通知观察者。

        Args:
            group_id: 更新配置的群组 ID。
        """
        for observer in self.observers:
            observer(group_id)

    async def load_configs(self):
        """
        从数据库加载所有群组配置。
        """
        try:
            async with get_session() as session:
                group_configs = (await session.scalars(select(DBGroupConfig))).all()
                for db_config in group_configs:
                    worldbooks = (await session.scalars(
                        select(GroupWorldbook).where(
                            GroupWorldbook.group_id == db_config.group_id,
                            GroupWorldbook.enabled == True,
                        )
                    )).all()
                    self.configs[db_config.group_id] = GroupConfig(
                        group_id=db_config.group_id,
                        character_id=db_config.character_id,
                        preset_name=db_config.preset_name,
                        worldbook_names=[
                            worldbook.worldbook_name for worldbook in worldbooks],
                        inactive_threshold=db_config.inactive_threshold,
                    )
        except Exception as e:
            logger.error(f"Failed to load group configs: {e}")

    def get_group_config(self, group_id: int) -> GroupConfig:
        """
        获取指定群组的配置。

        Args:
            group_id: 群组 ID。

        Returns:
            群组配置对象。
        """
        if group_id not in self.configs:
            self.configs[group_id] = GroupConfig(group_id=group_id)
        return self.configs[group_id]

    async def update_group_config(self, config: GroupConfig):
        """
        更新指定群组的配置。

        Args:
            config: 新的群组配置对象。
        """
        try:
            async with get_session() as session:
                db_config = await session.get(DBGroupConfig, config.group_id)
                if not db_config:
                    # 新创建的群组配置，使用全局默认值
                    db_config = DBGroupConfig(
                        group_id=config.group_id,
                        character_id=config.character_id or "default_character",  # 使用 config 的值或全局默认值
                        preset_name=config.preset_name or "default_preset",
                        inactive_threshold=config.inactive_threshold
                    )
                else:
                    # 已存在的群组配置
                    if config.character_id is not None:  # 如果 config 中提供了新值
                        db_config.character_id = config.character_id
                    if config.preset_name is not None:
                        db_config.preset_name = config.preset_name
                    db_config.inactive_threshold = config.inactive_threshold

                await session.execute(delete(GroupWorldbook).where(GroupWorldbook.group_id == config.group_id))
                for worldbook_name in config.worldbook_names:
                    session.add(GroupWorldbook(
                        group_id=config.group_id,
                        worldbook_name=worldbook_name,
                        enabled=True,
                    ))
                await session.commit()

            self.configs[config.group_id] = config
            self.notify_observers(config.group_id)  # 通知观察者
        except Exception as e:
            logger.error(f"Failed to update group config: {e}")

    def get_all_groups(self) -> List[int]:
        """
        获取所有已配置的群组 ID 列表。

        Returns:
            群组 ID 列表。
        """
        return list(self.configs.keys())

    async def set_preset(self, group_id: int, preset_name: str) -> bool:
        """
        设置指定群组的预设。

        Args:
            group_id: 群组 ID。
            preset_name: 预设名称。

        Returns:
            设置成功返回 True，否则返回 False。
        """
        config = self.get_group_config(group_id)
        # 使用绝对路径拼接预设文件路径
        preset_path = os.path.join(
            self.res_path, 'preset', f"{preset_name}.json")
        if os.path.exists(preset_path):
            config.preset_name = preset_name
            await self.update_group_config(config)
            return True
        return False

    async def enable_worldbook(self, group_id: int, worldbook_name: str) -> bool:
        """
        启用指定群组的世界书。

        Args:
            group_id: 群组 ID。
            worldbook_name: 世界书名称。

        Returns:
            启用成功返回 True，否则返回 False。
        """
        config = self.get_group_config(group_id)
        # 使用绝对路径拼接世界书文件路径
        worldbook_path = os.path.join(
            self.res_path, 'world', f"{worldbook_name}.json")
        if os.path.exists(worldbook_path):
            if worldbook_name not in config.worldbook_names:
                config.worldbook_names.append(worldbook_name)
                await self.update_group_config(config)
            return True
        return False

    async def disable_worldbook(self, group_id: int, worldbook_name: str) -> bool:
        """
        禁用指定群组的世界书。

        Args:
            group_id: 群组 ID。
            worldbook_name: 世界书名称。

        Returns:
            禁用成功返回 True，否则返回 False。
        """
        config = self.get_group_config(group_id)
        if worldbook_name in config.worldbook_names:
            config.worldbook_names.remove(worldbook_name)
            await self.update_group_config(config)
            return True
        return False

    async def set_character(self, group_id: int, character_name: str) -> bool:
        """
        设置指定群组的角色卡。

        Args:
            group_id: 群组 ID。
            character_name: 角色卡名称。

        Returns:
            设置成功返回 True，否则返回 False。
        """
        config = self.get_group_config(group_id)
        if character_card_loader.get_resource(character_name):
            config.character_id = character_name
            await self.update_group_config(config)
            return True
        return False


group_config_manager = GroupConfigManager()
