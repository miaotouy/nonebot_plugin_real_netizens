import time
from typing import Dict, Any, Optional
from nonebot import on_message, on_notice, get_driver, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupIncreaseNoticeEvent, MessageSegment
from nonebot.typing import T_State
from .config import Config
from .llm_generator import llm_generator
from .message_processor import process_message
from .trigger_manager import check_trigger
from .memory_manager import memory_manager
from .behavior_engine import decide_behavior
from .message_sender import send_message
from .group_config_manager import group_config_manager, GroupConfig
from .message_builder import MessageBuilder
from .character_manager import CharacterManager
from typing import List, Dict, Any, Optional

# 获取 logger 对象
import logging
logger = logging.getLogger(__name__)
# 加载配置
global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
# 初始化组件
character_manager = CharacterManager(character_cards_dir=plugin_config.character_cards_dir)
llm_generator.init()
# 模型选择函数
async def use_fast_model(messages: List[Dict[str, str]]) -> Optional[str]:
    return await llm_generator.generate_response(
        messages=messages,
        model=plugin_config.LLM_MODEL_FAST,
        temperature=plugin_config.LLM_TEMPERATURE,
        max_tokens=plugin_config.LLM_MAX_TOKENS_FAST
    )
async def use_pro_model(messages: List[Dict[str, str]]) -> Optional[str]:
    return await llm_generator.generate_response(
        messages=messages,
        model=plugin_config.LLM_MODEL_PRO,
        temperature=plugin_config.LLM_TEMPERATURE,
        max_tokens=plugin_config.LLM_MAX_TOKENS_PRO
    )
# 消息处理器
message_handler = on_message(priority=5)
@message_handler.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    group_config: GroupConfig = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return  # 如果没有配置角色，则不处理消息
    # 1. 消息接收与解析
    message = process_message(event)
    # 2. 触发机制检查
    if check_trigger(group_id, message, group_config):
        # 3. LLM 回复判断
        character_config: Optional[Dict[str, Any]] = character_manager.get_character_info(character_id, "extensions")
        chat_history = memory_manager.get_recent_messages(group_id, limit=5)
        if await should_respond(message, character_config, chat_history):
            # 4. 记忆检索
            memory = memory_manager.retrieve_memory(group_id, message)
            # 5. 行为决策
            behavior = decide_behavior(message, memory, character_config)
            # 6. LLM 调用与响应生成
            context = {"user": event.sender.nickname, "char": character_manager.get_character_info(character_id, "name")}
            builder = MessageBuilder(
                preset_file=group_config.preset_path,
                world_info_files=group_config.world_info_paths,
                character_cards_dir=plugin_config.character_cards_dir
            )
            messages = builder.build_message(character_id, context)
            response = await use_pro_model(messages)
            # 7. 消息发送
            await send_message(bot, event, response)
    # 8. 更新记忆
    memory_manager.update_memory(group_id, message)
async def should_respond(message: Dict, character_config: Optional[Dict], chat_history: List[str]) -> bool:
    prompt = f"""
    作为一个AI虚拟群友，你需要决定是否回复以下消息。请按照以下步骤进行思考：
    1. 信息感知：
       - 消息内容: {message['content']}
       - 发送者: {message['sender']}
       - 当前场景: 群聊
    2. 信息解读：
       - 根据你的性格特点（{character_config.get('personality', '无')}）和兴趣（{character_config.get('interests', '无')}），这条消息对你来说重要吗？
       - 这条消息与之前的对话（{chat_history[-3:] if chat_history else '无'}）有关联吗？
    3. 情绪反应：
       - 这条消息让你产生了什么情绪？（如：好奇、高兴、困惑、无聊）
    4. 目标管理：
       - 回复这条消息是否符合你当前的目标？（如：保持活跃、帮助他人、展示知识）
    5. 行动决策：
       - 考虑到以上因素，你认为应该回复这条消息吗？
    请根据以上思考过程，给出你的决定。只需回答 "YES" 或 "NO"。
    决定：
    """
    response = await use_fast_model([{"role": "user", "content": prompt}])
    return response.strip().upper() == "YES"
# 欢迎新成员
welcome_handler = on_notice(priority=5)
@welcome_handler.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = event.group_id
    group_config = group_config_manager.get_group_config(group_id)
    character_id = group_config.character_id
    if not character_id:
        return  # 如果没有配置角色，则不处理消息
    new_member = event.get_user_id()
    context = {"user": event.user_id, "char": character_manager.get_character_info(character_id, "name")}
    builder = MessageBuilder(
        preset_file=group_config.preset_path,
        world_info_files=group_config.world_info_paths,
        character_cards_dir=plugin_config.character_cards_dir
    )
    messages = builder.build_message(character_id, context)
    welcome_msg = await use_fast_model(messages)
    await send_message(bot, event, welcome_msg)
# 定时任务：每日问候
scheduler = require("nonebot_plugin_apscheduler").scheduler
@scheduler.scheduled_job("cron", hour=int(plugin_config.morning_greeting_hour), minute=int(plugin_config.morning_greeting_minute))
async def morning_greeting():
    bot = get_driver().bots.values()[0]  # 获取第一个机器人实例
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        if not character_id:
            continue
        context = {"user": "群友", "char": character_manager.get_character_info(character_id, "name")}
        builder = MessageBuilder(
            preset_file=group_config.preset_path,
            world_info_files=group_config.world_info_paths,
            character_cards_dir=plugin_config.character_cards_dir
        )
        messages = builder.build_message(character_id, context)
        greeting = await use_fast_model(messages)
        await send_message(bot, {"group_id": group_id}, greeting)
# 冷场检测和响应
@scheduler.scheduled_job("interval", minutes=int(plugin_config.inactive_check_interval))
async def check_inactive_chats():
    bot = get_driver().bots.values()[0]
    current_time = time.time()
    for group_id in group_config_manager.get_all_groups():
        group_config = group_config_manager.get_group_config(group_id)
        character_id = group_config.character_id
        if not character_id:
            continue
        last_message_time = memory_manager.get_last_message_time(group_id)
        if current_time - last_message_time > group_config.inactive_threshold:
            context = {"user": "群友", "char": character_manager.get_character_info(character_id, "name")}
            builder = MessageBuilder(
                preset_file=group_config.preset_path,
                world_info_files=group_config.world_info_paths,
                character_cards_dir=plugin_config.character_cards_dir
            )
            messages = builder.build_message(character_id, context)
            revival_msg = await use_fast_model(messages)
            await send_message(bot, {"group_id": group_id}, revival_msg)
# 其他功能和事件处理器可以在这里添加
