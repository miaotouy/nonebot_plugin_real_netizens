import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_get_character_info(app: App):
    from nonebot_plugin_real_netizens.character_manager import CharacterManager
    character_manager = CharacterManager()
    character_info = character_manager.get_character_info(123, "name")
    assert character_info is not None
    assert isinstance(character_info, str)


@pytest.mark.asyncio
async def test_load_character(app: App):
    from nonebot_plugin_real_netizens.character_manager import CharacterManager
    character_manager = CharacterManager()
    await character_manager.load_character("test_character")
    assert "test_character" in character_manager.character_cards
