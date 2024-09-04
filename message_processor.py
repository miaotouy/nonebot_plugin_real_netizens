# message_processor.py
from typing import Dict, List, Optional

from nonebot import get_driver
from nonebot_plugin_datastore import get_session

from .config import Config
from .db.database import get_recent_messages
from .llm_generator import llm_generator
from .message_builder import MessageBuilder

plugin_config = Config.parse_obj(get_driver().config)


async def process_message(event, message_builder: MessageBuilder) -> Optional[str]:
    # 获取消息内容
    message_content = event.get_plaintext()
    try:
        # 获取最近的消息
        async with get_session() as session:
            recent_messages = await get_recent_messages(session, event.group_id, limit=plugin_config.CONTEXT_MESSAGE_COUNT)
            context = [{"role": "user" if msg.user_id != event.self_id else "assistant",
                        "content": msg.content} for msg in reversed(recent_messages)]
        # 使用 MessageBuilder 构建消息
        messages = message_builder.build_message(
            {"user": event.sender.nickname})
        messages.extend(context)
        # 添加当前消息到上下文
        messages.append({"role": "user", "content": message_content})
        # 调用 LLM 生成回复
        response = await llm_generator.generate_response(
            messages=messages,
            model=plugin_config.LLM_MODEL,
            temperature=plugin_config.LLM_TEMPERATURE,
            max_tokens=plugin_config.LLM_MAX_TOKENS
        )
        return response
    except FileNotFoundError as e:
        return f"文件加载失败，请检查配置文件和相关资源文件。错误信息：{str(e)}"
    except ValueError as e:
        return f"配置或数据格式错误，请检查相关文件。错误信息：{str(e)}"
    except PermissionError as e:
        return f"无权限访问某些文件，请检查文件权限。错误信息：{str(e)}"
    except ConnectionError as e:
        return f"网络连接失败，请检查网络状态和API设置。错误信息：{str(e)}"
    except Exception as e:
        return f"发生未知错误，请联系管理员。错误信息：{str(e)}"
