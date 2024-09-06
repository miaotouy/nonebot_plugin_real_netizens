# character_manager.py
import asyncio
import os
from typing import Any, Dict, List, Optional, Union

from .group_config_manager import group_config_manager
from .logger import logger
from .resource_loader import character_card_loader, worldbook_loader


class CharacterManager:
    def __init__(self):
        self.character_cards: Dict[str, Dict[str, Any]] = {}
        self.worldbooks: Dict[str, List[Dict[str, Any]]] = {}
        self.character_cache: Dict[int, Dict[str, Any]] = {}  # 添加角色缓存
        group_config_manager.register_observer(self.on_config_change)  # 注册为观察者

    async def load_characters(self):
        for filename in os.listdir(character_card_loader.base_path):
            if filename.endswith(".json"):
                character_id = filename[:-5]
                await self.load_character(character_id)

    async def load_character(self, character_id: str):
        """加载单个角色"""
        try:
            character_data, worldbook_names = await character_card_loader.get_resource(character_id)
            self.character_cards[character_id] = character_data
            # 并发加载世界书
            await asyncio.gather(
                *[
                    self.worldbooks.update({worldbook_name: await worldbook_loader.get_resource(worldbook_name)})
                    for worldbook_name in worldbook_names
                    if worldbook_name not in self.worldbooks
                ]
            )
        except Exception as e:
            logger.error(f"Failed to load character {character_id}: {e}")

    def on_config_change(self, group_id: int):
        """配置更改时清除缓存"""
        if group_id in self.character_cache:
            del self.character_cache[group_id]

    def get_character_info(self, group_id: int, key: str = None) -> Optional[Union[Dict[str, Any], Any]]:
        """获取角色信息，优先从缓存获取"""
        # 获取角色ID
        character_id = group_config_manager.get_group_config(
            group_id).character_id
        # 如果没有设置角色ID，则返回None
        if not character_id:
            return None
        if group_id not in self.character_cache:
            # 如果缓存中没有，则加载角色信息
            self.character_cache[group_id] = self.character_cards.get(
                character_id, {})
        character_data = self.character_cache[group_id]
        if key is None:
            return character_data
        return character_data.get(key)

    def get_character_worldbooks(self, character_id: str) -> List[Dict[str, Any]]:
        """获取角色关联的世界书条目"""
        worldbook_names = self.character_cards.get(
            character_id, {}).get("worldbooks", [])
        worldbook_entries = []
        for worldbook_name in worldbook_names:
            worldbook_entries.extend(self.worldbooks.get(worldbook_name, []))
        return worldbook_entries


character_manager = CharacterManager()
