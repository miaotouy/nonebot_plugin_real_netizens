# nonebot_plugin_real_netizens\message_builder.py
import json
import os
import re
from string import Template
from typing import Any, Dict, List, Union

from config import Config
from nonebot import get_driver

from .character_manager import character_manager
from .resource_loader import character_card_loader, preset_loader, worldbook_loader


class MessageBuilder:
    def __init__(self, preset_name: str, worldbook_names: List[str], character_id: str):
        self.preset_data = preset_loader.get_resource(preset_name)
        self.world_info = []
        for worldbook_name in worldbook_names:
            self.world_info.extend(
                worldbook_loader.get_resource(worldbook_name))
        self.character_data = character_card_loader.get_resource(character_id)[
            0]
        self.config = Config.parse_obj(get_driver().config)

    def build_message(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        messages = []
        character_info = self.character_data

        # Prepare context for Template
        template_context = {
            "description": character_info.get("description", ""),
            "scenario": character_info.get("scenario", ""),
            "personality": character_info.get("personality", ""),
            "system": character_info.get("system", ""),
            "persona": context.get("persona", ""),
            "char": character_info.get("name", ""),
            "user": context.get("user", ""),
            "wiBefore": self.get_world_info_content("worldInfoBefore", context),
            "loreBefore": self.get_world_info_content("worldInfoBefore", context),
            "wiAfter": self.get_world_info_content("worldInfoAfter", context),
            "loreAfter": self.get_world_info_content("worldInfoAfter", context),
            "mesExamples": character_info.get("mes_example", ""),
        }

        # Add character information using Template
        char_info = self.render_template(
            self.config.character_info_template, template_context)
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
                        content = self.render_template(
                            prompt["content"], template_context)
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
            content = self.render_template(info["content"], template_context)
            messages.append({
                "role": "system",
                "content": content,
                "position": info["position"],
                "depth": info["depth"]
            })

        # Add example dialogue if available and enabled in config
        if "mes_example" in character_info and character_info["mes_example"] and self.config.include_example_messages:
            messages.append(
                {"role": "system", "content": f"Example dialogue:\n{character_info['mes_example']}"})

        # Add first message from character
        if "first_mes" in character_info and character_info["first_mes"]:
            first_mes = self.render_template(
                character_info["first_mes"], template_context)
            messages.append(
                {"role": "assistant", "content": first_mes})

        return messages

    def get_world_info_content(self, identifier: str, context: Dict[str, Any]) -> str:
        position = "before" if identifier == "worldInfoBefore" else "after"
        entries = [
            entry for entry in self.world_info
            if entry["position"] == position
        ]
        sorted_entries = sorted(entries, key=lambda x: x["order"])
        return "\n".join(entry["content"].format(**context) for entry in sorted_entries)

    def render_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template string with double curly braces syntax.

        Example:
            template_string = "Hello, {{name}}!"
            context = {"name": "world"}
            result = render_template(template_string, context)  # result will be "Hello, world!"
        """
        pattern = r"{{(.*?)}}"
        matches = re.findall(pattern, template_string)
        for match in matches:
            placeholder = f"{{{match}}}"
            try:
                value = context[match]
            except KeyError:
                # 忽略不在表里的变量，保留原字符串
                value = placeholder
            template_string = template_string.replace(placeholder, str(value))
        return template_string
