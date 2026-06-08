# YUJI 每日产物归档

这里存放 YUJI 工作室每天的运营和产品经理产物。

命名建议：

- `YYYY-MM-DD-0900.md`：当天主小红书待审核笔记 + 产品洞察
- `YYYY-MM-DD-1800.md`：补充观察 + 次日方向

这些文件会在每天 20:00（北京时间 / Asia/Shanghai）由同步自动化统一同步到 GitHub。

## 与运营素材库的关系

每日归档负责保存“当天完整产物”，运营素材库负责保存“可复用资产”。

每次 09:00 或 18:00 自动化运行后，应从日报中提取：

- 已使用素材：写入或更新 `docs/yuji-company/content-library/materials.md`，状态标为 `已用于笔记`。
- 未使用素材：写入 `docs/yuji-company/content-library/materials.md`，状态标为 `未使用` 或 `待验证`。
- 未发布选题：写入 `docs/yuji-company/content-library/topics.md`。
- 产品苗头：写入 `docs/yuji-company/content-library/product-signals.md`。

日报不需要承担长期检索功能；后续找素材、找灵感、找产品信号时，优先查 `content-library/`。
