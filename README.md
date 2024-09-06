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

## 管理员命令列表 (仅在测试群聊中可用)
以下命令仅供管理员在特定的测试群聊中使用,用于配置和管理AI虚拟群友:
### 配置命令
- `预设列表`: 显示所有可用的预设。
- `切换预设 <预设名称> <目标群号>`: 为指定群聊切换预设。
- `世界书列表`: 显示所有可用的世界书。
- `启用世界书 <世界书名称> <目标群号>`: 为指定群聊启用世界书。
- `禁用世界书 <世界书名称> <目标群号>`: 为指定群聊禁用世界书。
- `设置角色卡 <角色名称> <目标群号>`: 为指定群聊设置AI角色。
- `查看配置 <目标群号>`: 查看指定群聊的当前配置信息。
### 印象管理命令
- `清除印象 <用户QQ> <目标群号>`: 清除指定用户在指定群聊中对当前角色的印象。
- `恢复印象 <用户QQ> <目标群号>`: 恢复指定用户在指定群聊中之前被清除的印象。
- `查看印象 <用户QQ> <目标群号>`: 查看指定用户在指定群聊中对当前角色的印象。
- `更新印象 <用户QQ> <目标群号> <印象内容>`: 手动更新指定用户在指定群聊中对当前角色的印象。
### 其他命令
- `角色列表`: 显示所有可用的角色卡。
## 使用说明
1. 所有管理命令仅在指定的测试群聊中可用,需要管理员权限。
2. 在实际运行的目标群聊中,AI虚拟群友会自动根据配置运行,不接受任何命令。
3. 配置更改后会立即生效,影响AI在目标群聊中的行为。
4. 印象管理会影响AI对特定用户的记忆和反应,请谨慎使用。
5. 建议在测试群中充分调试和优化配置,然后再在目标群中启用AI虚拟群友。
6. 如遇任何问题,请查看日志文件或联系开发者。
## 配置示例
以下是在测试群中为目标群配置AI虚拟群友的示例流程:
1. 查看可用角色卡: `/角色列表`
2. 为目标群设置角色: `/设置角色卡 nolll 123456789`
3. 查看可用预设: `/预设列表`
4. 为目标群选择预设: `/切换预设 预设示例 123456789`
5. 为目标群启用世界书: `/启用世界书 世界书条目示例 123456789`
6. 查看目标群当前配置: `/查看配置 123456789`
完成以上步骤后,AI虚拟群友将在目标群(123456789)中根据配置自动运行,无需额外命令。

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