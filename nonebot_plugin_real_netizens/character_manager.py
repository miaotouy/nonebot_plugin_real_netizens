# nonebot_plugin_real_netizens\character_manager.py
import asyncio
import os
from typing import Any, Dict, List, Optional, Union
from .logger import logger
from .resource_loader import character_card_loader, worldbook_loader
class CharacterManager:
    """
    角色管理器，负责加载和管理角色卡信息，以及世界书内容。
    """
    def __init__(self, group_config_manager):  # 添加 group_config_manager 参数
        """
        初始化角色管理器。
        """
        self.character_cards: Dict[str, Dict[str, Any]] = {}
        self.worldbooks: Dict[str, List[Dict[str, Any]]] = {}
        self.character_cache: Dict[int, Dict[str, Any]] = {}
        self.group_config_manager = group_config_manager  # 存储 group_config_manager
        self.group_config_manager.register_observer(self.on_config_change)  # 注册为观察者
    async def load_characters(self):
        """
        加载所有角色卡和世界书信息。
        """
        # 加载 character 文件夹下的所有角色卡
        for filename in os.listdir(character_card_loader.base_path):
            if filename.endswith(".json"):
                character_id = filename[:-5]
                await self.load_character(character_id)
    async def load_character(self, character_id: str):
        """
        加载单个角色卡和关联的世界书。
        Args:
            character_id: 角色卡 ID。
        """
        try:
            # 从资源加载器获取角色卡数据和世界书列表
            character_data, worldbook_names = await character_card_loader.get_resource(
                character_id
            )
            self.character_cards[character_id] = character_data
            # 并发加载世界书
            await asyncio.gather(
                *[
                    self.worldbooks.update(
                        {worldbook_name: await worldbook_loader.get_resource(worldbook_name)}
                    )
                    for worldbook_name in worldbook_names
                    if worldbook_name not in self.worldbooks
                ]
            )
        except Exception as e:
            logger.error(f"Failed to load character {character_id}: {e}")
    def on_config_change(self, group_id: int):
        """
        当群组配置发生变化时，清除缓存的角色信息。
        Args:
            group_id: 群组 ID。
        """
        if group_id in self.character_cache:
            del self.character_cache[group_id]
    def get_character_info(
        self, group_id: int, key: str = None
    ) -> Optional[Union[Dict[str, Any], Any]]:
        """
        获取群组当前使用的角色信息。
        Args:
            group_id: 群组 ID。
            key:  要获取的角色信息的键，如果为 None 则返回整个角色信息字典。
        Returns:
            角色信息字典或指定键对应的值，如果角色信息不存在则返回 None。
        """
        # 从群组配置中获取角色 ID
        character_id = self.group_config_manager.get_group_config(group_id).character_id # 使用self.group_config_manager
        # 如果没有设置角色 ID，则返回 None
        if not character_id:
            return None
        # 优先从缓存中获取角色信息
        if group_id not in self.character_cache:
            # 如果缓存中没有，则从 self.character_cards 中获取并添加到缓存
            self.character_cache[group_id] = self.character_cards.get(character_id, {})
        character_data = self.character_cache[group_id]
        # 如果 key 为 None，则返回整个角色信息字典，否则返回指定键对应的值
        if key is None:
            return character_data
        return character_data.get(key)
    def get_character_worldbooks(self, character_id: str) -> List[Dict[str, Any]]:
        """
        获取角色关联的世界书条目。
        Args:
            character_id: 角色卡 ID。
        Returns:
            角色关联的世界书条目列表。
        """
        worldbook_names = self.character_cards.get(
            character_id, {}).get("worldbooks", [])
        worldbook_entries = []
        for worldbook_name in worldbook_names:
            worldbook_entries.extend(self.worldbooks.get(worldbook_name, []))
        return worldbook_entries
# character_manager = CharacterManager()  # 不要在这里创建实例
