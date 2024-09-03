from nonebot import require
require("nonebot_plugin_datastore")
require("nonebot_plugin_userinfo")
from nonebot_plugin_datastore import PluginData
plugin_data = PluginData(__name__)
from .db.models import init_models
User, Group, GroupUser = init_models(plugin_data)
from .db import database, user_info_service
