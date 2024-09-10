#tests/test_image_processor.py
import asyncio
import os
from typing import Dict
import pytest
from PIL import Image
from nonebot_plugin_real_netizens.image_processor import ImageProcessor
from nonebot_plugin_real_netizens.config import Config
# 测试图片路径
TEST_GIF_PATH = os.path.join(os.path.dirname(__file__), "giftest.gif")
TEST_JPG_PATH = os.path.join(os.path.dirname(__file__), "jpgtest.jpg")
TEST_PNG_PATH = os.path.join(os.path.dirname(__file__), "pngtest.png")
# 模拟配置
TEST_CONFIG = Config(
    IMAGE_SAVE_PATH="tests/test_images",
    MAX_RETRIES=3,
    RETRY_INTERVAL=1.0,
    FAST_LLM_MODEL="gemini-1.5-flash-exp-0827",
)
@pytest.mark.asyncio
async def test_process_image():
    image_processor = ImageProcessor(TEST_CONFIG)
    # 测试 GIF 图片
    success, gif_info = await image_processor.process_image(TEST_GIF_PATH, "test_gif_hash")
    assert success is True
    assert isinstance(gif_info, Dict)
    assert gif_info["file_path"] == TEST_GIF_PATH
    assert gif_info["description"] is not None
    # 测试 JPG 图片
    success, jpg_info = await image_processor.process_image(TEST_JPG_PATH, "test_jpg_hash")
    assert success is True
    assert isinstance(jpg_info, Dict)
    assert jpg_info["file_path"] == TEST_JPG_PATH
    assert jpg_info["description"] is not None
    # 测试 PNG 图片
    success, png_info = await image_processor.process_image(TEST_PNG_PATH, "test_png_hash")
    assert success is True
    assert isinstance(png_info, Dict)
    assert png_info["file_path"] == TEST_PNG_PATH
    assert png_info["description"] is not None
@pytest.mark.asyncio
async def test_preprocess_image():
    image_processor = ImageProcessor(TEST_CONFIG)
    # 测试 GIF 预处理
    gif_image = await asyncio.to_thread(image_processor.preprocess_image, TEST_GIF_PATH)
    assert gif_image is not None
    assert gif_image.format == "JPEG"
    # 测试 JPG 预处理
    jpg_image = await asyncio.to_thread(image_processor.preprocess_image, TEST_JPG_PATH)
    assert jpg_image is not None
    assert jpg_image.format == "JPEG"
    # 测试 PNG 预处理
    png_image = await asyncio.to_thread(image_processor.preprocess_image, TEST_PNG_PATH)
    assert png_image is not None
    assert png_image.format == "JPEG"
