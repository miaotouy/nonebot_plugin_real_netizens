# message_builder.py
import json
import os
from typing import List, Dict, Any, Union
from .config import Config
from .character_manager import CharacterManager
from nonebot import get_driver
class MessageBuilder:
    def __init__(self, preset_file: str, world_info_files: Union[str, List[str]], character_id: str):
        self.base_path = os.path.join(os.path.dirname(__file__), 'res')
        self.preset_file = os.path.join(self.base_path, 'preset', preset_file)
        self.preset_data = self.load_preset()
        self.world_info_files = [os.path.join(self.base_path, 'world', f) for f in (world_info_files if isinstance(world_info_files, list) else [world_info_files])]
        self.world_info = self.load_world_info()
        self.character_manager = CharacterManager(os.path.join(self.base_path, 'character'))
        self.character_id = character_id
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
        except PermissionError:
            raise PermissionError(f"无权限读取预设文件 {self.preset_file}！")
    def load_world_info(self) -> Dict[str, Any]:
        """加载并合并多个世界书"""
        world_info = {"entries": {}}
        for file in self.world_info_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 合并世界书条目
                world_info["entries"].update(data["entries"])
            except FileNotFoundError:
                raise FileNotFoundError(f"世界书文件 {file} 不存在！")
            except json.JSONDecodeError:
                raise ValueError(f"世界书文件 {file} 格式错误！")
            except KeyError:
                raise ValueError(f"世界书文件 {file} 缺少必要的 'entries' 字段！")
            except PermissionError:
                raise PermissionError(f"无权限读取世界书文件 {file}！")
        return world_info
    def build_message(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        messages = []
        try:
            prompt_order = next(
                (order for order in self.preset_data["prompt_order"] if order["character_id"] == int(self.character_id)),
                None
            )
            if not prompt_order:
                raise ValueError(f"预设文件中找不到角色 {self.character_id} 的配置！")
            for prompt_item in prompt_order["order"]:
                if not prompt_item["enabled"]:
                    continue
                prompt = next(
                    (p for p in self.preset_data["prompts"] if p["identifier"] == prompt_item["identifier"]),
                    None
                )
                if not prompt:
                    raise ValueError(f"预设文件中找不到标识符为 {prompt_item['identifier']} 的提示词！")
                if prompt["identifier"] in ["charDescription", "charPersonality", "scenario", "first_mes"]:
                    character_info = self.character_manager.get_character_info(self.character_id, prompt["identifier"])
                    if character_info:
                        messages.append({"role": prompt["role"], "content": character_info.format(**context)})
                elif prompt["identifier"].startswith("worldInfo"):
                    world_info_content = self.get_world_info_content(prompt["identifier"], context)
                    if world_info_content:
                        messages.append({"role": prompt["role"], "content": world_info_content})
                else:
                    prompt_content = prompt["content"].format(**context)
                    messages.append({"role": prompt["role"], "content": prompt_content})
        except AttributeError:
            raise ValueError("预设文件格式错误，缺少必要的字段！")
        except KeyError as e:
            raise ValueError(f"预设文件缺少必要的键：{str(e)}")
        except Exception as e:
            raise Exception(f"构建消息时发生未知错误：{str(e)}")
        return messages
    def get_world_info_content(self, identifier: str, context: Dict[str, Any]) -> str:
        """根据 identifier 和 position 获取世界书条目内容"""
        position = "before" if identifier == "worldInfoBefore" else "after"
        try:
            entries = [
                entry for entry in self.world_info["entries"].values()
                if entry["position"] == position and not entry["disable"]
            ]
            # 按 order 排序
            sorted_entries = sorted(entries, key=lambda x: x["order"])
            return "\n".join(entry["content"].format(**context) for entry in sorted_entries)
        except KeyError:
            raise ValueError("世界书条目格式错误，缺少必要的字段！")
        except AttributeError:
            raise ValueError("世界书条目格式错误，可能是数据类型不正确！")
