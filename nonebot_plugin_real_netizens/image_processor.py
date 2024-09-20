# nonebot_plugin_real_netizens\image_processor.py
import asyncio
import base64
import json
import os
from io import BytesIO
from typing import Dict, Optional, Tuple
import imagehash
from PIL import Image
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger
from .config import Config
from .db.models import Image as DBImage  # 避免与 PIL.Image 冲突
from .llm_generator import llm_generator


class ImageProcessor:
    def __init__(self, config: Config):
        # 获取插件的配置对象
        self.config = config

        # 使用插件的配置项初始化属性
        self.max_retries = self.config.MAX_RETRIES
        self.retry_delay = self.config.RETRY_INTERVAL
        self.max_size = self.config.MAX_IMAGE_SIZE
        self.vl_llm_model = self.config.VL_LLM_MODEL
        self.supported_formats = ['JPEG', 'PNG', 'GIF', 'WEBP', 'BMP']

    async def process_image(self, image_path: str, image_hash: str) -> Tuple[bool, Dict]:
        try:
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                logger.error(f"Failed to preprocess image {image_path}")
                return False, self._build_error_image_info(image_path, image_hash, "图片预处理失败")
            image_description = await self.generate_image_description(processed_image)
            if image_description is None or 'error' in image_description:
                logger.error(
                    f"Failed to generate image description for {image_path}: {image_description.get('error')}"
                )
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
                    background.paste(img, mask=img.split()[
                                     3] if img.mode == 'RGBA' else None)
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
        try:
            image_base64 = await self.encode_image_to_base64(image)
            system_message = (
                "请详细描述这张图片。\n"
                "然后判断它是否是表情包,如果是表情包,请给出一个或多个情绪标签。\n"
                "使用json格式输出:\n"
                "{\n"
                '  "description": {"type": "string"},\n'
                '  "is_meme": {"type": "boolean"},\n'
                '  "emotion_tag": {"type": "string", "nullable": true}\n'
                "}"
            )

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{system_message}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                }
            ]

            for attempt in range(self.max_retries):
                try:
                    response = await llm_generator.generate_response(
                        messages=messages,
                        model=self.vl_llm_model,
                        temperature=0.7,
                        max_tokens=150,
                    )

                    if response is None:
                        error_msg = f"Attempt {attempt + 1} failed: API returned None."
                        logger.error(error_msg)
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        else:
                            return self._build_error_response(error_msg, None)
                    
                    # 尝试提取 JSON 对象
                    try:
                        first_brace_index = response.find("{")
                        last_brace_index = response.rfind("}")
                        if first_brace_index != -1 and last_brace_index != -1:
                            json_string = response[first_brace_index : last_brace_index + 1]
                            description_data = json.loads(json_string)

                            if not all(
                                key in description_data for key in ["description", "is_meme"]
                            ):  # 只检查必要字段
                                raise KeyError("Missing required fields in JSON response")
                            return description_data
                        else:
                            raise ValueError("No valid JSON object found in response")
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        error_msg = f"Attempt {attempt + 1} failed: JSON decode error or missing fields: {e}. Response: {response}"
                        logger.error(error_msg)
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        else:
                            return self._build_error_response(error_msg, 200)


                except RuntimeError as e:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        logger.error(
                            f"All attempts to generate image description failed. Last error: {e}"
                        )
                        return self._build_error_response(str(e), None)
        except Exception as e:
            logger.error(f"Error in generate_image_description: {e}")
            return self._build_error_response(str(e), None)
        return self._build_error_response(
            "All attempts to generate image description failed.", None
        )

    async def encode_image_to_base64(self, image: Image.Image) -> str:
        buffered = BytesIO()
        image = image.convert("RGB")
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def _build_error_response(self, error_msg: str, status_code: Optional[int]) -> Dict:
        return {
            'description': "生成图片描述失败",
            'is_meme': False,
            'emotion_tag': None,
            'error': error_msg,
            'status_code': status_code
        }


# 创建一个全局实例,使用依赖注入
plugin_config = Config.parse_obj(get_driver().config)
image_processor = ImageProcessor(plugin_config)
