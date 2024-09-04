from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .character_manager import character_manager
from .config import plugin_config
from .group_config_manager import group_config_manager

# 列出可用预设
list_presets = on_command("预设列表", rule=to_me(),
                          permission=SUPERUSER, priority=5)


@list_presets.handle()
async def handle_list_presets(bot: Bot, event: Event):
    presets = character_manager.get_preset_list()
    message = "可用的预设列表：\n" + "\n".join(presets)
    await list_presets.finish(message)
# 切换预设
switch_preset = on_command(
    "切换预设", rule=to_me(), permission=SUPERUSER, priority=5)


@switch_preset.handle()
async def handle_switch_preset(bot: Bot, event: Event):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await switch_preset.finish("使用方法：切换预设 <预设名称>")

    preset_name = args[1]
    group_id = event.group_id
    if await group_config_manager.set_preset(group_id, preset_name):
        await switch_preset.finish(f"成功切换到预设：{preset_name}")
    else:
        await switch_preset.finish(f"切换预设失败，请检查预设名称是否正确")
# 列出世界书
list_worldbooks = on_command(
    "世界书列表", rule=to_me(), permission=SUPERUSER, priority=5)


@list_worldbooks.handle()
async def handle_list_worldbooks(bot: Bot, event: Event):
    worldbooks = character_manager.get_worldbook_list()
    message = "可用的世界书列表：\n" + "\n".join(worldbooks)
    await list_worldbooks.finish(message)
# 启用世界书
enable_worldbook = on_command(
    "启用世界书", rule=to_me(), permission=SUPERUSER, priority=5)


@enable_worldbook.handle()
async def handle_enable_worldbook(bot: Bot, event: Event):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await enable_worldbook.finish("使用方法：启用世界书 <世界书名称>")

    worldbook_name = args[1]
    group_id = event.group_id
    if await group_config_manager.enable_worldbook(group_id, worldbook_name):
        await enable_worldbook.finish(f"成功启用世界书：{worldbook_name}")
    else:
        await enable_worldbook.finish(f"启用世界书失败，请检查世界书名称是否正确")
# 禁用世界书
disable_worldbook = on_command(
    "禁用世界书", rule=to_me(), permission=SUPERUSER, priority=5)


@disable_worldbook.handle()
async def handle_disable_worldbook(bot: Bot, event: Event):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await disable_worldbook.finish("使用方法：禁用世界书 <世界书名称>")

    worldbook_name = args[1]
    group_id = event.group_id
    if await group_config_manager.disable_worldbook(group_id, worldbook_name):
        await disable_worldbook.finish(f"成功禁用世界书：{worldbook_name}")
    else:
        await disable_worldbook.finish(f"禁用世界书失败，请检查世界书名称是否正确")
# 设置角色卡
set_character = on_command("设置角色卡", rule=to_me(),
                           permission=SUPERUSER, priority=5)


@set_character.handle()
async def handle_set_character(bot: Bot, event: Event):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await set_character.finish("使用方法：设置角色卡 <角色名称>")

    character_name = args[1]
    group_id = event.group_id
    if await group_config_manager.set_character(group_id, character_name):
        await set_character.finish(f"成功设置角色卡：{character_name}")
    else:
        await set_character.finish(f"设置角色卡失败，请检查角色名称是否正确")
# 查看当前配置
view_config = on_command("查看配置", rule=to_me(),
                         permission=SUPERUSER, priority=5)


@view_config.handle()
async def handle_view_config(bot: Bot, event: Event):
    group_id = event.group_id
    config = await group_config_manager.get_group_config(group_id)
    message = f"当前群配置：\n预设：{config.preset_path}\n角色卡：{config.character_id}\n世界书：{', '.join(config.world_info_paths)}"
    await view_config.finish(message)
