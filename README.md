<div align="center">

  <a href="https://nonebot.dev/">
    <img src="https://nonebot.dev/logo.png" width="200" height="200" alt="nonebot">
  </a>

# nonebot_plugin_real_netizens


✨ [Nonebot2](https://github.com/nonebot/nonebot2) AI虚拟群友插件 ✨
<p align="center">
  <img src="https://img.shields.io/github/license/miaotouy/nonebot_plugin_real_netizens" alt="license">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/nonebot-2.3.0+-red.svg" alt="NoneBot">
</p>
</div>


## 简介
nonebot_plugin_real_netizens 是一个用于 Nonebot2 的插件，旨在创建足够拟人的AI群友，能够自然地在群聊中活动。
## 特性
- 基于大型语言模型的对话生成
- 支持多角色切换
- 群组配置管理
- 世界观和预设系统
- 定时任务（早安问候、冷场检测）
- 管理员命令支持
## 安装（可能还不行）
```bash
pip install nonebot_plugin_real_netizens
```
## 使用方法
1. 在 Nonebot2 项目的 `.env` 文件中添加以下配置：
```env
LLM_API_BASE=https://api.example.com #设置openai格式的调用地址，比如中转站
LLM_API_KEY=your-api-key
```
2. 在 `bot.py` 中添加插件：
```python
nonebot.load_plugin("nonebot_plugin_real_netizens")
```
## 配置项
在 `config/friend_config.yml` 中可以设置以下配置项：
- `LLM_MODEL`: 使用的语言模型名称
- `LLM_MAX_TOKENS`: 生成的最大token数
- `LLM_TEMPERATURE`: 生成的温度参数
- `TRIGGER_PROBABILITY`: AI主动发言的概率
- `TRIGGER_MESSAGE_INTERVAL`: 触发AI主动发言的消息间隔数
- `CONTEXT_MESSAGE_COUNT`: 群聊消息上下文条数上限
## 命令
- `角色列表`: 显示所有可用角色
- `切换角色 <角色ID>`: 切换当前群聊的AI角色
- `查看配置`: 查看当前群聊的配置信息
## 开发计划
- [x] 最初的构想
- [ ] 跑起来
- [ ] 完善错误处理和日志记录
- [ ] 实现更多管理员命令
- [ ] 优化LLM调用逻辑和性能
- [ ] 添加单元测试
- [ ] 实现多模态支持（图片处理）
- [ ] 完善文档和注释
## 贡献
欢迎提交 Issue 或 Pull Request 来帮助改进这个项目！
## 许可证
本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。