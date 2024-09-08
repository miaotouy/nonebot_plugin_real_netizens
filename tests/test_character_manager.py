# tests\test_character_manager.py
import asyncio
import pytest
from nonebug import App
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot_plugin_real_netizens.character_manager import CharacterManager
from nonebot_plugin_real_netizens.group_config_manager import group_config_manager
# 将 fixture 作用域更改为 "session"
@pytest.fixture(scope="session")
async def character_manager():
    # 创建 CharacterManager 实例
    manager = CharacterManager()
    # 加载角色数据
    await manager.load_characters()
    return manager
@pytest.mark.asyncio
async def test_get_character_info(app: App, character_manager: CharacterManager, mocker, bot: Bot, event:Event):
    # 模拟 group_config_manager
    mock_group_config = mocker.patch.object(group_config_manager, "get_group_config")
    mock_group_config.return_value.character_id = "test_character"
    # 使用 mocker 模拟 character_card_loader 的行为
    mock_character_card_loader = mocker.patch(
        "nonebot_plugin_real_netizens.character_manager.character_card_loader"
    )
    mock_character_card_loader.get_resource.return_value = (
        {"name": "Test Character", "description": "This is a test character"},
        ["test_worldbook"],
    )
    # 使用 mocker 模拟 worldbook_loader 的行为
    mock_worldbook_loader = mocker.patch(
        "nonebot_plugin_real_netizens.character_manager.worldbook_loader"
    )
    mock_worldbook_loader.get_resource.return_value = [
        {"content": "Test worldbook content"}
    ]
    # 调用 load_characters() 方法
    await character_manager.load_characters()
    # 获取角色信息
    character_info = character_manager.get_character_info(123)
    # 断言
    assert character_info is not None
    assert isinstance(character_info, dict)
    assert character_info["name"] == "Test Character"
    # 测试获取特定键
    name = character_manager.get_character_info(123, "name")
    assert name == "Test Character"
    # 测试获取不存在的键
    non_existent = character_manager.get_character_info(123, "non_existent")
    assert non_existent is None


@pytest.mark.asyncio
async def test_load_character(app: App, character_manager, mocker):
    # 模拟 character_card_loader
    mock_loader = mocker.patch(
        'nonebot_plugin_real_netizens.character_manager.character_card_loader')
    mock_loader.get_resource.return_value = (
        {
            "name": "Test Character",
            "description": "This is a test character"
        },
        ["test_worldbook"]
    )
    # 模拟 worldbook_loader
    mock_worldbook_loader = mocker.patch(
        'nonebot_plugin_real_netizens.character_manager.worldbook_loader')
    mock_worldbook_loader.get_resource.return_value = [
        {"content": "Test worldbook content"}]
    await character_manager.load_character("test_character")
    assert "test_character" in character_manager.character_cards
    assert character_manager.character_cards["test_character"]["name"] == "Test Character"
    assert "test_worldbook" in character_manager.worldbooks


@pytest.mark.asyncio
async def test_load_character_error(app: App, character_manager, mocker):
    # 模拟 character_card_loader 抛出异常
    mock_loader = mocker.patch(
        'nonebot_plugin_real_netizens.character_manager.character_card_loader')
    mock_loader.get_resource.side_effect = Exception("Test exception")
    # 模拟 logger
    mock_logger = mocker.patch(
        'nonebot_plugin_real_netizens.character_manager.logger')
    await character_manager.load_character("test_character")
    assert "test_character" not in character_manager.character_cards
    mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_character_worldbooks(app: App, character_manager):
    character_manager.character_cards = {
        "test_character": {
            "worldbooks": ["test_worldbook1", "test_worldbook2"]
        }
    }
    character_manager.worldbooks = {
        "test_worldbook1": [{"content": "Worldbook 1 content"}],
        "test_worldbook2": [{"content": "Worldbook 2 content"}]
    }
    worldbooks = character_manager.get_character_worldbooks("test_character")
    assert len(worldbooks) == 2
    assert worldbooks[0]["content"] == "Worldbook 1 content"
    assert worldbooks[1]["content"] == "Worldbook 2 content"


@pytest.mark.asyncio
async def test_on_config_change(app: App, character_manager):
    character_manager.character_cache[123] = {"name": "Cached Character"}
    character_manager.on_config_change(123)
    assert 123 not in character_manager.character_cache

@pytest.mark.asyncio
async def test_on_config_change(app: App, character_manager: CharacterManager, mocker):
    # 模拟群组配置变化
    group_id = 123
    new_character_id = "new_character"
    mock_group_config = mocker.patch.object(group_config_manager, "get_group_config")
    mock_group_config.return_value.character_id = new_character_id
    # 预先设置缓存
    character_manager.character_cache[group_id] = {"name": "Old Character"}
    # 调用 on_config_change() 方法
    character_manager.on_config_change(group_id)
    # 断言缓存已被清除
    assert group_id not in character_manager.character_cache