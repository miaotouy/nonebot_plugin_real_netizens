# tests\conftest.py
import os
import sys
import pytest
from nonebot import get_driver, load_plugins
from nonebot.adapters.onebot.v11 import Bot, Event, Adapter as OneBotV11Adapter
from nonebot.drivers.fastapi import Driver
from nonebug import App
# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
@pytest.fixture(scope="session")
async def app() -> App:
    # 加载 NoneBot 插件
    load_plugins("src/plugins")
    # 初始化 NoneBug App
    app = App()
    driver = get_driver()
    # 注册适配器
    driver.register_adapter(OneBotV11Adapter)
    # 返回 NoneBug App 实例
    return app

# 其他 fixture 和测试辅助函数
@pytest.fixture
def bot(app: App):
    return Bot(app=app, self_id="test")

@pytest.fixture
def event():
    return Event()

# 添加一个模拟的群消息事件
@pytest.fixture
def group_message_event(bot: Bot):
    from nonebot.adapters.onebot.v11 import GroupMessageEvent
    return GroupMessageEvent(
        time=1000000,
        self_id=bot.self_id,
        post_type="message",
        sub_type="normal",
        user_id=10000,
        message_type="group",
        group_id=10000,
        message_id=1,
        message="test message",
        raw_message="test message",
        font=1,
        sender={"user_id": 10000, "nickname": "test_user"},
    )

# 添加一个用于生成测试图片的 fixture
@pytest.fixture
async def mock_image():
    from nonebot_plugin_txt2img import Txt2Img
    txt2img = Txt2Img()
    image_bytes = await txt2img.draw("Test Image")
    return f"base64://{image_bytes.getvalue().decode()}"
