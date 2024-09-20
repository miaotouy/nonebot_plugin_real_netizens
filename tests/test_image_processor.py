# tests/test_image_processor.py
import asyncio
import os
from typing import Dict
import pytest
from PIL import Image
from nonebot import get_driver
from nonebot_plugin_real_netizens.image_processor import ImageProcessor
from nonebot_plugin_real_netizens.config import Config  # 导入插件的 Config

# 测试图片路径，使用绝对路径
TEST_GIF_PATH = os.path.join(os.path.dirname(__file__), "giftest.gif")
TEST_JPG_PATH = os.path.join(os.path.dirname(__file__), "jpgtest.jpg")
TEST_PNG_PATH = os.path.join(os.path.dirname(__file__), "pngtest.png")

# 打印测试图片路径，使用 os.path.abspath() 获取绝对路径
print(f"TEST_GIF_PATH: {os.path.abspath(TEST_GIF_PATH)}")
print(f"TEST_JPG_PATH: {os.path.abspath(TEST_JPG_PATH)}")
print(f"TEST_PNG_PATH: {os.path.abspath(TEST_PNG_PATH)}")

# 获取插件的配置
config = Config()  # 实例化插件的 Config 对象
image_processor = ImageProcessor(config)


@pytest.mark.asyncio
async def test_process_image():

    # 测试 GIF 图片
    success, gif_info = await image_processor.process_image(TEST_GIF_PATH,
                                                            "test_gif_hash")
    assert success is True
    assert isinstance(gif_info, Dict)
    assert gif_info["file_path"] == TEST_GIF_PATH

    # 测试 JPG 图片
    success, jpg_info = await image_processor.process_image(TEST_JPG_PATH,
                                                            "test_jpg_hash")
    assert success is True
    assert isinstance(jpg_info, Dict)
    assert jpg_info["file_path"] == TEST_JPG_PATH

    # 测试 PNG 图片
    success, png_info = await image_processor.process_image(TEST_PNG_PATH,
                                                            "test_png_hash")
    assert success is True
    assert isinstance(png_info, Dict)
    assert png_info["file_path"] == TEST_PNG_PATH


@pytest.mark.asyncio
async def test_preprocess_image():

    # 测试 GIF 预处理
    gif_image = await asyncio.to_thread(image_processor.preprocess_image,
                                        TEST_GIF_PATH)
    assert gif_image is not None
    assert gif_image.format == "JPEG"

    # 测试 JPG 预处理
    jpg_image = await asyncio.to_thread(image_processor.preprocess_image,
                                        TEST_JPG_PATH)
    assert jpg_image is not None
    assert jpg_image.format == "JPEG"

    # 测试 PNG 预处理
    png_image = await asyncio.to_thread(image_processor.preprocess_image,
                                        TEST_PNG_PATH)
    assert png_image is not None
    assert png_image.format == "JPEG"


@pytest.mark.asyncio
async def test_generate_image_description():

    # 测试 GIF 描述生成
    with Image.open(TEST_GIF_PATH) as gif_image:
        gif_description = await image_processor.generate_image_description(
            gif_image)
    assert gif_description is not None
    assert isinstance(gif_description, dict)
    assert "description" in gif_description
    assert "is_meme" in gif_description
    assert "emotion_tag" in gif_description
    if gif_description["error"]:
        print(f"GIF 描述生成错误: {gif_description['error']}")
        print(f"状态码: {gif_description['status_code']}")
    else:
        print(f"GIF 描述: {gif_description}")

    # 测试 JPG 描述生成
    with Image.open(TEST_JPG_PATH) as jpg_image:
        jpg_description = await image_processor.generate_image_description(
            jpg_image)
    assert jpg_description is not None
    assert isinstance(jpg_description, dict)
    assert "description" in jpg_description
    assert "is_meme" in jpg_description
    assert "emotion_tag" in jpg_description
    if jpg_description["error"]:
        print(f"JPG 描述生成错误: {jpg_description['error']}")
        print(f"状态码: {jpg_description['status_code']}")
    else:
        print(f"JPG 描述: {jpg_description}")

    # 测试 PNG 描述生成
    with Image.open(TEST_PNG_PATH) as png_image:
        png_description = await image_processor.generate_image_description(
            png_image)
    assert png_description is not None
    assert isinstance(png_description, dict)
    assert "description" in png_description
    assert "is_meme" in png_description
    assert "emotion_tag" in png_description
    if png_description["error"]:
        print(f"PNG 描述生成错误: {png_description['error']}")
        print(f"状态码: {png_description['status_code']}")
    else:
        print(f"PNG 描述: {png_description}")
