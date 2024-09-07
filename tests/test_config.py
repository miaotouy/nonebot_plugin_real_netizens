# tests\test_config.py
import os

import pytest
from nonebot import get_driver

from nonebot_plugin_real_netizens.config import Config, get_plugin_config


@pytest.fixture(scope="function")
def clean_config():
    original_config = get_driver().config.dict()
    yield
    get_driver().config = Config.parse_obj(original_config)


def test_default_config(app, clean_config):
    config = get_plugin_config()
    assert config.LLM_MODEL == "gemini-1.5-pro-exp-0827"
    assert config.LLM_MAX_TOKENS == 4096
    assert config.LLM_TEMPERATURE == 0.9
    assert config.TRIGGER_PROBABILITY == 0.6


def test_config_load(app, clean_config):
    config = Config.parse_obj({})
    assert config.LLM_MODEL == "gemini-1.5-pro-exp-0827"
    assert config.LLM_MAX_TOKENS == 4096


def test_config_override(app, clean_config):
    test_config = {
        "LLM_MODEL": "test-model",
        "LLM_MAX_TOKENS": 2048,
        "LLM_TEMPERATURE": 0.7,
    }
    get_driver().config.update(test_config)
    config = get_plugin_config()
    assert config.LLM_MODEL == "test-model"
    assert config.LLM_MAX_TOKENS == 2048
    assert config.LLM_TEMPERATURE == 0.7
    assert config.TRIGGER_PROBABILITY == 0.6


def test_env_override(app, clean_config, monkeypatch):
    # 使用环境变量中的值，如果不存在则使用默认值
    test_api_key = os.getenv("TEST_LLM_API_KEY", "default_test_api_key")
    test_api_base = os.getenv(
        "TEST_LLM_API_BASE", "https://default.test.api.com")
    monkeypatch.setenv("LLM_API_KEY", test_api_key)
    monkeypatch.setenv("LLM_API_BASE", test_api_base)
    config = get_plugin_config()
    assert config.LLM_API_KEY == test_api_key
    assert config.LLM_API_BASE == test_api_base


def test_invalid_config(app, clean_config):
    with pytest.raises(ValueError):
        Config.parse_obj({"LLM_TEMPERATURE": 1.5})  # 超出有效范围
    with pytest.raises(ValueError):
        Config.parse_obj({"TRIGGER_PROBABILITY": -0.1})  # 小于0
