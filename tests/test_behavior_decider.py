# tests\test_behavior_decider.py
import pytest
from nonebug import App

from nonebot_plugin_real_netizens.behavior_decider import decide_behavior
from nonebot_plugin_real_netizens.config import Config
from nonebot_plugin_real_netizens.message_builder import MessageBuilder


@pytest.mark.asyncio
async def test_decide_behavior(app: App, mocker):
    # 模拟配置
    mocker.patch('nonebot_plugin_real_netizens.behavior_decider.plugin_config', Config(
        LLM_MODEL="test_model",
        LLM_TEMPERATURE=0.7,
        LLM_MAX_TOKENS=100,
        TRIGGER_PROBABILITY=0.5
    ))
    # 模拟LLM生成器
    mock_llm_generator = mocker.patch(
        'nonebot_plugin_real_netizens.behavior_decider.llm_generator')
    mock_llm_generator.generate_response.return_value = '{"should_reply": true, "reply_type": "text", "reason": "Test reason", "thoughts": "Test thoughts"}'
    # 模拟内存管理器
    mock_memory_manager = mocker.patch(
        'nonebot_plugin_real_netizens.behavior_decider.memory_manager')
    mock_memory_manager.get_impression.return_value = "Test impression"
    message = "Hello"
    recent_messages = [{"role": "user", "content": "Hi"}]
    message_builder = MessageBuilder(
        "test_preset", ["test_worldbook"], "test_character")
    user_id = 123
    group_id = 456
    result = await decide_behavior(message, recent_messages, message_builder, user_id, group_id)
    assert isinstance(result, dict)
    assert "should_reply" in result
    assert "reply_type" in result
    assert "reason" in result
    assert "thoughts" in result
    assert result["should_reply"] is True
    assert result["reply_type"] == "text"
    assert result["reason"] == "Test reason"
    assert result["thoughts"] == "Test thoughts"
    # 验证LLM生成器被正确调用
    mock_llm_generator.generate_response.assert_called_once()
    # 验证内存管理器被正确调用
    mock_memory_manager.get_impression.assert_called_once_with(
        group_id, user_id, "test_character")


@pytest.mark.asyncio
async def test_decide_behavior_error_handling(app: App, mocker):
    # 模拟LLM生成器抛出异常
    mock_llm_generator = mocker.patch(
        'nonebot_plugin_real_netizens.behavior_decider.llm_generator')
    mock_llm_generator.generate_response.side_effect = Exception(
        "Test exception")
    message = "Hello"
    recent_messages = [{"role": "user", "content": "Hi"}]
    message_builder = MessageBuilder(
        "test_preset", ["test_worldbook"], "test_character")
    user_id = 123
    group_id = 456
    result = await decide_behavior(message, recent_messages, message_builder, user_id, group_id)
    assert isinstance(result, dict)
    assert result["should_reply"] is False
    assert result["reason"] == "解析错误"
    assert result["reply_type"] == "none"
