# YUJI 工作室

这里是 YUJI 的本地公司工作台，用来沉淀 Agent、Skill、内容运营、产品洞察、同步规则和每日产物。

## 基础文档

- [YUJI 公司与品牌基础介绍](./company-profile.md)：记录品牌定位、愿景、小红书主页设定、内容方向和当前边界。
- [小红书发布内容库](./xhs-notes/README.md)：沉淀草稿、待发布、已发布和复盘反馈。

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
