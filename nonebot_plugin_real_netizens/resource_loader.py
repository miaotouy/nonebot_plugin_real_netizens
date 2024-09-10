# nonebot_plugin_real_netizens\resource_loader.py
import json
import os
from logging import Logger
from typing import Any, Dict, List, Tuple

import aiofiles
from cachetools import TTLCache

from .config import plugin_config


class ResourceLoader:
    """资源加载器基类"""

    def __init__(self, base_path: str, ttl: int = 3600):
        self.base_path = base_path
        # 使用 TTLCache，设置缓存过期时间为 ttl 秒
        self.cache: TTLCache = TTLCache(maxsize=100, ttl=ttl)

    async def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """异步加载JSON文件"""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"文件 {file_path} 不存在！")
        except json.JSONDecodeError:
            raise ValueError(f"文件 {file_path} 格式错误！")

    async def get_resource(self, resource_id: str) -> Any:
        """获取资源，如果缓存中没有则加载"""
        if resource_id not in self.cache:
            try:
                await self.load_resource(resource_id)
            except Exception as e:
                logger = Logger(__name__)
                logger.error(f"Failed to load resource '{resource_id}': {e}")
                # 返回默认值，避免程序崩溃
                if isinstance(self, WorldbookLoader):
                    self.cache[resource_id] = await self.load_resource(plugin_config.DEFAULT_WORLDBOOK)
                elif isinstance(self, PresetLoader):
                    self.cache[resource_id] = await self.load_resource(plugin_config.DEFAULT_PRESET)
                elif isinstance(self, CharacterCardLoader):
                    self.cache[resource_id] = await self.load_resource(plugin_config.DEFAULT_CHARACTER_ID)[0]
        return self.cache[resource_id]

    async def load_resource(self, resource_id: str):
        """加载资源到缓存，需要子类实现"""
        raise NotImplementedError


class WorldbookLoader(ResourceLoader):
    """世界书加载器"""

    def __init__(self):
        super().__init__(os.path.join(plugin_config.RES_PATH, "world"))

    async def load_resource(self, worldbook_name: str):
        """异步加载世界书"""
        file_path = os.path.join(self.base_path, f"{worldbook_name}.json")
        worldbook_data = await self._load_json_file(file_path)
        # 解析世界书条目
        entries = worldbook_data["entries"].values()
        parsed_entries = [
            {
                "content": entry["content"],
                "position": entry["position"],
                "order": entry.get("order", 100),
                "depth": entry.get("depth", 4),
            }
            for entry in entries
            if not entry.get("disable", False)
        ]
        self.cache[worldbook_name] = sorted(
            parsed_entries, key=lambda x: x["order"])


class PresetLoader(ResourceLoader):
    """预设加载器"""

    def __init__(self):
        super().__init__(os.path.join(plugin_config.RES_PATH, "preset"))

    async def load_resource(self, preset_name: str):
        """加载预设"""
        file_path = os.path.join(self.base_path, f"{preset_name}.json")
        preset_data = await self._load_json_file(file_path)
        self.cache[preset_name] = preset_data


class CharacterCardLoader(ResourceLoader):
    """角色卡加载器"""

    def __init__(self):
        super().__init__(os.path.join(plugin_config.RES_PATH, "character"))

    async def load_resource(self, character_id: str) -> Tuple[Dict[str, Any], List[str]]:
        """加载角色卡，并返回角色卡数据和世界书列表"""
        file_path = os.path.join(self.base_path, f"{character_id}.json")
        character_data = await self._load_json_file(file_path)
        worldbook_names = character_data.get("worldbooks", [])
        self.cache[character_id] = character_data
        return character_data, worldbook_names


# 创建全局实例
worldbook_loader = WorldbookLoader()
preset_loader = PresetLoader()
character_card_loader = CharacterCardLoader()
