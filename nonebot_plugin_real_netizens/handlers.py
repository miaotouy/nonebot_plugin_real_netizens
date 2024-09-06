# handlers.py
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_txt2img import Txt2Img

from .character_manager import character_manager
from .config import plugin_config
from .group_config_manager import group_config_manager
from .memory_manager import memory_manager
from .message_processor import message_processor
from .resource_loader import (character_card_loader, preset_loader,
                              worldbook_loader)

# 列出可用预设
list_presets = on_command("预设列表", rule=to_me(),
                          permission=SUPERUSER, priority=5)


@list_presets.handle()
async def handle_list_presets(bot: Bot, event: GroupMessageEvent):
    presets = preset_loader.cache.keys()
    message = "可用的预设列表：\n" + "\n".join(presets)
    image = await Txt2Img.render(message)
    await list_presets.finish(MessageSegment.image(image))
# 切换预设
switch_preset = on_command(
    "切换预设", rule=to_me(), permission=SUPERUSER, priority=5)


@switch_preset.handle()
async def handle_switch_preset(bot: Bot, event: GroupMessageEvent):
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
async def handle_list_worldbooks(bot: Bot, event: GroupMessageEvent):
    worldbooks = worldbook_loader.cache.keys()
    message = "可用的世界书列表：\n" + "\n".join(worldbooks)
    image = await Txt2Img.render(message)
    await list_worldbooks.finish(MessageSegment.image(image))
# 启用世界书
enable_worldbook = on_command(
    "启用世界书", rule=to_me(), permission=SUPERUSER, priority=5)


@enable_worldbook.handle()
async def handle_enable_worldbook(bot: Bot, event: GroupMessageEvent):
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
async def handle_disable_worldbook(bot: Bot, event: GroupMessageEvent):
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
async def handle_set_character(bot: Bot, event: GroupMessageEvent):
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
async def handle_view_config(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    config = group_config_manager.get_group_config(group_id)
    message = f"当前群配置：\n预设：{config.preset_name}\n角色卡：{config.character_id}\n世界书：{', '.join(config.worldbook_names)}"
    image = await Txt2Img.render(message)
    await view_config.finish(MessageSegment.image(image))
# 清除印象
clear_impression = on_command(
    "清除印象", rule=to_me(), permission=SUPERUSER, priority=5)


@clear_impression.handle()
async def handle_clear_impression(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.get_user_id()
    character_id = group_config_manager.get_group_config(
        group_id).character_id
    await memory_manager.deactivate_impression(group_id, int(user_id), character_id)
    await clear_impression.finish("已清除该用户的印象")
# 恢复印象
restore_impression = on_command(
    "恢复印象", rule=to_me(), permission=SUPERUSER, priority=5)


@restore_impression.handle()
async def handle_restore_impression(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.get_user_id()
    character_id = group_config_manager.get_group_config(
        group_id).character_id
    await memory_manager.reactivate_impression(group_id, int(user_id), character_id)
    await restore_impression.finish("已恢复该用户的印象")
# 查看印象
view_impression = on_command(
    "查看印象", rule=to_me(), permission=SUPERUSER, priority=5)


@view_impression.handle()
async def handle_view_impression(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.get_user_id()
    character_id = group_config_manager.get_group_config(
        group_id).character_id
    impression = await memory_manager.get_impression(group_id, int(user_id), character_id)
    if impression:
        message = f"用户 {user_id} 的印象：\n{impression}"
    else:
        message = f"未找到用户 {user_id} 的印象"
    image = await Txt2Img.render(message)
    await view_impression.finish(MessageSegment.image(image))
# 手动更新印象
update_impression = on_command(
    "更新印象", rule=to_me(), permission=SUPERUSER, priority=5)


@update_impression.handle()
async def handle_update_impression(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split(maxsplit=1)
    if len(args) != 2:
        await update_impression.finish("使用方法：更新印象 <印象内容>")
    group_id = event.group_id
    user_id = event.get_user_id()
    character_id = group_config_manager.get_group_config(
        group_id).character_id
    new_impression = args[1]
    await memory_manager.update_impression(group_id, int(user_id), character_id, new_impression)
    await update_impression.finish("已更新用户印象")
