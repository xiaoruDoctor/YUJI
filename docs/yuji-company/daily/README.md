# YUJI 每日产物归档

这里存放 YUJI 工作室每天的运营和产品经理产物。

命名建议：

- `YYYY-MM-DD-0900.md`：当天主小红书待审核笔记 + 产品洞察 + 昨日羽毛球热点检查
- `YYYY-MM-DD-1800.md`：补充观察 + 次日方向

这些文件会在每天 20:00（北京时间 / Asia/Shanghai）由同步自动化统一同步到 GitHub。

## 与运营素材库的关系

每日归档负责保存“当天完整产物”，运营素材库负责保存“可复用资产”。

每次 09:00 或 18:00 自动化运行后，应从日报中提取：

- 已使用素材：写入或更新 `docs/yuji-company/content-library/materials.md`，状态标为 `已用于笔记`。
- 未使用素材：写入 `docs/yuji-company/content-library/materials.md`，状态标为 `未使用` 或 `待验证`。
- 未发布选题：写入 `docs/yuji-company/content-library/topics.md`。
- 产品苗头：写入 `docs/yuji-company/content-library/product-signals.md`。

## 早间热点栏规则

`YYYY-MM-DD-0900.md` 必须包含一栏 `昨日羽毛球热点检查`。

- 有适合 YUJI 的热点：写 1-3 条，每条包含事件事实、来源链接、热度来源说明、是否适合 YUJI、可转成的小红书标题。
- 没有适合热点：明确写 `昨日暂无适合 YUJI 蹭的羽毛球热点`。
- 不要为了完成栏目硬凑赛事资讯、纯比分、装备参数、训练技巧或争议撕扯。
- 热点只有在能转成普通球友的情绪、记忆、身份感、球搭子关系或羽迹卡产品信号时，才进入选题池。

日报不需要承担长期检索功能；后续找素材、找灵感、找产品信号时，优先查 `content-library/`。
