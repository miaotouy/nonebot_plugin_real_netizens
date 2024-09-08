# tests\test_message_processor.py
import pytest
from nonebug import App
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
@pytest.fixture
def processor():
    from nonebot_plugin_real_netizens.message_processor import MessageProcessor
    return MessageProcessor()
@pytest.fixture
async def mock_image():
    from nonebot_plugin_txt2img import Txt2Img
    txt2img = Txt2Img()
    image_bytes = await txt2img.draw("Test Image")
    return f"base64://{image_bytes.getvalue().decode()}"
@pytest.mark.asyncio
async def test_process_message(app: App, group_message_event: GroupMessageEvent, processor, mocker, mock_image):
    # 模拟依赖
    mock_group_config = mocker.patch(
        "nonebot_plugin_real_netizens.message_processor.group_config_manager"
    )
    mock_group_config.get_group_config.return_value.preset_name = "test_preset"
    mock_group_config.get_group_config.return_value.worldbook_names = ["test_worldbook"]
    mock_group_config.get_group_config.return_value.character_id = "test_character"
    mock_llm_generator = mocker.patch(
        "nonebot_plugin_real_netizens.message_processor.llm_generator"
    )
    mock_llm_generator.generate_response.return_value = "Generated response"
    # 准备测试数据
    context = {"user": "test_user", "char": "test_char"}
    group_message_event.message = Message(
        f"Hello, world! [CQ:image,file={mock_image}]"
    )
    # 调用待测试函数
    result = await processor.process_message(
        group_message_event, [], context
    )
    # 断言
    assert result is not None
    assert isinstance(result, str)
    assert result == "Generated response"
    # 验证依赖函数被调用
    mock_llm_generator.generate_response.assert_called_once()
@pytest.mark.asyncio
async def test_process_message_content(app: App, processor, mock_image):
    # 测试纯文本消息
    message = Message("Hello, world!")
    full_content, image_descriptions = await processor.process_message_content(message)
    assert full_content == "Hello, world!"
    assert image_descriptions == []
    # 测试包含图片的消息
    message_with_image = Message(
        f"Check this out! [CQ:image,file={mock_image}]"
    )
    full_content, image_descriptions = await processor.process_message_content(
        message_with_image
    )
    assert "Check this out!" in full_content
    assert len(image_descriptions) == 1
    assert "Test Image" in image_descriptions[0]
@pytest.mark.asyncio
async def test_process_message_with_empty_content(
    app: App, group_message_event: GroupMessageEvent, processor, mocker
):
    # 模拟依赖
    mock_llm_generator = mocker.patch(
        "nonebot_plugin_real_netizens.message_processor.llm_generator"
    )
    mock_llm_generator.generate_response.return_value = ""
    # 准备测试数据
    context = {"user": "test_user", "char": "test_char"}
    group_message_event.message = Message("")
    # 调用待测试函数
    result = await processor.process_message(
        group_message_event, [], context
    )
    # 断言
    assert result is not None
    assert isinstance(result, str)
    assert result == ""
@pytest.mark.asyncio
async def test_download_and_process_image(app: App, processor, mocker):
    # 模拟 aiohttp.ClientSession
    mock_session = mocker.AsyncMock()
    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    mock_response.read.return_value = b"fake_image_data"
    mock_session.get.return_value.__aenter__.return_value = mock_response
    mocker.patch("aiohttp.ClientSession", return_value=mock_session)
    # 模拟 image_processor
    mock_image_processor = mocker.patch(
        "nonebot_plugin_real_netizens.message_processor.image_processor"
    )
    mock_image_processor.process_image.return_value = (
        True,
        {
            "description": "A test image",
            "is_meme": False,
            "emotion_tag": None,
        },
    )
    # 模拟 add_image_record
    mock_add_image_record = mocker.patch(
        "nonebot_plugin_real_netizens.message_processor.add_image_record"
    )
    # 调用待测试函数
    image_info = await processor.download_and_process_image(
        "http://test.com/image.jpg"
    )
    # 断言
    assert image_info is not None
    assert image_info["description"] == "A test image"
    assert image_info["is_meme"] is False
    assert image_info["emotion_tag"] is None
    # 验证依赖函数被调用
    mock_session.get.assert_called_once_with("http://test.com/image.jpg")
    mock_image_processor.process_image.assert_called_once()
    mock_add_image_record.assert_called_once()
@pytest.mark.asyncio
async def test_download_and_process_image_error(app: App, processor, mocker):
    # 模拟 aiohttp.ClientSession 抛出异常
    mock_session = mocker.AsyncMock()
    mock_session.get.side_effect = Exception("Network error")
    mocker.patch("aiohttp.ClientSession", return_value=mock_session)
    # 模拟 logger
    mock_logger = mocker.patch(
        "nonebot_plugin_real_netizens.message_processor.logger"
    )
    # 调用待测试函数
    image_info = await processor.download_and_process_image(
        "http://test.com/image.jpg"
    )
    # 断言
    assert image_info is None
    mock_logger.error.assert_called_once()

