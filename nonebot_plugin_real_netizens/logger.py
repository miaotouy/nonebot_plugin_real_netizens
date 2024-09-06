# logger.py
import os
from typing import Optional

from nonebot import get_driver
from nonebot.log import logger as nonebot_logger

from .config import Config

plugin_config = Config.parse_obj(get_driver().config)
class PluginLogger:
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.logger = nonebot_logger.bind(plugin=plugin_name)
        # 如果配置了文件日志，则添加文件处理器
        if plugin_config.LOG_TO_FILE:
            self._setup_file_logging()
    def _setup_file_logging(self):
        log_dir = os.path.dirname(plugin_config.LOG_FILE_PATH)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.logger = self.logger.bind(
            sink=plugin_config.LOG_FILE_PATH,
            rotation=f"{plugin_config.LOG_FILE_MAX_SIZE} MB",
            retention=plugin_config.LOG_FILE_BACKUP_COUNT,
            compression="zip"
        )
    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)
    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)
    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)
    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)
    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)
    def exception(self, message: str, *args, exc_info: bool = True, **kwargs):
        self.logger.exception(message, *args, exc_info=exc_info, **kwargs)
def get_plugin_logger(name: Optional[str] = None) -> PluginLogger:
    return PluginLogger(name or "nonebot_plugin_real_netizens")
# 创建默认的插件日志器实例
logger = get_plugin_logger()
