from nonebot import require
require("nonebot_plugin_datastore")
require("nonebot_plugin_userinfo")
from nonebot_plugin_datastore import PluginData
from .models import init_models
plugin_data = PluginData(__name__)
User, Group, GroupUser = init_models(plugin_data)
from . import user_info_service
