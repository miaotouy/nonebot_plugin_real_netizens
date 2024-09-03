import json
import os
from typing import Dict, Any
class CharacterManager:
    def __init__(self, character_cards_dir: str):
        self.character_cards_dir = character_cards_dir
        self.character_cards = {}
    def load_character_card(self, character_id: str):
        """加载角色卡文件"""
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
