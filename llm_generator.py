# llm_generator.py
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from nonebot import get_driver

from .config import Config

logger = logging.getLogger(__name__)

global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)


class LLMGenerator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMGenerator, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def init(self):
        self.url = plugin_config.LLM_API_BASE
        self.key = plugin_config.LLM_API_KEY
        self.proxy = plugin_config.LLM_PROXY_SERVER
        self.initialized = True

    async def generate_response(self, messages: List[Dict[str, str]], model: str,
                                temperature: float, max_tokens: int,
                                **kwargs) -> Optional[str]:
        if not self.initialized:
            logger.error("LLMGenerator not initialized")
            return None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        # 如果是 Gemini 系列模型，添加安全设置
        if "gemini" in model.lower():
            payload["safety_settings"] = [
                {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.url}/v1/chat/completions",
                                        headers=headers,
                                        json=payload,
                                        proxy=self.proxy) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return self.process_response(data)
        except aiohttp.ClientError as e:
            logger.error(f"API request error: {e}")
            return None

    def process_response(self, data: Dict[str, Any]) -> Optional[str]:
        if data and 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        else:
            logger.warning("No valid content in API response")
            return None


# 创建一个全局实例
llm_generator = LLMGenerator()
