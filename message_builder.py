# message_builder.py
import json
import os
from typing import Any, Dict, List, Union

from nonebot import get_driver

from .config import Config


class MessageBuilder:
    def __init__(self, preset_file: str, world_info_files: Union[str, List[str]], character_id: str):
        self.base_path = os.path.join(os.path.dirname(__file__), 'res')
        self.preset_file = os.path.join(self.base_path, 'preset', preset_file)
        self.preset_data = self.load_preset()
        self.world_info_files = [os.path.join(self.base_path, 'world', f) for f in (
            world_info_files if isinstance(world_info_files, list) else [world_info_files])]
        self.world_info = self.load_world_info()
        self.character_file = os.path.join(
            self.base_path, 'character', f"{character_id}.json")
        self.character_data = self.load_character()
        self.config = Config.parse_obj(get_driver().config)

    def load_preset(self) -> Dict[str, Any]:
        try:
            with open(self.preset_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"预设文件 {self.preset_file} 不存在！")
        except json.JSONDecodeError:
            raise ValueError(f"预设文件 {self.preset_file} 格式错误！")

    def load_world_info(self) -> List[Dict[str, Any]]:
        world_info = []
        for file in self.world_info_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for entry in data["entries"].values():
                        if not entry.get("disable", False):
                            world_info.append({
                                "content": entry["content"],
                                "position": entry["position"],
                                "order": entry.get("order", 100),
                                "depth": entry.get("depth", 4)
                            })
            except FileNotFoundError:
                raise FileNotFoundError(f"世界书文件 {file} 不存在！")
            except json.JSONDecodeError:
                raise ValueError(f"世界书文件 {file} 格式错误！")
        return sorted(world_info, key=lambda x: x["order"])

    def load_character(self) -> Dict[str, Any]:
        try:
            with open(self.character_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"角色卡文件 {self.character_file} 不存在！")
        except json.JSONDecodeError:
            raise ValueError(f"角色卡文件 {self.character_file} 格式错误！")

    def build_message(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        messages = []
        character_info = self.character_data
        # Add character information
        char_info = f"Character name: {character_info['name']}\n"
        char_info += f"Description: {character_info['description']}\n"
        if 'personality' in character_info:
            char_info += f"Personality: {character_info['personality']}\n"
        if 'scenario' in character_info:
            char_info += f"Scenario: {character_info['scenario']}\n"
        messages.append({"role": "system", "content": char_info})
        # Process preset prompts
        prompt_order = next((order for order in self.preset_data["prompt_order"] if order["character_id"] == int(
            self.character_data["name"])), None)
        if prompt_order:
            for prompt_item in prompt_order["order"]:
                if prompt_item["enabled"]:
                    prompt = next(
                        (p for p in self.preset_data["prompts"] if p["identifier"] == prompt_item["identifier"]), None)
                    if prompt:
                        content = prompt["content"].format(**context)
                        message = {
                            "role": prompt["role"],
                            "content": content
                        }
                        if "injection_position" in prompt:
                            message["injection_position"] = prompt["injection_position"]
                        if "injection_depth" in prompt:
                            message["injection_depth"] = prompt["injection_depth"]
                        messages.append(message)
        # Add world info
        for info in self.world_info:
            messages.append({
                "role": "system",
                "content": info["content"],
                "position": info["position"],
                "depth": info["depth"]
            })
        # Add example dialogue if available
        if "mes_example" in character_info and character_info["mes_example"]:
            messages.append(
                {"role": "system", "content": f"Example dialogue:\n{character_info['mes_example']}"})
        # Add first message from character
        if "first_mes" in character_info and character_info["first_mes"]:
            messages.append(
                {"role": "assistant", "content": character_info["first_mes"]})
        return messages

    def get_world_info_content(self, identifier: str, context: Dict[str, Any]) -> str:
        position = "before" if identifier == "worldInfoBefore" else "after"
        entries = [
            entry for entry in self.world_info
            if entry["position"] == position
        ]
        sorted_entries = sorted(entries, key=lambda x: x["order"])
        return "\n".join(entry["content"].format(**context) for entry in sorted_entries)
