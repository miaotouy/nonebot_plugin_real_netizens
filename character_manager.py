# character_manager.py
import json
import os
from typing import Any, Dict, List

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.plugin import require
from nonebot.rule import to_me
from nonebot_plugin_txt2img import Txt2Img


class CharacterManager:
    def __init__(self):
        self.character_cards_dir = os.path.join(os.path.dirname(__file__), 'res', 'character')
        self.character_cards = {}
        self.load_all_characters()
    def load_all_characters(self):
        """加载所有角色卡文件"""
        for filename in os.listdir(self.character_cards_dir):
            if filename.endswith('.json'):
                character_id = filename[:-5]  # 移除 .json 后缀
                self.load_character_card(character_id)
    def load_character_card(self, character_id: str):
        """加载单个角色卡文件"""
        filepath = os.path.join(self.character_cards_dir, f"{character_id}.json")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                character_data = json.load(f)
            self.character_cards[character_id] = character_data
        except FileNotFoundError:
            raise FileNotFoundError(f"角色卡文件 {filepath} 不存在！")
        except json.JSONDecodeError:
            raise ValueError(f"角色卡文件 {filepath} 格式错误！")
    def get_character_info(self, character_id: str, key: str) -> Any:
        """获取角色卡信息"""
        if character_id not in self.character_cards:
            self.load_character_card(character_id)
        return self.character_cards[character_id].get(key, None)
    def get_all_characters(self) -> List[Dict[str, str]]:
        """获取所有角色的简要信息"""
        return [
            {"id": char_id, "name": char_data["name"], "description": char_data["description"]}
            for char_id, char_data in self.character_cards.items()
        ]
    async def switch_character(self, group_id: int, character_id: str) -> Dict[str, str]:
        """切换角色"""
        if character_id not in self.character_cards:
            raise ValueError(f"角色 {character_id} 不存在")
        # 这里需要调用 group_config_manager 来更新群组的角色设置
        from .group_config_manager import group_config_manager
        await group_config_manager.set_character(group_id, character_id)
        return {"id": character_id, "name": self.character_cards[character_id]["name"]}
# 创建一个全局实例
character_manager = CharacterManager()
# 列出角色命令
list_characters = on_command("角色列表", permission=SUPERUSER, priority=5)
@list_characters.handle()
async def handle_list_characters(bot: Bot, event: GroupMessageEvent):
    characters = character_manager.get_all_characters()
    text = "角色列表：\n" + "\n".join(f"{char['id']}. {char['name']}: {char['description'][:30]}..." for char in characters)
    image = await Txt2Img.render(text)
    await list_characters.finish(MessageSegment.image(image))
# 切换角色命令
switch_character = on_command("切换角色", permission=SUPERUSER, priority=5)
@switch_character.handle()
async def handle_switch_character(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await switch_character.finish("使用方法：切换角色 <角色ID>")
    character_id = args[1]
    group_id = event.group_id
    try:
        character = await character_manager.switch_character(group_id, character_id)
        await switch_character.finish(f"已切换到角色：{character['name']}")
    except ValueError as e:
        await switch_character.finish(str(e))
