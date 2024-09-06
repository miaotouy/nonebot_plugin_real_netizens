import pytest
from nonebug import App

from nonebot_plugin_real_netizens.message_builder import MessageBuilder


@pytest.mark.asyncio
async def test_decide_behavior(app: App):
    from nonebot_plugin_real_netizens.behavior_decider import decide_behavior
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
