import pytest
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebug import App


@pytest.mark.asyncio
async def test_process_message(app: App, group_message_event: GroupMessageEvent):
    from nonebot_plugin_real_netizens.message_processor import MessageProcessor
    processor = MessageProcessor()
    context = {"user": "test_user", "char": "test_char"}

    # 使用一个更复杂的消息内容来测试
    group_message_event.message = Message(
        "Hello, world! [CQ:image,file=test.jpg]")

    result = await processor.process_message(group_message_event, [], context)
    assert result is not None
    assert isinstance(result, str)
    assert "Hello, world!" in result


@pytest.mark.asyncio
async def test_process_message_content(app: App):
    from nonebot_plugin_real_netizens.message_processor import MessageProcessor
    processor = MessageProcessor()

    # 测试纯文本消息
    message = Message("Hello, world!")
    full_content, image_descriptions = await processor.process_message_content(message)
    assert full_content == "Hello, world!"
    assert image_descriptions == []
    # 测试包含图片的消息
    message_with_image = Message("Check this out! [CQ:image,file=test.jpg]")
    full_content, image_descriptions = await processor.process_message_content(message_with_image)
    assert "Check this out!" in full_content
    assert len(image_descriptions) == 1


@pytest.mark.asyncio
async def test_process_message_with_empty_content(app: App, group_message_event: GroupMessageEvent):
    from nonebot_plugin_real_netizens.message_processor import MessageProcessor
    processor = MessageProcessor()
    context = {"user": "test_user", "char": "test_char"}

    # 测试空消息
    group_message_event.message = Message("")

    result = await processor.process_message(group_message_event, [], context)
    assert result is not None
    assert isinstance(result, str)
    assert result.strip() == ""  # 期望处理空消息时返回空字符串
