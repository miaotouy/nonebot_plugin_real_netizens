# tests\test_llm_generator.py
import asyncio
import os
import sys
from dotenv import load_dotenv
# 将项目根目录添加到 sys.path 中，以便导入 nonebot_plugin_real_netizens 模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)
from nonebot.log import logger
from nonebot_plugin_real_netizens.llm_generator import llm_generator
# 加载 .env 文件中的环境变量
load_dotenv()
# 使用 logger.add() 方法设置日志级别和处理器
logger.add(
    sys.stderr,  # 输出到标准错误流
    level="DEBUG",  # 设置日志级别为 DEBUG
    format="{time} {level} {message}",  # 设置日志格式
    filter="nonebot_plugin_real_netizens"  # 只记录 nonebot_plugin_real_netizens 模块的日志
)
async def test_llm_generator():
    """测试 llm_generator 模块的功能"""
    # 从环境变量中获取 LLM_API_BASE 和 LLM_API_KEY
    llm_api_base = os.getenv("LLM_API_BASE")
    llm_api_key = os.getenv("LLM_API_KEY")
    # 初始化 llm_generator，并传入 LLM_API_BASE 和 LLM_API_KEY
    llm_generator.url = llm_api_base # type: ignore
    llm_generator.key = llm_api_key # type: ignore
    llm_generator.initialized = True
    # 构造测试消息
    messages = [
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "你好，世界！"}
    ]
    # 调用 generate_response 函数生成响应
    response = await llm_generator.generate_response(
        messages=messages,
        model="gemini-1.5-flash-8b-exp-0827",  # 使用您配置的模型
        temperature=0.7,
        max_tokens=100
    )
    # 打印响应内容
    logger.debug(f"LLM response: {response}")
    print(f"LLM response: {response}")
    # 断言响应不为空
    assert response is not None
if __name__ == "__main__":
    asyncio.run(test_llm_generator())
