#character_manager.py
import asyncio
import os
from typing import Any, Dict, List, Optional, Union

from .resource_loader import character_card_loader, worldbook_loader


class CharacterManager:
    def __init__(self):
        self.character_cards: Dict[str, Dict[str, Any]] = {}
        self.worldbooks: Dict[str, List[Dict[str, Any]]] = {}
    async def load_characters(self):
        """加载所有角色"""
        for filename in os.listdir(character_card_loader.base_path):
            if filename.endswith(".json"):
                character_id = filename[:-5]
                await self.load_character(character_id)
    async def load_character(self, character_id: str):
        """加载单个角色"""
        character_data, worldbook_names = character_card_loader.get_resource(
            character_id
        )
        self.character_cards[character_id] = character_data
        # 并发加载世界书
        await asyncio.gather(
            *[
                self.worldbooks.update({worldbook_name: worldbook_loader.get_resource(worldbook_name)})
                for worldbook_name in worldbook_names
                if worldbook_name not in self.worldbooks
            ]
        )
    def get_character_info(
        self, character_id: str, key: str = None
    ) -> Optional[Union[Dict[str, Any], Any]]:
        """获取角色信息"""
        character_data = self.character_cards.get(character_id)
        if character_data is None:
            return None
        if key is None:
            return character_data
        return character_data.get(key)
    def get_character_worldbooks(self, character_id: str) -> List[Dict[str, Any]]:
        """获取角色关联的世界书条目"""
        worldbook_names = self.character_cards.get(character_id, {}).get(
            "worldbooks", []
        )
        worldbook_entries = []
        for worldbook_name in worldbook_names:
            worldbook_entries.extend(self.worldbooks.get(worldbook_name, []))
        return worldbook_entries
