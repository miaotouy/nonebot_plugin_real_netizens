# group_config_manager.py
from typing import Dict, List, Optional
from pydantic import BaseModel
from nonebot_plugin_datastore import get_session
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
                    world_info_paths=db_config.world_info_paths.split(',') if db_config.world_info_paths else [],
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
group_config_manager = GroupConfigManager()
