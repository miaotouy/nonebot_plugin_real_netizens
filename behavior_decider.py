# behavior_decider.py
import json
import logging
from typing import Dict, List
from .character_manager import character_manager
from .config import plugin_config
from .llm_generator import llm_generator
from .memory_manager import memory_manager
from .message_builder import MessageBuilder
logger = logging.getLogger(__name__)
async def decide_behavior(message: str, recent_messages: List[Dict], message_builder: MessageBuilder, user_id: int, character_id: str) -> Dict:
    """根据角色设定、用户印象和最近的对话历史，决定是否回复消息以及回复类型。
    Args:
        message: 接收到的消息内容.
        recent_messages: 最近的几条消息
        message_builder: 消息构建器.
        user_id: 用户ID.
        character_id: 角色ID.
    Returns:
        包含决策结果的字典，例如：
        {
          "thoughts": "AI的思考过程",
          "reason": "决策理由",
          "should_reply": True/False,
          "reply_type": "text/image/mixed",
          "impression_update": {
            "user_id": 123456789,
            "content": "对用户印象的更新"
          }
        }
    """
    # 使用 message_builder 构建 prompt
    context = {
        "user_id": user_id,
        "message": message,
        "recent_messages": recent_messages,
        "character_info": character_manager.get_character_info(character_id),
        "user_impression": await memory_manager.get_impression(group_id, user_id, character_id) # type: ignore
    }
    messages = message_builder.build_message(context)
    # 调用LLM生成决策结果
    response = await llm_generator.generate_response(
        messages=messages,
        model=plugin_config.LLM_MODEL,
        temperature=plugin_config.LLM_TEMPERATURE,
        max_tokens=plugin_config.LLM_MAX_TOKENS
    )
    try:
        decision = json.loads(response)
        return decision
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response as JSON: {response}")
        return {"should_reply": False, "reason": "解析错误", "reply_type": "none", "impression_update": {"user_id": user_id, "content": ""}}
