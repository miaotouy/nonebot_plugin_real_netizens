# tests\conftest.py
import os
import sys

import pytest
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.drivers.fastapi import Driver
from nonebug import App

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


@pytest.fixture(scope="session", autouse=True)
def init_nonebot():
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter

    # 设置测试用的配置
    nonebot.init(
        debug=True,
        datastore_database_url="sqlite:///:memory:",  # 使用内存数据库进行测试
        LLM_API_BASE="https://test.api.com",
        LLM_API_KEY="test_key",
        LLM_MODEL="gemini-1.5-flash-exp-0827",
        SUPERUSERS=["12345"],
        ENABLED_GROUPS=[67890],
    )
    app = App()
    app.register_adapter(Adapter)
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)
    # 初始化插件
    nonebot.load_plugin("nonebot_plugin_datastore")
    nonebot.load_plugin("nonebot_plugin_txt2img")
    nonebot.load_plugin("nonebot_plugin_real_netizens")
    yield app


@pytest.fixture
def app(init_nonebot):
    return init_nonebot


@pytest.fixture
def driver():
    return get_driver()


@pytest.fixture
def bot():
    return Bot("test", "test")


@pytest.fixture
def event():
    return Event()
# 添加一个模拟的群消息事件


@pytest.fixture
def group_message_event(bot):
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
        sender={'user_id': 10000, 'nickname': 'test_user'},
    )
# 添加一个用于生成测试图片的fixture


@pytest.fixture
async def mock_image():
    from nonebot_plugin_txt2img import Txt2Img
    txt2img = Txt2Img()
    image_bytes = await txt2img.draw("Test Image")
    return f"base64://{image_bytes.getvalue().decode()}"