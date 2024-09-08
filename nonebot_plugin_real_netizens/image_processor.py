import asyncio
import base64
import json
import os
from io import BytesIO
from typing import Dict, Optional, Tuple

import imagehash  # type: ignore
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image

from .config import Config
from .db.database import add_image_record, get_image_by_hash
from .llm_generator import llm_generator
from nonebot.log import logger

plugin_config = Config.parse_obj(get_driver().config)



class ImageProcessor:
    def __init__(self):
        self.image_save_path = plugin_config.IMAGE_SAVE_PATH
        self.max_retries = plugin_config.MAX_RETRIES
        self.retry_delay = plugin_config.RETRY_DELAY
        self.max_size = 512

    async def process_image(self, image_path: str, image_hash: str) -> Tuple[bool, Dict]:
        try:
            # 预处理图片
            processed_image = self.preprocess_image(image_path)
            # 生成图片描述
            image_description = await self.generate_image_description(processed_image)

            # 如果生成图片描述失败，记录错误并返回包含错误信息的 image_info
            if image_description is None:
                logger.error(f"Failed to generate image description for {image_path}")
                return False, {
                    'file_path': image_path,  # 保留文件路径
                    'file_name': os.path.basename(image_path),  # 保留文件名
                    'hash': image_hash,
                    'description': "图片描述生成失败",
                    'is_meme': False,
                    'emotion_tag': None
                }

            image_info = {
                'file_path': image_path,
                'file_name': os.path.basename(image_path),
                'hash': image_hash,
                'description': image_description['description'],
                'is_meme': image_description['is_meme'],
                'emotion_tag': image_description.get('emotion_tag')
            }
            return True, image_info
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return False, {
                'file_path': None,
                'file_name': None,
                'hash': image_hash,
                'description': "图片处理失败，无法生成描述",
                'is_meme': False,
                'emotion_tag': None
            }


    def preprocess_image(self, image_path: str) -> Image.Image:
        """预处理图片：调整大小和处理GIF"""
        with Image.open(image_path) as img:
            # 如果是GIF，只取第一帧
            if img.format == 'GIF':
                img.seek(0)
            # 调整大小
            if img.width > self.max_size or img.height > self.max_size:
                img.thumbnail((self.max_size, self.max_size))
            # 转换为RGB模式（去除透明通道）
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[
                                 3] if img.mode == 'RGBA' else None)
                img = background
            # 将图片保存为JPEG格式
            jpeg_image = BytesIO()
            img.save(jpeg_image, format='JPEG')
            # 从BytesIO对象中重新打开图片，以JPEG格式返回
            jpeg_image.seek(0)
            return Image.open(jpeg_image)

    def calculate_image_hash(self, image: Image.Image) -> str:
        """计算图片的感知哈希值"""
        return str(imagehash.phash(image))

    async def generate_image_description(self, image: Image.Image) -> Dict:
        """使用多模态LLM生成图片描述"""
        # 将图片转换为base64编码
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        messages = [
            {"role": "system",
             "content": "请描述这张图片，判断它是否是表情包，如果是表情包，请给出一个情绪标签。输出格式为JSON，包含'description'(描述文本)、'is_meme'（布尔值）和'emotion_tag'（如果是表情包，则提供情绪标签，否则为null）字段。"},
            {"role": "user", "content": [
                {"type": "text", "text": "这是一张图片，请描述它。"},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"}
            ]}
        ]
        for attempt in range(self.max_retries):
            try:
                response = await llm_generator.generate_response(
                    messages=messages,
                    model=plugin_config.FAST_LLM_MODEL,
                    temperature=0.7,
                    max_tokens=150
                )
                description_data = json.loads(response)
                return {
                    'description': description_data['description'],
                    'is_meme': description_data['is_meme'],
                    'emotion_tag': description_data['emotion_tag'] if description_data['is_meme'] else None
                }
            except (json.JSONDecodeError, KeyError, Exception) as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(
                        "All attempts to generate image description failed")
                    return {
                        'description': "无法生成图片描述",
                        'is_meme': False,
                        'emotion_tag': None
                    }


# 创建一个全局实例
image_processor = ImageProcessor()
