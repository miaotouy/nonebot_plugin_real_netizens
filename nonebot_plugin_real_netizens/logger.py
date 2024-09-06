# logger.py
import logging

from nonebot import get_driver

from .config import Config

plugin_config = Config.parse_obj(get_driver().config)
def setup_logger():
    logger = logging.getLogger("nonebot_plugin_real_netizens")
    logger.setLevel(plugin_config.LOG_LEVEL)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 如果需要，也可以添加文件处理器
    # file_handler = logging.FileHandler("nonebot_plugin_real_netizens.log")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    return logger
logger = setup_logger()
