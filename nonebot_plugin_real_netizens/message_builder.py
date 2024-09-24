# nonebot_plugin_real_netizens\message_builder.py
import datetime
import random
import re
import uuid
from typing import Any, Dict, List, Tuple

from nonebot import get_driver
from .config import Config

from .resource_loader import character_card_loader, preset_loader, worldbook_loader


class MessageBuilder:
    """
    消息构建器，负责根据预设、世界书、角色卡信息、以及聊天历史构建消息列表。

    该类负责整合预设、世界书、角色卡和聊天历史等信息，生成符合角色设定的回复消息。
    它会根据预设中定义的 prompt_order 顺序，依次处理预设提示、聊天历史和世界书条目，
    并将它们插入到消息列表的适当位置。同时，它还支持使用模板字符串和上下文信息渲染消息内容，
    使得消息内容更加灵活和丰富。
    """

    def __init__(self, preset_name: str, worldbook_names: List[str], character_id: str):
        """
        初始化消息构建器。

        Args:
            preset_name (str): 预设名称。
            worldbook_names (List[str]): 世界书名称列表。
            character_id (str): 角色卡 ID。
        """
        self.preset_data = preset_loader.get_resource(preset_name)
        self.world_info = []
        for worldbook_name in worldbook_names:
            self.world_info.extend(
                worldbook_loader.get_resource(worldbook_name)[
                    "entries"].values()
            )
        self.character_data = character_card_loader.get_resource(character_id)[
            0]
        self.config = Config.parse_obj(get_driver().config)

        # 获取角色对应的 prompt_order
        self.prompt_order = next(
            (
                order["order"]
                for order in self.preset_data.get("prompt_order", [])
                if str(order["character_id"]) == self.character_data["name"]
            ),
            [],
        )

    def build_message(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        构建消息列表。

        根据预设、世界书、角色卡、聊天记录以及传入的上下文，构建一个包含多条消息的列表。
        每条消息都是一个字典，包含 "role" 和 "content" 两个字段，分别表示消息发送者的角色和消息内容。

        Args:
            context (Dict[str, Any]): 上下文信息，包括用户名、角色名、聊天记录、最后一条消息等。

        Returns:
            List[Dict[str, str]]: 消息列表。
        """
        messages = []
        character_info = self.character_data

        # 准备用于模板渲染的上下文
        template_context = {
            "description": character_info.get("description", ""),
            "scenario": character_info.get("scenario", ""),
            "personality": character_info.get("personality", ""),
            "system": character_info.get("system", ""),
            "persona": context.get("persona", ""),
            "char": character_info.get("name", ""),
            "user": context.get("user", ""),
            "wiBefore": self.get_world_info_content("before", context),
            "loreBefore": self.get_world_info_content("before", context),
            "wiAfter": self.get_world_info_content("after", context),
            "loreAfter": self.get_world_info_content("after", context),
            "mesExamples": character_info.get("mes_example", ""),
            "chat_history": context.get("chat_history", [])
        }

        # 获取聊天历史
        chat_history = context.get("chat_history", [])

        # 为聊天历史中的消息生成唯一的 message_id
        for message in chat_history:
            message["message_id"] = str(uuid.uuid4())

        # 添加角色信息
        char_info = self.render_template(
            self.config.character_info_template, template_context
        )
        messages.append({"role": "system", "content": char_info,
                        "message_id": str(uuid.uuid4())})

        # 提取 position 为 0, 1, 2, 3 和 4 的世界书条目
        before_entries = sorted([entry for entry in self.world_info if entry["position"] == 0 and not entry["disable"] and (
            not entry["useProbability"] or (entry["probability"] / 100) >= random.random())], key=lambda x: x["order"])
        after_entries = sorted([entry for entry in self.world_info if entry["position"] == 1 and not entry["disable"] and (
            not entry["useProbability"] or (entry["probability"] / 100) >= random.random())], key=lambda x: x["order"])
        before_author_notes_entries = sorted([entry for entry in self.world_info if entry["position"] == 2 and not entry["disable"] and (
            not entry["useProbability"] or (entry["probability"] / 100) >= random.random())], key=lambda x: x["order"])
        after_author_notes_entries = sorted([entry for entry in self.world_info if entry["position"] == 3 and not entry["disable"] and (
            not entry["useProbability"] or (entry["probability"] / 100) >= random.random())], key=lambda x: x["order"])
        during_entries = sorted([entry for entry in self.world_info if entry["position"] == 4 and not entry["disable"] and (
            not entry["useProbability"] or (entry["probability"] / 100) >= random.random())], key=lambda x: (-x["depth"], x["order"]))

        # 插入 position 为 0 的世界书条目
        for entry in before_entries:
            messages.insert(1, {"role": self.get_role_from_entry(entry), "content": self.render_template(
                entry["content"], template_context), "message_id": str(uuid.uuid4())})

        # 添加角色描述
        char_description_index = len(messages)
        if character_info.get("description"):
            messages.append(
                {"role": "system", "content": character_info["description"], "message_id": str(uuid.uuid4())})

        # 插入 position 为 1 的世界书条目
        for entry in after_entries:
            messages.insert(char_description_index + 1, {"role": self.get_role_from_entry(
                entry), "content": self.render_template(entry["content"], template_context), "message_id": str(uuid.uuid4())})

        # 插入 position 为 2 的世界书条目
        for entry in before_author_notes_entries:
            messages.append({"role": self.get_role_from_entry(entry), "content": self.render_template(
                entry["content"], template_context), "message_id": str(uuid.uuid4())})

        # 插入 position 为 3 的世界书条目
        for entry in after_author_notes_entries:
            messages.append({"role": self.get_role_from_entry(entry), "content": self.render_template(
                entry["content"], template_context), "message_id": str(uuid.uuid4())})

        # 按照 prompt_order 的顺序处理预设提示和聊天历史
        message_ids = [message["message_id"] for message in messages]
        for prompt_item in self.prompt_order:
            if prompt_item["enabled"]:
                # 处理预设提示
                if prompt_item["identifier"] != "chatHistory":
                    prompt = next(
                        (
                            p
                            for p in self.preset_data["prompts"]
                            if p["identifier"] == prompt_item["identifier"]
                        ),
                        None,
                    )
                    if prompt:
                        content = self.render_template(
                            prompt["content"], template_context
                        )
                        # 检查预设提示是否包含 depth 字段
                        if "depth" in prompt:
                            depth = prompt["depth"]
                            if depth < len(message_ids):
                                insert_index = message_ids[depth]
                                messages.insert(messages.index(next((m for m in messages if m["message_id"] == insert_index), None)), {
                                                "role": prompt["role"], "content": content, "message_id": str(uuid.uuid4())})
                                message_ids = [message["message_id"]
                                               for message in messages]  # 更新 message_ids 列表
                            else:
                                messages.append(
                                    {"role": prompt["role"], "content": content, "message_id": str(uuid.uuid4())})
                                message_ids.append(str(uuid.uuid4()))
                        else:
                            # 如果预设提示没有 depth 字段，则直接添加到 messages 列表末尾
                            messages.append(
                                {"role": prompt["role"], "content": content, "message_id": str(uuid.uuid4())})
                            message_ids.append(str(uuid.uuid4()))
                # 处理聊天历史
                else:
                    # 将聊天历史消息添加到 messages 列表
                    messages.extend(chat_history)
                    message_ids.extend([message["message_id"]
                                       for message in chat_history])

        # 处理 position 为 4 的世界书条目和包含 depth 字段的预设提示和角色卡条目
        for entry in during_entries:
            if "depth" not in entry:
                print(
                    f"警告: 世界书条目 {entry.get('uid', '未知')} 缺少 depth 字段，已跳过该条目。")
                continue
            depth = entry["depth"]
            if depth < len(message_ids):
                insert_index = message_ids[depth]
                messages.insert(messages.index(next((m for m in messages if m["message_id"] == insert_index), None)), {
                                "role": self.get_role_from_entry(entry), "content": self.render_template(entry["content"], template_context), "message_id": str(uuid.uuid4())})
                message_ids = [message["message_id"]
                               for message in messages]  # 更新 message_ids 列表
            else:
                messages.append({"role": self.get_role_from_entry(
                    entry), "content": self.render_template(entry["content"], template_context), "message_id": str(uuid.uuid4())})
                message_ids.append(str(uuid.uuid4()))

        # 添加示例对话（如果可用且在配置中启用）
        if (
            character_info.get("mes_example")
            and self.config.include_example_messages
        ):
            messages.append(
                {"role": "system", "content": f"Example dialogue:\n{character_info['mes_example']}", "message_id": str(uuid.uuid4())})

        # 添加角色的第一条消息
        if character_info.get("first_mes"):
            first_mes = self.render_template(
                character_info["first_mes"], template_context
            )
            messages.append(
                {"role": "assistant", "content": first_mes, "message_id": str(uuid.uuid4())})

        # 移除 message_id 字段
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def get_role_from_entry(self, entry):
        """
        根据世界书条目的 role 字段获取角色。

        Args:
            entry (Dict[str, Any]): 世界书条目。

        Returns:
            str: 角色名称，可以是 "system"、"user" 或 "assistant"。
        """
        if entry["role"] == 0:
            return "system"
        elif entry["role"] == 1:
            return "user"
        elif entry["role"] == 2:
            return "assistant"
        else:
            return "system"  # 默认角色为 system

    def get_world_info_content(self, position: str, context: Dict[str, Any]) -> str:
        """
        获取指定位置的世界书信息内容。

        Args:
            position (str): 位置，可以是 "before" 或 "after"。
            context (Dict[str, Any]): 上下文信息，用于渲染模板。

        Returns:
            str: 世界书信息内容。
        """
        entries = [
            entry
            for entry in self.world_info
            if entry["position"] in [0, 1]
            and (
                position == "before"
                and entry["position"] == 0
                or position == "after"
                and entry["position"] == 1
            )
        ]
        sorted_entries = sorted(entries, key=lambda x: x["order"])
        return "\n".join(
            self.render_template(entry["content"], context)
            for entry in sorted_entries
            if not entry["disable"]
        )

    def render_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        渲染模板字符串。

        支持以下宏：
            {{user}} 和 <USER>: 用户名。
            {{char}} 和 <BOT>: 角色名。
            {{description}}: 角色描述。
            {{personality}}: 角色性格。
            {{persona}}: 用户的角色描述。
            {{mesExamples}}: 角色的对话示例（未更改且未拆分）。
            {{lastMessage}}: 最后一条聊天消息文本。
            {{time}}: 当前系统时间。
            {{time_UTC±X}}: 指定 UTC 偏移量（时区）的当前时间，例如 UTC+02:00 使用 {{time_UTC+2}}。
            {{date}}: 当前系统日期。
            {{weekday}}: 当前星期几。
            {{isotime}}: 当前 ISO 时间（24 小时制）。
            {{isodate}}: 当前 ISO 日期（YYYY-MM-DD）。
            {{lastCharMessage}}: 角色发送的最后一条聊天消息。
            {{lastUserMessage}}: 用户发送的最后一条聊天消息。

        Args:
            template_string (str): 模板字符串。
            context (Dict[str, Any]): 上下文信息，用于替换模板中的变量。

        Returns:
            str: 渲染后的字符串。
        """

        # 获取聊天历史
        chat_history = context.get("chat_history", [])

        # 替换宏
        template_string = template_string.replace(
            "{{user}}", context.get("user", ""))
        template_string = template_string.replace(
            "<USER>", context.get("user", ""))
        template_string = template_string.replace(
            "{{char}}", context.get("char", ""))
        template_string = template_string.replace(
            "<BOT>", context.get("char", ""))
        template_string = template_string.replace(
            "{{description}}", context.get("description", "")
        )
        template_string = template_string.replace(
            "{{personality}}", context.get("personality", "")
        )
        template_string = template_string.replace(
            "{{persona}}", context.get("persona", "")
        )
        template_string = template_string.replace(
            "{{mesExamples}}", context.get("mesExamples", "")
        )

        # 获取最后一条消息、角色发送的最后一条消息和用户发送的最后一条消息
        last_message = chat_history[-1]["content"] if chat_history else ""
        last_char_message = ""
        last_user_message = ""
        for message in reversed(chat_history):
            if message["role"] == "assistant":
                last_char_message = message["content"]
                break
        for message in reversed(chat_history):
            if message["role"] == "user":
                last_user_message = message["content"]
                break

        # 替换最后一条消息相关的宏
        template_string = template_string.replace(
            "{{lastMessage}}", last_message)
        template_string = template_string.replace(
            "{{lastCharMessage}}", last_char_message)
        template_string = template_string.replace(
            "{{lastUserMessage}}", last_user_message)

        # 替换时间和日期相关的宏
        now = datetime.datetime.now(datetime.timezone.utc)
        template_string = template_string.replace(
            "{{time}}", now.strftime("%H:%M:%S"))
        template_string = template_string.replace(
            "{{date}}", now.strftime("%Y-%m-%d"))
        template_string = template_string.replace(
            "{{weekday}}", now.strftime("%A")
        )
        template_string = template_string.replace(
            "{{isotime}}", now.isoformat())
        template_string = template_string.replace(
            "{{isodate}}", now.strftime("%Y-%m-%d"))

        # 处理 {{time_UTC±X}} 宏
        time_utc_pattern = r"{{\{time_UTC([+-]\d+)\}\}}"
        matches = re.findall(time_utc_pattern, template_string)
        for match in matches:
            offset = int(match)
            utc_time = now + datetime.timedelta(hours=offset)
            template_string = template_string.replace(
                f"{{{{time_UTC{match}}}}}", utc_time.strftime("%H:%M:%S")
            )

        # 处理其他模板变量
        pattern = r"{{(.*?)}}"
        matches = re.findall(pattern, template_string)
        for match in matches:
            placeholder = f"{{{{{match}}}}}"
            try:
                value = context.get(match.strip(), placeholder)
            except KeyError:
                value = placeholder
            template_string = template_string.replace(placeholder, str(value))

        return template_string
