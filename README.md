# AstrBot 小林 Coding 学习推送

这是一个 AstrBot 插件，用于把小林 Coding 内容抓取到本地私有学习卡片题库，并通过 AstrBot 会话推送复习。

现有 `java-pusher/` 文件夹不会被改动，也不会被这个插件仓库跟踪。

## 命令

- `/xlin status` - 查看题库数量和定时推送状态
- `/xlin import` - 抓取小林 Coding 并刷新本地题库
- `/xlin next` - 推送下一张待复习卡片
- `/xlin topic <关键词>` - 按主题或关键词查找卡片
- `/xlin set <HH:MM>` - 为当前会话启用每日定时推送
- `/xlin cancel` - 关闭每日定时推送
- `/xlin rate <卡片ID> <不会|模糊|掌握>` - 记录复习结果并更新间隔，也兼容 `again|hard|good`

## 数据说明

完整抓取内容只会保存在 AstrBot 插件数据目录中，不会提交到 Git。仓库只跟踪插件代码、测试和少量说明文件。

## 开发验证

```bash
python -m pytest
ruff format .
ruff check .
```
