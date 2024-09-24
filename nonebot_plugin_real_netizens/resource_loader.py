# nonebot_plugin_real_netizens\resource_loader.py
import json
import os
from logging import Logger
from typing import Any, Dict, List, Tuple, Optional

import aiofiles
from cachetools import TTLCache

from .config import plugin_config

logger = Logger(__name__)


class ResourceLoader:
    """
    资源加载器基类，负责从文件系统加载资源并缓存。

    Attributes:
        resource_type (str): 资源类型，子类需要重写，用于区分不同类型的资源。
        base_path (str): 资源文件所在的基路径。
        cache (TTLCache): 缓存已加载的资源，使用资源类型和名称组合作为键。
    """

    resource_type = "resource"  # 资源类型，子类需要重写

    def __init__(self, base_path: str, ttl: int = 3600):
        """
        初始化资源加载器。

        Args:
            base_path (str): 资源文件所在的基路径。
            ttl (int): 缓存过期时间，单位为秒，默认为 3600 秒（1 小时）。
        """
        self.base_path = base_path
        self.cache: TTLCache = TTLCache(maxsize=100, ttl=ttl)

    async def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        异步加载 JSON 文件。

        Args:
            file_path (str): JSON 文件路径。

        Returns:
            Dict[str, Any]: 解析后的 JSON 数据。

        Raises:
            FileNotFoundError: 文件不存在。
            ValueError: 文件格式错误。
        """
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"文件 {file_path} 不存在！")
        except json.JSONDecodeError:
            raise ValueError(f"文件 {file_path} 格式错误！")

    async def get_resource(self, resource_name: str) -> Optional[Any]:
        """
        获取资源。

        如果缓存中存在该资源，则直接返回缓存中的数据；
        否则，调用 `load_resource` 方法加载资源并缓存，然后返回加载后的数据。

        Args:
            resource_name (str): 资源名称。

        Returns:
            Optional[Any]: 资源数据，如果加载失败则返回 None。
        """
        cache_key = f"{self.resource_type}:{resource_name}"
        if cache_key not in self.cache:
            try:
                await self.load_resource(resource_name)
            except Exception as e:
                logger.error(
                    f"Failed to load {self.resource_type} '{resource_name}': {e}"
                )
                # 返回 None 表示加载失败
                return None
        return self.cache[cache_key]

    async def load_resource(self, resource_name: str) -> None:
        """
        加载资源到缓存。

        子类需要实现此方法，根据资源类型和名称加载资源数据，
        并将加载后的数据存储到缓存中，使用资源类型和名称组合作为键。

        Args:
            resource_name (str): 资源名称。

        Raises:
            NotImplementedError: 子类未实现此方法。
        """
        raise NotImplementedError


class WorldbookLoader(ResourceLoader):
    """
    世界书加载器，负责加载世界书文件。
    """

    resource_type = "worldbook"

    def __init__(self):
        super().__init__(os.path.join(plugin_config.RES_PATH, "world"))

    async def load_resource(self, worldbook_name: str) -> None:
        """
        异步加载世界书文件，并将解析后的条目列表存储到缓存中。

        Args:
            worldbook_name (str): 世界书名称。
        """
        file_path = os.path.join(self.base_path, f"{worldbook_name}.json")
        worldbook_data = await self._load_json_file(file_path)
        # 解析世界书条目
        entries = worldbook_data.get("entries", {}).values()
        parsed_entries = list(entries)
        cache_key = f"{self.resource_type}:{worldbook_name}"
        self.cache[cache_key] = sorted(
            parsed_entries, key=lambda x: x.get("order", 100)
        )


class PresetLoader(ResourceLoader):
    """
    预设加载器，负责加载预设文件。
    """

    resource_type = "preset"

    def __init__(self):
        super().__init__(os.path.join(plugin_config.RES_PATH, "preset"))

    async def load_resource(self, preset_name: str) -> None:
        """
        加载预设文件，并将解析后的数据存储到缓存中。

        Args:
            preset_name (str): 预设名称。
        """
        file_path = os.path.join(self.base_path, f"{preset_name}.json")
        preset_data = await self._load_json_file(file_path)
        cache_key = f"{self.resource_type}:{preset_name}"
        self.cache[cache_key] = preset_data


class CharacterCardLoader(ResourceLoader):
    """
    角色卡加载器，负责加载角色卡文件。
    """

    resource_type = "character"

    def __init__(self):
        super().__init__(os.path.join(plugin_config.RES_PATH, "character"))

    async def load_resource(self, character_id: str) -> None:
        """
        加载角色卡文件，并将解析后的数据存储到缓存中。

        Args:
            character_id (str): 角色卡 ID。
        """
        file_path = os.path.join(self.base_path, f"{character_id}.json")
        character_data = await self._load_json_file(file_path)
        cache_key = f"{self.resource_type}:{character_id}"
        self.cache[cache_key] = character_data


# 创建全局实例
worldbook_loader = WorldbookLoader()
preset_loader = PresetLoader()
character_card_loader = CharacterCardLoader()
