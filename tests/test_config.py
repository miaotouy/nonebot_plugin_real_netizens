# tests\test_config.py
import os
import pytest
from nonebot import get_driver
from nonebot_plugin_real_netizens.config import Config
from ruamel.yaml import YAML


@pytest.fixture(scope="session")
def test_config_file(tmpdir_factory):
    """在 tests 目录下创建一个临时 YAML 配置文件，并写入默认配置"""
    config_dir = os.path.join(os.path.dirname(__file__), "test_config")
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, "test_friend_config.yml")
    config = Config()
    config.from_yaml(config_file)
    return config_file


def test_config_write_to_yaml(test_config_file):
    """测试将配置写入 YAML 文件"""
    new_config = {
        "LLM_MODEL": "test_model",
        "TRIGGER_PROBABILITY": 0.5,
        "ENABLED_GROUPS": [123456789],
        "RES_PATH": os.path.dirname(test_config_file),
    }
    config = Config.from_yaml(test_config_file, new_config=new_config)

    # 重新加载配置
    loaded_config = Config.from_yaml(test_config_file)

    # 断言加载的配置与写入的配置一致
    assert loaded_config.LLM_MODEL == "test_model"
    assert loaded_config.TRIGGER_PROBABILITY == 0.5
    assert loaded_config.ENABLED_GROUPS == [123456789]


def test_config_load_and_write_unchanged(test_config_file):
    """测试加载并写入配置后，非 API 配置项保持不变"""
    # 加载已存在的配置文件
    initial_config = Config.from_yaml(test_config_file)

    # 修改一些配置项
    modified_config = {
        "LLM_MODEL": "initial_model",
        "TRIGGER_PROBABILITY": 0.5,
        "ENABLED_GROUPS": [111654111],
        "SUPERUSERS": [112168711],
        "DEFAULT_CHARACTER_ID": "114514",
    }
    config = Config.from_yaml(test_config_file, new_config=modified_config)

    # 再次加载配置
    loaded_config = Config.from_yaml(test_config_file)

    # 比较初始配置和再次写入后的配置（排除 API 密钥）
    for key in modified_config:
        if key not in ["LLM_API_KEY", "LLM_API_BASE"]:
            assert getattr(config, key) == getattr(loaded_config, key)


def test_invalid_config():
    """测试无效配置是否引发 ValueError。"""
    with pytest.raises(ValueError):
        Config.parse_obj({"LLM_TEMPERATURE": 2.5})  # 超出范围
    with pytest.raises(ValueError):
        Config.parse_obj({"TRIGGER_PROBABILITY": -0.1})  # 超出范围


