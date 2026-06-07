# YUJI 工作室

这里是 YUJI 的本地公司工作台，用来沉淀 Agent、Skill、内容运营、产品洞察、同步规则和每日产物。

## 基础文档

- [YUJI 公司与品牌基础介绍](./company-profile.md)：记录品牌定位、愿景、小红书主页设定、内容方向和当前边界。
- [小红书发布内容库](./xhs-notes/README.md)：沉淀草稿、待发布、已发布和复盘反馈。
- [YUJI 研究项目](./research/README.md)：沉淀每周情绪价值研究会、全球社区观察和跨 Agent 讨论结论。

## 固定角色

- [运营总监](./agents/xiaohongshu-operator.md)：把真实情绪转成 YUJI 风格小红书内容，负责选题、标题、封面、正文、互动和发布复盘。
- [用户研究专家](./agents/user-researcher.md)：从全球社区采集真实表达，分析羽毛球人的情绪本质和消费动机。
- [产品总监](./agents/product-manager.md)：把用户情绪和外部观察转成低成本可验证 MVP。
- [秘书](./agents/secretary.md)：在每轮对话后做复盘收口，整理决策、待办、潜力想法、流程优化、定时任务候选和文件沉淀。

## 对话唤醒规则

当 CEO 在对话中直接提到“运营总监”“产品总监”“用户研究专家”或“秘书”时，默认读取对应角色职责并进入该角色视角。若 CEO 要求三方一起讨论，则由 Codex 同时汇总运营总监、产品总监和用户研究专家三方判断，最后给出 CEO 可执行的结论。若 CEO 说“复盘一下”“收一下尾”“整理一下待办”，默认唤醒秘书。

## 每周二研究会

YUJI 每周二进行一次“羽毛球情绪价值雷达”研究会，CEO 参与最终判断。开会前必须完成当周研究调研，会议只讨论判断和落地动作。

研究会使用：

- [羽毛球情绪价值雷达](./research/badminton-emotion-value-radar.md)
- [每周情绪价值研究会模板](./research/weekly-template.md)

每次研究会结束后，把可复用结果分别写入素材库、选题池和产品信号池。

会前节奏：

- 周三至周日：用户研究专家持续采集真实表达。
- 周一 22:00 前：完成本周研究会预读材料。
- 周二会前：运营总监和产品总监完成各自落地判断。
- 周二会议：CEO 参与讨论，确定下周主内容情绪、产品信号和继续观察问题。

## 每日同步规则

- 本地是实时工作区，飞书和 GitHub 是每日远端镜像。
- 每天 20:00（Asia/Shanghai）增量同步当天变动到现有 YUJI 知识库。
- 同一时间同步到 GitHub 仓库：`https://github.com/xiaoruDoctor/YUJI`
- 飞书同步和 GitHub 同步彼此独立；无论飞书同步是否成功，都必须继续执行 GitHub 同步。
- 同步目标知识库根节点：`羽毛球需求`
- 知识库根节点 token：`GSh5wwHU6iA6YqkbX4IcDATSnbh`
- 知识库空间 ID：`7507296694975905820`
- 同步形态：飞书在线文档。

## 本地文件范围

默认同步 `docs/**/*.md` 中的正式文档，不同步：

- 同步映射表和同步报告
- 临时文件、缓存、二维码、构建产物
- 命令输出或草稿性中间文件

同步总控脚本位于：[scripts/sync_daily.py](../../scripts/sync_daily.py)。

单项同步脚本：

- 飞书：[scripts/sync_feishu.py](../../scripts/sync_feishu.py)
- GitHub：[scripts/sync_github.py](../../scripts/sync_github.py)
