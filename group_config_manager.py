# group_config_manager.py
import os
from typing import Dict, List, Optional

from nonebot_plugin_datastore import get_session
from pydantic import BaseModel
from sqlalchemy import select

from .db.models import GroupConfig as DBGroupConfig


class GroupConfig(BaseModel):
    group_id: int
    character_id: Optional[str] = None
    preset_path: Optional[str] = None
    world_info_paths: List[str] = []
    inactive_threshold: int = 3600  # 默认1小时


class GroupConfigManager:
    def __init__(self):
        self.configs: Dict[int, GroupConfig] = {}

    async def load_configs(self):
        async with get_session() as session:
            query = select(DBGroupConfig)
            result = await session.execute(query)
            db_configs = result.scalars().all()
            for db_config in db_configs:
                self.configs[db_config.group_id] = GroupConfig(
                    group_id=db_config.group_id,
                    character_id=db_config.character_id,
                    preset_path=db_config.preset_path,
                    world_info_paths=db_config.world_info_paths.split(
                        ',') if db_config.world_info_paths else [],
                    inactive_threshold=db_config.inactive_threshold
                )

    def get_group_config(self, group_id: int) -> GroupConfig:
        if group_id not in self.configs:
            self.configs[group_id] = GroupConfig(group_id=group_id)
        return self.configs[group_id]

    async def update_group_config(self, config: GroupConfig):
        self.configs[config.group_id] = config
        async with get_session() as session:
            db_config = await session.get(DBGroupConfig, config.group_id)
            if not db_config:
                db_config = DBGroupConfig(group_id=config.group_id)

            db_config.character_id = config.character_id
            db_config.preset_path = config.preset_path
            db_config.world_info_paths = ','.join(config.world_info_paths)
            db_config.inactive_threshold = config.inactive_threshold
            session.add(db_config)
            await session.commit()

    def get_all_groups(self) -> List[int]:
        return list(self.configs.keys())

    async def set_preset(self, group_id: int, preset_name: str) -> bool:
        config = self.get_group_config(group_id)
        preset_path = f"preset/{preset_name}.json"
        if os.path.exists(os.path.join(self.base_path, preset_path)):
            config.preset_path = preset_path
            await self.update_group_config(config)
            return True
        return False

    async def enable_worldbook(self, group_id: int, worldbook_name: str) -> bool:
        config = self.get_group_config(group_id)
        worldbook_path = f"world/{worldbook_name}.json"
        if os.path.exists(os.path.join(self.base_path, worldbook_path)):
            if worldbook_path not in config.world_info_paths:
                config.world_info_paths.append(worldbook_path)
                await self.update_group_config(config)
            return True
        return False

    async def disable_worldbook(self, group_id: int, worldbook_name: str) -> bool:
        config = self.get_group_config(group_id)
        worldbook_path = f"world/{worldbook_name}.json"
        if worldbook_path in config.world_info_paths:
            config.world_info_paths.remove(worldbook_path)
            await self.update_group_config(config)
            return True
        return False

    async def set_character(self, group_id: int, character_name: str) -> bool:
        config = self.get_group_config(group_id)
        if character_name in self.character_manager.get_character_list():
            config.character_id = character_name
            await self.update_group_config(config)
            return True
        return False


group_config_manager = GroupConfigManager()
