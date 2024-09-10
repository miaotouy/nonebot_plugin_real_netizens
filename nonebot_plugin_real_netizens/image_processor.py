import asyncio
import base64
import json
import os
from io import BytesIO
from typing import Dict, Optional, Tuple
import imagehash  # type: ignore
from PIL import Image
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger
from .config import Config
from .db.models import Image as DBImage  # 避免与 PIL.Image 冲突
from .llm_generator import llm_generator

# 依赖注入，避免直接访问全局配置对象
class ImageProcessor:
    def __init__(self, config: Config):
        self.image_save_path = config.IMAGE_SAVE_PATH
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_INTERVAL  # 使用RETRY_INTERVAL作为重试间隔
        self.max_size = 512
        self.fast_llm_model = config.FAST_LLM_MODEL
        self.supported_formats = ['JPEG', 'PNG', 'GIF', 'WEBP', 'BMP']  # 支持的图片格式

    async def process_image(self, image_path: str, image_hash: str) -> Tuple[bool, Dict]:
        try:
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                logger.error(f"Failed to preprocess image {image_path}")
                return False, self._build_error_image_info(image_path, image_hash, "图片预处理失败")
            
            image_description = await self.generate_image_description(processed_image)
            if image_description is None:
                logger.error(f"Failed to generate image description for {image_path}")
                return False, self._build_error_image_info(image_path, image_hash, "图片描述生成失败")

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
            return False, self._build_error_image_info(image_path, image_hash, "图片处理失败，无法生成描述")

    def _build_error_image_info(self, image_path: str, image_hash: str, error_message: str) -> Dict:
        return {
            'file_path': image_path,
            'file_name': os.path.basename(image_path) if image_path else None,
            'hash': image_hash,
            'description': error_message,
            'is_meme': False,
            'emotion_tag': None
        }

    def preprocess_image(self, image_path: str) -> Optional[Image.Image]:
        try:
            with Image.open(image_path) as img:
                if img.format not in self.supported_formats:
                    logger.warning(f"Unsupported image format: {img.format}")
                    return None

                if img.format == 'GIF':
                    img.seek(0)

                if img.width > self.max_size or img.height > self.max_size:
                    img.thumbnail((self.max_size, self.max_size))

                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode == 'P':  # 处理 PNG 图片的调色板模式
                    img = img.convert('RGB')

                jpeg_image = BytesIO()
                img.save(jpeg_image, format='JPEG')
                jpeg_image.seek(0)
                return Image.open(jpeg_image)
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return None

    def calculate_image_hash(self, image: Image.Image) -> str:
        image_hash = str(imagehash.phash(image))
        new_image = DBImage(hash=image_hash)  # 使用 DBImage 进行数据库操作
        new_image.save()
        return image_hash

    async def generate_image_description(self, image: Image.Image) -> Dict:
        buffered = BytesIO()
        image = image.convert("RGB")  # 将图片转换为 RGB 模式
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
                    model=self.fast_llm_model,  # 使用传入的模型配置
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


# 创建一个全局实例，使用依赖注入
plugin_config = Config.parse_obj(get_driver().config)
image_processor = ImageProcessor(plugin_config)
