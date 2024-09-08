# nonebot_plugin_real_netizens\admin_commands.py
from nonebot import require, on_command


from typing import List

from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_txt2img import Txt2Img

from .character_manager import character_manager
from .group_config_manager import group_config_manager
from nonebot.log import logger
from .memory_manager import memory_manager

# 定义所有管理命令
admin_commands = {
    "预设列表": on_command("预设列表", permission=SUPERUSER, priority=5),
    "切换预设": on_command("切换预设", permission=SUPERUSER, priority=5),
    "世界书列表": on_command("世界书列表", permission=SUPERUSER, priority=5),
    "启用世界书": on_command("启用世界书", permission=SUPERUSER, priority=5),
    "禁用世界书": on_command("禁用世界书", permission=SUPERUSER, priority=5),
    "设置角色卡": on_command("设置角色卡", permission=SUPERUSER, priority=5),
    "查看配置": on_command("查看配置", permission=SUPERUSER, priority=5),
    "清除印象": on_command("清除印象", permission=SUPERUSER, priority=5),
    "恢复印象": on_command("恢复印象", permission=SUPERUSER, priority=5),
    "查看印象": on_command("查看印象", permission=SUPERUSER, priority=5),
    "更新印象": on_command("更新印象", permission=SUPERUSER, priority=5),
}
# 通用的参数检查函数


def check_args(args: List[str], expected_length: int, usage: str) -> bool:
    if len(args) != expected_length:
        raise ValueError(f"参数数量不正确。使用方法：{usage}")
    return True
# 处理函数


async def handle_list_presets(bot: Bot, event: GroupMessageEvent):
    presets = character_manager.get_preset_list()
    message = "可用的预设列表：\n" + "\n".join(presets)
    return message


async def handle_switch_preset(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 3, "切换预设 <目标群号> <预设名称>")
    group_id, preset_name = int(args[1]), args[2]
    if await group_config_manager.set_preset(group_id, preset_name):
        return f"成功为群 {group_id} 切换到预设：{preset_name}"
    else:
        return f"切换预设失败，请检查群号和预设名称是否正确"


async def handle_list_worldbooks(bot: Bot, event: GroupMessageEvent):
    worldbooks = character_manager.get_worldbook_list()
    message = "可用的世界书列表：\n" + "\n".join(worldbooks)
    return message


async def handle_enable_worldbook(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 3, "启用世界书 <目标群号> <世界书名称>")
    group_id, worldbook_name = int(args[1]), args[2]
    if await group_config_manager.enable_worldbook(group_id, worldbook_name):
        return f"成功为群 {group_id} 启用世界书：{worldbook_name}"
    else:
        return f"启用世界书失败，请检查群号和世界书名称是否正确"


async def handle_disable_worldbook(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 3, "禁用世界书 <目标群号> <世界书名称>")
    group_id, worldbook_name = int(args[1]), args[2]
    if await group_config_manager.disable_worldbook(group_id, worldbook_name):
        return f"成功为群 {group_id} 禁用世界书：{worldbook_name}"
    else:
        return f"禁用世界书失败，请检查群号和世界书名称是否正确"


async def handle_set_character(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 3, "设置角色卡 <目标群号> <角色名称>")
    group_id, character_name = int(args[1]), args[2]
    if await group_config_manager.set_character(group_id, character_name):
        return f"成功为群 {group_id} 设置角色卡：{character_name}"
    else:
        return f"设置角色卡失败，请检查群号和角色名称是否正确"


async def handle_view_config(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 2, "查看配置 <目标群号>")
    group_id = int(args[1])
    config = group_config_manager.get_group_config(group_id)
    message = f"群 {group_id} 配置：\n预设：{config.preset_name}\n角色卡：{config.character_id}\n世界书：{', '.join(config.worldbook_names)}"
    image = await Txt2Img.render(message)
    return MessageSegment.image(image)


async def handle_clear_impression(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 4, "清除印象 <目标群号> <用户QQ> <角色ID>")
    group_id, user_id, character_id = int(args[1]), int(args[2]), args[3]
    await memory_manager.deactivate_impression(group_id, user_id, character_id)
    return f"已清除群 {group_id} 中用户 {user_id} 对角色 {character_id} 的印象"


async def handle_restore_impression(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 4, "恢复印象 <目标群号> <用户QQ> <角色ID>")
    group_id, user_id, character_id = int(args[1]), int(args[2]), args[3]
    await memory_manager.reactivate_impression(group_id, user_id, character_id)
    return f"已恢复群 {group_id} 中用户 {user_id} 对角色 {character_id} 的印象"


async def handle_view_impression(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split()
    check_args(args, 4, "查看印象 <目标群号> <用户QQ> <角色ID>")
    group_id, user_id, character_id = int(args[1]), int(args[2]), args[3]
    impression = await memory_manager.get_impression(group_id, user_id, character_id)
    if impression:
        message = f"群 {group_id} 中角色 {character_id} 对用户 {user_id} 的印象：\n{impression}"
    else:
        message = f"未找到群 {group_id} 中角色 {character_id} 对用户 {user_id} 的印象"
    image = await Txt2Img.render(message)
    return MessageSegment.image(image)


async def handle_update_impression(bot: Bot, event: GroupMessageEvent):
    args = str(event.get_message()).strip().split(maxsplit=4)
    check_args(args, 5, "更新印象 <目标群号> <用户QQ> <角色ID> <印象内容>")
    group_id, user_id, character_id, new_impression = int(
        args[1]), int(args[2]), args[3], args[4]
    await memory_manager.update_impression(group_id, user_id, character_id, new_impression)
    return f"已更新群 {group_id} 中用户 {user_id} 对角色 {character_id} 的印象"
# 主要的命令处理函数


async def handle_admin_command(bot: Bot, event: GroupMessageEvent, args: list):
    command = args[0]
    try:
        if command == "预设列表":
            return await handle_list_presets(bot, event)
        elif command == "切换预设":
            return await handle_switch_preset(bot, event)
        elif command == "世界书列表":
            return await handle_list_worldbooks(bot, event)
        elif command == "启用世界书":
            return await handle_enable_worldbook(bot, event)
        elif command == "禁用世界书":
            return await handle_disable_worldbook(bot, event)
        elif command == "设置角色卡":
            return await handle_set_character(bot, event)
        elif command == "查看配置":
            return await handle_view_config(bot, event)
        elif command == "清除印象":
            return await handle_clear_impression(bot, event)
        elif command == "恢复印象":
            return await handle_restore_impression(bot, event)
        elif command == "查看印象":
            return await handle_view_impression(bot, event)
        elif command == "更新印象":
            return await handle_update_impression(bot, event)
        else:
            return f"未知的命令：{command}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error(f"处理命令 {command} 时发生错误: {str(e)}")
        return f"处理命令时发生错误，请检查日志"
# 为每个命令注册处理函数
for cmd, matcher in admin_commands.items():
    @matcher.handle()
    async def _(bot: Bot, event: GroupMessageEvent, matcher=matcher):
        result = await handle_admin_command(bot, event, str(event.get_message()).strip().split())
        await matcher.finish(result)
