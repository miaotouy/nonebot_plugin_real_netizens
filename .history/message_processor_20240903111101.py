from typing import List, Dict
from nonebot import get_driver
from .config import Config
from .llm_generator import llm_generator
plugin_config = Config.parse_obj(get_driver().config)
async def process_message(event, recent_messages: List[Dict]):
    # 获取消息内容
    message_content = event.get_plaintext()
    # 添加消息到上下文
    recent_messages.append({"role": "user", "content": message_content})
    if len(recent_messages) > plugin_config.CONTEXT_MESSAGE_COUNT:
        recent_messages.pop(0)
    # 构建 LLM 消息列表
    messages = [
        {"role": "system", "content": f"你是一个性格鲜明、爱好广泛的虚拟群友，拥有以下性格特点和兴趣：{plugin_config.CHARACTER_CONFIG}。请你尽量表现得像一个真实的网友，不要提及你是AI或者语言模型等信息。与用户聊天互动时，请根据用户的发言内容和你的性格特点以及兴趣爱好进行回复，并尽量使你的回复更具个性化和趣味性，可以使用一些新潮的网络流行语、表情图片等。"},
        *recent_messages
    ]
    # 调用 LLM 生成回复
    response = await llm_generator.generate_response(
        messages=messages,
        model=plugin_config.LLM_MODEL,
        temperature=plugin_config.LLM_TEMPERATURE,
        max_tokens=plugin_config.LLM_MAX_TOKENS
    )
    return response, recent_messages
