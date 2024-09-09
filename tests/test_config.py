import os
from pathlib import Path
import pytest
from nonebot import get_driver
from nonebot_plugin_real_netizens.config import Config

plugin_config: Config  # 全局变量，存储插件配置
def get_plugin_config() -> Config:
    """获取插件配置。"""
    global plugin_config
    plugin_config = Config.parse_obj(get_driver().config.dict()) # 每次调用都重新解析配置
    return plugin_config

@pytest.fixture(scope="function")
def clean_config():
    """清除 NoneBot 配置，避免测试用例之间相互干扰。"""
    original_config = get_driver().config.dict()
    yield
    get_driver().config = Config.parse_obj(original_config)
@pytest.fixture(scope="function")
def clean_env():
    """清除环境变量，避免测试用例之间相互干扰。"""
    original_env = os.environ.copy()
    yield
    os.environ = original_env
def test_default_config(app, clean_config):
    """测试默认配置是否正确加载。"""
    config = get_plugin_config()
    assert config.LLM_MODEL == "gemini-1.5-pro-exp-0827"
    assert config.LLM_MAX_TOKENS == 4096
    assert config.LLM_TEMPERATURE == 0.7
    assert config.TRIGGER_PROBABILITY == 0.5
def test_config_load(app, clean_config):
    """测试仅使用默认值初始化配置。"""
    config = Config.parse_obj({})
    assert config.LLM_MODEL == "gemini-1.5-pro-exp-0827"
    assert config.LLM_MAX_TOKENS == 4096
def test_config_override(app, clean_config):
    """测试使用 NoneBot 配置覆盖默认配置。"""
    test_config = {
        "LLM_MODEL": "test-model",
        "LLM_MAX_TOKENS": 2048,
        "LLM_TEMPERATURE": 0.7,
    }
    get_driver().config = Config.parse_obj(
        {**get_driver().config.dict(), **test_config}
    )
    # 重新加载插件配置
    global plugin_config
    plugin_config = Config.from_yaml()
    config = get_plugin_config()
    assert config.LLM_MODEL == "test-model"
    assert config.LLM_MAX_TOKENS == 2048
    assert config.LLM_TEMPERATURE == 0.7
    assert config.TRIGGER_PROBABILITY == 0.5

@pytest.mark.asyncio
async def test_env_override(app, clean_config, clean_env):
    """测试使用环境变量覆盖默认配置，并使用 llm_generator 获取响应。"""
    # 检查环境变量是否存在，如果不存在则跳过测试
    if "LLM_API_KEY" not in os.environ or "LLM_API_BASE" not in os.environ:
        pytest.skip("LLM_API_KEY or LLM_API_BASE not found in environment variables")
    os.environ["FAST_LLM_MODEL"] = "gemini-1.5-flash-8b-exp-0827"
    global plugin_config
    plugin_config = Config.from_yaml()
    config = get_plugin_config()
    from nonebot_plugin_real_netizens.llm_generator import llm_generator
    llm_generator.init()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]
    response = await llm_generator.generate_response(
        messages=messages,
        model=config.FAST_LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
    )
    assert response == "Paris"
def test_invalid_config(app, clean_config):
    """测试无效配置是否引发 ValueError。"""
    with pytest.raises(ValueError):
        Config.parse_obj({"LLM_TEMPERATURE": 2.5})
    with pytest.raises(ValueError):
        Config.parse_obj({"TRIGGER_PROBABILITY": -0.1})
