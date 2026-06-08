# YUJI Xiaoyu Character Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable Xiaoyu character asset system: reusable prompts, reference-image slots, quality checklist, and integration rules for YUJI Xiaohongshu and future video content.

**Architecture:** Keep Xiaoyu's identity rules in the existing character bible, then add a focused character asset package under `docs/yuji-company/visual-system/xiaoyu/`. The package has one source-of-truth prompt file, one asset index, one QA checklist, and one workflow note so future image/video work can reuse Xiaoyu consistently without turning YUJI into an AI/virtual-idol account.

**Tech Stack:** Markdown documentation, local image assets, existing YUJI content library, existing Xiaohongshu note workflow.

---

## File Structure

Create these files:

- `docs/yuji-company/visual-system/xiaoyu/README.md`  
  Role entry point for Xiaoyu: who she is, when to use her, when not to use her.

- `docs/yuji-company/visual-system/xiaoyu/prompts.md`  
  Reusable prompt templates for the six base reference images and future scene generation.

- `docs/yuji-company/visual-system/xiaoyu/assets-index.md`  
  Asset registry for Xiaoyu's base reference images, usage status, and QA notes.

- `docs/yuji-company/visual-system/xiaoyu/qa-checklist.md`  
  Visual acceptance checklist for face consistency, badminton court correctness, clothing boundaries, and brand fit.

- `docs/yuji-company/visual-system/xiaoyu/workflow.md`  
  Workflow for generating, reviewing, storing, and using Xiaoyu assets in Xiaohongshu notes and future videos.

Create this directory for generated assets:

- `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/`

Modify these existing files:

- `docs/yuji-company/skills/yuji-brand-voice.md`  
  Add Xiaoyu as a default visual member when a YUJI visual needs a person.

- `docs/yuji-company/skills/xhs-note-writer.md`  
  Add a check that Xiaohongshu image suggestions consider Xiaoyu when person-based visuals are appropriate.

No code changes are required.

---

## Task 1: Create Xiaoyu Visual System Entry Point

**Files:**
- Create: `docs/yuji-company/visual-system/xiaoyu/README.md`

- [ ] **Step 1: Create the directory**

Run:

```bash
mkdir -p docs/yuji-company/visual-system/xiaoyu/assets/base-reference
```

Expected: command exits `0`.

- [ ] **Step 2: Create `README.md`**

Write this exact content:

```markdown
# 小羽视觉角色系统

小羽是 YUJI 工作室的固定成员，是 YUJI 的虚拟女生球友，也是所有可出镜内容优先考虑的前台人物资产。

她不是一次性封面素材，不是虚拟偶像，不是 AI 美女，也不是运动穿搭博主。她的作用是把“羽毛球是情绪出口”“下班后还想打一局”“球馆接住了很多情绪”这些内容变成稳定、真实、可持续的视觉表达。

## 核心身份

- 名字：小羽
- 身份：YUJI 的女生球友
- 年龄感：25-30 岁
- 气质：安静、有点累，但眼神里还有一局
- 出镜定位：真实球馆纪录片 + 轻角色识别

## 默认调用规则

当 YUJI 内容需要人物出镜时，优先判断是否由小羽出现。

适合使用小羽：

- 小红书封面需要女生球友视角。
- 视频需要主角、旁观者、场边人物或第一视角承载者。
- 羽迹卡、Player ID、羽迹时刻需要示例人物。
- 内容主题是情绪出口、下班后去球馆、最后一局、场边休息、混双搭子关系。

不适合使用小羽：

- 内容更适合旧球、旧拍、手胶、空球馆等静物视觉。
- 内容来自真实用户故事，应该保留真实用户的匿名表达或授权素材。
- 小羽出现会让内容像角色美图，而不是羽毛球情绪内容。

## 内部判断句

> 这个位置如果可以有人出现，先想一遍：是不是应该让 YUJI 的女生球友小羽出现？

## 关联文档

- 角色圣经：`docs/superpowers/specs/2026-06-08-yuji-virtual-female-badminton-player-design.md`
- 提示词模板：`docs/yuji-company/visual-system/xiaoyu/prompts.md`
- 资产索引：`docs/yuji-company/visual-system/xiaoyu/assets-index.md`
- 质量检查：`docs/yuji-company/visual-system/xiaoyu/qa-checklist.md`
- 使用流程：`docs/yuji-company/visual-system/xiaoyu/workflow.md`
```

- [ ] **Step 3: Verify file content**

Run:

```bash
rg -n "小羽是 YUJI 工作室的固定成员|默认调用规则|这个位置如果可以有人出现" docs/yuji-company/visual-system/xiaoyu/README.md
```

Expected: all three phrases are found.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/yuji-company/visual-system/xiaoyu/README.md
git commit -m "Add Xiaoyu visual system entry point"
```

Expected: commit succeeds and includes only `README.md`.

---

## Task 2: Create Xiaoyu Prompt Templates

**Files:**
- Create: `docs/yuji-company/visual-system/xiaoyu/prompts.md`

- [ ] **Step 1: Create `prompts.md`**

Write this exact content:

````markdown
# 小羽生成提示词模板

本文件用于生成和复用小羽的图片与视频视觉。前台内容不讲 AI，不讲虚拟人技术；本文件只供内部制作使用。

## 固定角色描述

每次生成小羽时都必须保留以下角色描述：

```text
YUJI 的虚拟女生球友小羽，亚洲女生，25-30 岁，清晰正脸或清晰侧脸，五官稳定，黑色或深棕色长发，真实羽毛球运动生活方式气质。她安静、有点累，但眼神里还有一局。她不是网红，不是写真模特，不性感化，不浓妆，不甜美营业笑，像一个下班后仍然会去球馆打球的普通女生球友。
```

## 固定场地描述

每次生成羽毛球馆场景时都必须保留以下场地描述：

```text
真实羽毛球馆，常规羽毛球 PVC 地胶，低饱和墨绿、青绿色或蓝绿色地面，白色或黄色羽毛球场地线，球馆灯光，地胶有柔和反光，画面中可以有拍包、旧羽毛球、球桶、矿泉水、磨损球鞋和旧手胶。
```

## 固定禁用描述

每次生成时都必须加入以下禁用描述：

```text
不要篮球馆，不要木地板，不要排球馆，不要红色跑道，不要水泥地；不要网红写真，不要低胸，不要湿身感，不要刻意腿部特写，不要情侣暧昧，不要虚拟偶像感，不要夸张妆容，不要过度磨皮，不要 AI 科技感。
```

## 基础参考图 1：正脸基础图

用途：建立小羽的脸部记忆，后续所有图片和视频都以它作为核心参考。

```text
竖版 3:4 真实摄影风格，YUJI 的虚拟女生球友小羽，亚洲女生，25-30 岁，清晰正脸，五官稳定，黑色或深棕色长发，自然披发或低马尾，清淡耐看的脸，略有距离感的眼神，安静、有点累，但眼神里还有一局。她穿黑色或深灰运动 T 恤，站在真实羽毛球馆场边，背景是常规羽毛球 PVC 地胶，低饱和青绿色地面，白色羽毛球场地线，球馆灯光柔和，真实运动生活方式，不网红，不写真，不性感化，不浓妆，不甜美营业笑。

不要篮球馆，不要木地板，不要低胸，不要湿身感，不要刻意腿部特写，不要虚拟偶像感，不要 AI 科技感。
```

## 基础参考图 2：三分之二侧脸图

用途：小红书封面、情绪海报、场边叙事。

```text
竖版 3:4 真实摄影风格，小羽，YUJI 的虚拟女生球友，亚洲女生，25-30 岁，三分之二侧脸，脸部清晰，五官与正脸基础图一致，黑色或深棕色长发，安静、有点累，但眼神里还有一局。她坐在羽毛球馆场边长椅上，低头握着羽毛球拍，身边有黑色拍包和矿泉水，常规羽毛球 PVC 地胶，低饱和青绿色地面，白色场地线，球馆灯光和地胶柔和反光。真实球友纪录片感，不网红，不写真，不性感化。

不要篮球馆，不要木地板，不要低胸，不要湿身感，不要刻意腿部特写，不要情侣暧昧，不要虚拟偶像感。
```

## 基础参考图 3：侧脸图

用途：场边休息、下班后到球馆、视频转场。

```text
竖版 3:4 真实摄影风格，小羽，YUJI 的虚拟女生球友，亚洲女生，25-30 岁，清晰侧脸，五官与正脸基础图一致，黑色或深棕色长发扎低马尾。她站在羽毛球馆边线旁，肩上背着黑色拍包，刚到球馆还没有完全放下包，表情安静，像下班后来打球。真实羽毛球馆，常规羽毛球 PVC 地胶，低饱和墨绿或青绿色地面，白色场地线，球馆灯光明亮但克制。

不要网红摆拍，不要写真姿势，不要低胸，不要木地板，不要篮球馆，不要 AI 科技感。
```

## 基础参考图 4：背影图

用途：最后一局、离开球馆、安静情绪内容。

```text
竖版 3:4 真实摄影风格，小羽，YUJI 的虚拟女生球友，亚洲女生，25-30 岁，从背后拍摄，黑色或深棕色长发，穿黑色运动 T 恤和真实适合打羽毛球的运动短裤或训练裤，背着黑色拍包，站在羽毛球馆边线外，看向还亮着灯的球场。常规羽毛球 PVC 地胶，低饱和青绿色地面，白色场地线，地胶柔和反光，画面安静克制，像最后一局结束后还舍不得离开。

不要性感化背影，不要刻意腿部特写，不要木地板，不要篮球馆，不要虚拟偶像感。
```

## 基础参考图 5：半身场边图

用途：“羽毛球是情绪出口”系列首图。

```text
竖版 3:4 真实摄影风格，小羽，YUJI 的虚拟女生球友，亚洲女生，25-30 岁，半身画面，脸部清晰，五官与正脸基础图一致，黑色或深棕色长发，穿深色运动 T 恤。她坐在羽毛球馆场边，双手握着羽毛球拍手柄，低头发呆，像刚把呼吸缓下来。身边有旧羽毛球、球桶、黑色拍包和矿泉水。真实羽毛球馆，常规羽毛球 PVC 地胶，低饱和青绿色地面，白色场地线，球馆灯光柔和。

不要写真，不要网红妆，不要低胸，不要刻意腿部特写，不要情侣感，不要 AI 科技感。
```

## 基础参考图 6：全身球馆图

用途：视频延展、运动场景、品牌物料。

```text
竖版 3:4 真实摄影风格，小羽，YUJI 的虚拟女生球友，亚洲女生，25-30 岁，全身画面，脸部可辨认，五官与正脸基础图一致，黑色或深棕色长发扎低马尾，穿黑色或白色运动 T 恤、真实适合羽毛球运动的短裤或训练裤、白色羽毛球鞋。她站在羽毛球场边，右手拿羽毛球拍，姿态自然，不摆拍，像准备上场。真实羽毛球馆，常规羽毛球 PVC 地胶，低饱和墨绿或青绿色地面，白色场地线，灯光明亮，地胶柔和反光。

不要篮球馆，不要木地板，不要低胸，不要湿身感，不要刻意腿部特写，不要虚拟偶像感，不要 AI 科技感。
```

## 场景复用模板

把 `{场景}`、`{动作}`、`{情绪}`、`{画面用途}` 替换成具体需求：

```text
竖版 3:4 真实摄影风格，{画面用途}。YUJI 的虚拟女生球友小羽，亚洲女生，25-30 岁，脸部清晰，五官与小羽基础参考图一致，黑色或深棕色长发，真实羽毛球运动生活方式气质。她安静、有点累，但眼神里还有一局。场景是{场景}，她正在{动作}，画面情绪是{情绪}。真实羽毛球馆，常规羽毛球 PVC 地胶，低饱和墨绿、青绿色或蓝绿色地面，白色或黄色羽毛球场地线，球馆灯光，地胶柔和反光，可以出现拍包、旧羽毛球、球桶、矿泉水、磨损球鞋和旧手胶。

不要篮球馆，不要木地板，不要排球馆，不要红色跑道，不要水泥地；不要网红写真，不要低胸，不要湿身感，不要刻意腿部特写，不要情侣暧昧，不要虚拟偶像感，不要夸张妆容，不要过度磨皮，不要 AI 科技感。
```
````

- [ ] **Step 2: Verify required prompt sections**

Run:

```bash
rg -n "固定角色描述|基础参考图 1|基础参考图 6|场景复用模板|不要篮球馆" docs/yuji-company/visual-system/xiaoyu/prompts.md
```

Expected: all five phrases are found.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/yuji-company/visual-system/xiaoyu/prompts.md
git commit -m "Add Xiaoyu prompt templates"
```

Expected: commit succeeds and includes only `prompts.md`.

---

## Task 3: Create Xiaoyu Asset Index

**Files:**
- Create: `docs/yuji-company/visual-system/xiaoyu/assets-index.md`

- [ ] **Step 1: Create `assets-index.md`**

Write this exact content:

```markdown
# 小羽视觉资产索引

本索引用于记录小羽所有基础参考图、正式可用图、废弃图和后续视频素材。

## 资产状态

- `待生成`：还没有生成。
- `待审核`：已生成，等待检查脸部一致性、球馆正确性和品牌边界。
- `可用`：通过检查，可进入小红书、视频或品牌物料。
- `废弃`：不再使用，原因必须记录。

## 基础参考图

| 编号 | 资产名称 | 文件路径 | 状态 | 用途 | 审核备注 |
|-|-|-|-|-|-|
| XY-BASE-01 | 正脸基础图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg` | 待生成 | 建立脸部记忆 | 需要脸清晰、五官稳定、不过度精修 |
| XY-BASE-02 | 三分之二侧脸图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-02-three-quarter.jpg` | 待生成 | 小红书封面、情绪海报 | 需要和正脸像同一个人 |
| XY-BASE-03 | 侧脸图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-03-profile.jpg` | 待生成 | 场边休息、视频转场 | 需要发型和脸型稳定 |
| XY-BASE-04 | 背影图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-04-back.jpg` | 待生成 | 最后一局、离开球馆 | 不要性感化背影 |
| XY-BASE-05 | 半身场边图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-05-bench-halfbody.jpg` | 待生成 | 情绪出口系列首图 | 需要场边独处感 |
| XY-BASE-06 | 全身球馆图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-06-fullbody-court.jpg` | 待生成 | 视频延展、运动场景 | 服装必须适合真实打球 |

## 使用记录

| 日期 | 资产编号 | 使用位置 | 内容主题 | 数据或反馈 | 后续判断 |
|-|-|-|-|-|-|
```

- [ ] **Step 2: Verify all six base slots exist**

Run:

```bash
rg -n "XY-BASE-01|XY-BASE-02|XY-BASE-03|XY-BASE-04|XY-BASE-05|XY-BASE-06" docs/yuji-company/visual-system/xiaoyu/assets-index.md
```

Expected: all six IDs are found.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/yuji-company/visual-system/xiaoyu/assets-index.md docs/yuji-company/visual-system/xiaoyu/assets/base-reference
git commit -m "Add Xiaoyu asset index"
```

Expected: commit succeeds and includes `assets-index.md`. The empty asset directory may not appear in git until images are added; that is acceptable.

---

## Task 4: Create Xiaoyu QA Checklist

**Files:**
- Create: `docs/yuji-company/visual-system/xiaoyu/qa-checklist.md`

- [ ] **Step 1: Create `qa-checklist.md`**

Write this exact content:

````markdown
# 小羽视觉质量检查清单

每张小羽图片或视频截图进入正式内容前，必须按本清单检查。只要有一项严重失败，就不能使用。

## 1. 角色一致性

- [ ] 看起来是小羽，而不是另一个随机女生。
- [ ] 年龄感在 25-30 岁之间。
- [ ] 发色为黑色或深棕色。
- [ ] 脸部清晰时，五官与基础参考图一致。
- [ ] 表情符合“安静、有点累，但眼神里还有一局”。
- [ ] 没有网红精修感、浓妆、甜美营业笑或虚拟偶像感。

## 2. 羽毛球真实感

- [ ] 场地是常规羽毛球 PVC 地胶。
- [ ] 地胶为低饱和墨绿、青绿色或蓝绿色。
- [ ] 场地线是白色或黄色羽毛球线。
- [ ] 没有篮球馆、木地板、排球馆、红色跑道或水泥地。
- [ ] 球拍、拍包、球桶、旧球、手胶、球鞋等物件没有明显错误。

## 3. 身体与服装边界

- [ ] 服装适合真实打羽毛球。
- [ ] 没有低胸、湿身感、写真姿势或刻意腿部特写。
- [ ] 身体表达健康、真实、运动化，不把身材作为主卖点。
- [ ] 和搭子同框时没有情侣暧昧感。

## 4. YUJI 品牌 fit

- [ ] 画面服务一个羽毛球情绪，而不是单纯角色美图。
- [ ] 能联想到情绪出口、下班后去球馆、最后一局、场边休息或搭子关系。
- [ ] 不讲 AI，不出现 AI 科技感。
- [ ] 画面克制、真实、有球馆生活感。

## 5. 发布前结论

审核结论只能填写以下三种：

- `可用`：直接进入资产索引。
- `修改后再审`：记录需要重生成或修正的问题。
- `废弃`：记录废弃原因，不进入正式内容。

审核记录格式：

```markdown
### YYYY-MM-DD｜资产编号

- 审核结论：
- 主要问题：
- 可使用位置：
- 是否更新资产索引：
```
````

- [ ] **Step 2: Verify checklist coverage**

Run:

```bash
rg -n "角色一致性|羽毛球真实感|身体与服装边界|YUJI 品牌 fit|发布前结论" docs/yuji-company/visual-system/xiaoyu/qa-checklist.md
```

Expected: all five sections are found.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/yuji-company/visual-system/xiaoyu/qa-checklist.md
git commit -m "Add Xiaoyu visual QA checklist"
```

Expected: commit succeeds and includes only `qa-checklist.md`.

---

## Task 5: Create Xiaoyu Asset Workflow

**Files:**
- Create: `docs/yuji-company/visual-system/xiaoyu/workflow.md`

- [ ] **Step 1: Create `workflow.md`**

Write this exact content:

```markdown
# 小羽视觉资产工作流

本工作流用于从角色圣经出发，生成、审核、保存和使用小羽的图片与视频素材。

## 1. 生成前

1. 先判断内容是否适合小羽出现。
2. 如果适合，从 `prompts.md` 选择基础参考图提示词或场景复用模板。
3. 不删除固定角色描述、固定场地描述和固定禁用描述。
4. 只替换具体场景、动作、情绪和画面用途。

## 2. 生成首批基础参考图

按以下顺序生成：

1. `XY-BASE-01` 正脸基础图。
2. `XY-BASE-02` 三分之二侧脸图。
3. `XY-BASE-03` 侧脸图。
4. `XY-BASE-04` 背影图。
5. `XY-BASE-05` 半身场边图。
6. `XY-BASE-06` 全身球馆图。

正脸基础图通过审核后，再生成其他角度。其他角度必须参考正脸基础图，不能各生成各的。

## 3. 审核

每张图生成后，按 `qa-checklist.md` 检查。

通过审核后：

1. 将图片保存到 `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/`。
2. 按资产编号命名。
3. 更新 `assets-index.md` 中的状态和审核备注。
4. 如果用于小红书正式笔记，再复制到对应笔记的 `assets/` 目录。

未通过审核：

1. 不进入正式内容。
2. 在审核记录中写明失败原因。
3. 根据失败原因回到 `prompts.md` 修正提示词，或重新生成。

## 4. 小红书使用

每次写小红书配图建议时，先判断：

> 这个位置如果可以有人出现，先想一遍：是不是应该让 YUJI 的女生球友小羽出现？

适合小羽出现时，配图建议要写清：

- 使用哪个小羽基础参考图作为角色参考。
- 场景是什么。
- 动作是什么。
- 画面情绪是什么。
- 是否需要露出正脸、侧脸或背影。

## 5. 视频使用

视频只使用真实球友会做的小动作：

- 坐在场边握拍。
- 系鞋带。
- 撕旧手胶。
- 把旧球放进拍包侧袋。
- 低头喝水。
- 看向球场灯光。
- 和搭子短暂击掌或说球。
- 最后一局后收包离开。

视频不做夸张表演，不做偶像式回眸，不做技术教学口播。

## 6. 复盘

每次小羽出现在正式内容后，在 `assets-index.md` 的使用记录中补充：

- 日期。
- 资产编号。
- 使用位置。
- 内容主题。
- 数据或评论反馈。
- 后续判断。
```

- [ ] **Step 2: Verify workflow sections**

Run:

```bash
rg -n "生成首批基础参考图|小红书使用|视频使用|复盘|这个位置如果可以有人出现" docs/yuji-company/visual-system/xiaoyu/workflow.md
```

Expected: all five phrases are found.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/yuji-company/visual-system/xiaoyu/workflow.md
git commit -m "Add Xiaoyu visual asset workflow"
```

Expected: commit succeeds and includes only `workflow.md`.

---

## Task 6: Integrate Xiaoyu Into Brand Voice Skill

**Files:**
- Modify: `docs/yuji-company/skills/yuji-brand-voice.md`

- [ ] **Step 1: Insert Xiaoyu rule after `人物组合视觉规则` section**

Open `docs/yuji-company/skills/yuji-brand-voice.md` and find the section titled:

```markdown
## 人物组合视觉规则
```

At the end of that section, before `## 字体与文字质感`, insert:

```markdown

## 小羽默认出镜规则

小羽是 YUJI 工作室的固定成员，是 YUJI 的虚拟女生球友，也是所有可出镜内容优先考虑的前台人物资产。

当 YUJI 内容需要人物出镜时，先判断是否由小羽出现：

- 小红书封面需要女生球友视角时，优先考虑小羽。
- 视频需要主角、旁观者、场边人物或第一视角承载者时，优先考虑小羽。
- 羽迹卡、Player ID、羽迹时刻需要示例人物时，优先考虑小羽。
- 内容主题是情绪出口、下班后去球馆、最后一局、场边休息或混双搭子关系时，优先考虑小羽。

如果内容更适合旧物、空球馆、真实用户故事或搭子关系群像，可以不使用小羽；不要为了刷脸硬塞角色。

内部判断句：

`这个位置如果可以有人出现，先想一遍：是不是应该让 YUJI 的女生球友小羽出现？`
```

- [ ] **Step 2: Verify insertion**

Run:

```bash
rg -n "小羽默认出镜规则|YUJI 的虚拟女生球友|不要为了刷脸硬塞角色" docs/yuji-company/skills/yuji-brand-voice.md
```

Expected: all three phrases are found.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/yuji-company/skills/yuji-brand-voice.md
git commit -m "Add Xiaoyu visual role to brand voice"
```

Expected: commit succeeds and includes only `yuji-brand-voice.md`.

---

## Task 7: Integrate Xiaoyu Into Xiaohongshu Note Workflow

**Files:**
- Modify: `docs/yuji-company/skills/xhs-note-writer.md`

- [ ] **Step 1: Insert Xiaoyu check after `配图建议` requirement**

Open `docs/yuji-company/skills/xhs-note-writer.md` and find this list item:

```markdown
- 配图建议 2-3 条
```

Immediately after the related `ChatGPT 生图提示词` line, insert:

```markdown
- 小羽出镜判断：如果本篇需要人物承载情绪，必须判断是否由 YUJI 的女生球友小羽出镜；如果不用小羽，要说明原因。
```

- [ ] **Step 2: Add Xiaoyu image suggestion rule**

In the same file, after the `## 羽毛球场地视觉规则` section or the nearest visual rules section, insert:

```markdown
## 小羽配图建议规则

小羽是 YUJI 工作室的固定成员，是 YUJI 的虚拟女生球友。写小红书配图建议时，如果画面需要人物，优先判断是否使用小羽。

适合小羽出镜的笔记：

- 情绪出口。
- 下班后去球馆。
- 场边休息。
- 最后一局。
- 女生球友视角。
- 混双搭子关系。
- 羽迹卡、Player ID、羽迹时刻示例。

配图建议中如果使用小羽，必须写清：

- 使用正脸、三分之二侧脸、侧脸、背影、半身或全身。
- 她的动作。
- 她所在的球馆场景。
- 画面承载的具体情绪。
- 需要参考 `docs/yuji-company/visual-system/xiaoyu/prompts.md`。

不用小羽的合理原因：

- 本篇更适合旧球、旧拍、手胶、空球馆等静物视觉。
- 本篇更适合真实用户授权素材。
- 小羽出现会让内容像角色美图，而不是羽毛球情绪内容。
```

- [ ] **Step 3: Verify insertion**

Run:

```bash
rg -n "小羽出镜判断|小羽配图建议规则|visual-system/xiaoyu/prompts.md" docs/yuji-company/skills/xhs-note-writer.md
```

Expected: all three phrases are found.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/yuji-company/skills/xhs-note-writer.md
git commit -m "Add Xiaoyu check to Xiaohongshu workflow"
```

Expected: commit succeeds and includes only `xhs-note-writer.md`.

---

## Task 8: Generate and Register First Xiaoyu Front-Face Reference

**Files:**
- Read: `docs/yuji-company/visual-system/xiaoyu/prompts.md`
- Modify: `docs/yuji-company/visual-system/xiaoyu/assets-index.md`
- Add image: `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg`

- [ ] **Step 1: Generate `XY-BASE-01`**

Use the prompt under `基础参考图 1：正脸基础图` in `prompts.md`.

Save the selected output as:

```text
docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg
```

- [ ] **Step 2: QA the image**

Open the image and check it against `qa-checklist.md`.

The image must satisfy:

- Face is clear.
- She reads as 25-30 years old.
- Hair is black or deep brown.
- Expression is quiet and slightly tired, not smiling for the camera.
- Clothing is suitable for real badminton.
- Court is a badminton PVC court, not wood/basketball/volleyball.
- Image is not sexy, not influencer-style, not virtual-idol-like.

- [ ] **Step 3: Update asset index if accepted**

In `assets-index.md`, update the `XY-BASE-01` row from:

```markdown
| XY-BASE-01 | 正脸基础图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg` | 待生成 | 建立脸部记忆 | 需要脸清晰、五官稳定、不过度精修 |
```

to:

```markdown
| XY-BASE-01 | 正脸基础图 | `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg` | 可用 | 建立脸部记忆 | 已通过：脸清晰，气质安静，适合作为小羽后续角度参考 |
```

If the image fails QA, do not update the row to `可用`; regenerate before proceeding.

- [ ] **Step 4: Verify file exists and index is updated**

Run:

```bash
test -f docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg
rg -n "XY-BASE-01.*可用" docs/yuji-company/visual-system/xiaoyu/assets-index.md
```

Expected: both commands exit `0`.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg docs/yuji-company/visual-system/xiaoyu/assets-index.md
git commit -m "Add Xiaoyu front-face reference"
```

Expected: commit succeeds and includes the image plus `assets-index.md`.

---

## Task 9: Generate Remaining Five Base References

**Files:**
- Read: `docs/yuji-company/visual-system/xiaoyu/prompts.md`
- Modify: `docs/yuji-company/visual-system/xiaoyu/assets-index.md`
- Add images:
  - `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-02-three-quarter.jpg`
  - `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-03-profile.jpg`
  - `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-04-back.jpg`
  - `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-05-bench-halfbody.jpg`
  - `docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-06-fullbody-court.jpg`

- [ ] **Step 1: Generate each image in order**

Use the matching prompt from `prompts.md`:

- `基础参考图 2：三分之二侧脸图`
- `基础参考图 3：侧脸图`
- `基础参考图 4：背影图`
- `基础参考图 5：半身场边图`
- `基础参考图 6：全身球馆图`

For each image, reference `xy-base-01-front.jpg` as Xiaoyu's face anchor when the image generation tool supports reference images.

- [ ] **Step 2: QA each image**

Each image must pass `qa-checklist.md`.

Additional requirements:

- `XY-BASE-02` and `XY-BASE-03` must look like the same person as `XY-BASE-01`.
- `XY-BASE-04` must not sexualize the back view.
- `XY-BASE-05` must carry emotional stillness, not fashion posing.
- `XY-BASE-06` must look physically suitable for real badminton movement.

- [ ] **Step 3: Update asset index**

For each accepted image, update its row status from `待生成` to `可用` and write a short audit note:

```markdown
已通过：与正脸基础图一致，符合小羽角色气质
```

For `XY-BASE-04`, use:

```markdown
已通过：背影自然克制，没有性感化
```

For `XY-BASE-06`, use:

```markdown
已通过：全身比例自然，服装适合真实羽毛球运动
```

- [ ] **Step 4: Verify all images exist and all rows are usable**

Run:

```bash
test -f docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-02-three-quarter.jpg
test -f docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-03-profile.jpg
test -f docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-04-back.jpg
test -f docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-05-bench-halfbody.jpg
test -f docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-06-fullbody-court.jpg
rg -n "XY-BASE-02.*可用|XY-BASE-03.*可用|XY-BASE-04.*可用|XY-BASE-05.*可用|XY-BASE-06.*可用" docs/yuji-company/visual-system/xiaoyu/assets-index.md
```

Expected: all `test -f` commands exit `0`; `rg` returns all five IDs.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/yuji-company/visual-system/xiaoyu/assets/base-reference docs/yuji-company/visual-system/xiaoyu/assets-index.md
git commit -m "Add Xiaoyu base reference set"
```

Expected: commit succeeds and includes five images plus `assets-index.md`.

---

## Task 10: Final Verification

**Files:**
- Read:
  - `docs/yuji-company/visual-system/xiaoyu/README.md`
  - `docs/yuji-company/visual-system/xiaoyu/prompts.md`
  - `docs/yuji-company/visual-system/xiaoyu/assets-index.md`
  - `docs/yuji-company/visual-system/xiaoyu/qa-checklist.md`
  - `docs/yuji-company/visual-system/xiaoyu/workflow.md`
  - `docs/yuji-company/skills/yuji-brand-voice.md`
  - `docs/yuji-company/skills/xhs-note-writer.md`

- [ ] **Step 1: Verify core documentation exists**

Run:

```bash
test -f docs/yuji-company/visual-system/xiaoyu/README.md
test -f docs/yuji-company/visual-system/xiaoyu/prompts.md
test -f docs/yuji-company/visual-system/xiaoyu/assets-index.md
test -f docs/yuji-company/visual-system/xiaoyu/qa-checklist.md
test -f docs/yuji-company/visual-system/xiaoyu/workflow.md
```

Expected: all commands exit `0`.

- [ ] **Step 2: Verify all base assets exist**

Run:

```bash
find docs/yuji-company/visual-system/xiaoyu/assets/base-reference -type f | sort
```

Expected output includes:

```text
docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-01-front.jpg
docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-02-three-quarter.jpg
docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-03-profile.jpg
docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-04-back.jpg
docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-05-bench-halfbody.jpg
docs/yuji-company/visual-system/xiaoyu/assets/base-reference/xy-base-06-fullbody-court.jpg
```

- [ ] **Step 3: Verify Xiaoyu is integrated into YUJI workflows**

Run:

```bash
rg -n "小羽默认出镜规则|小羽出镜判断|小羽配图建议规则" docs/yuji-company/skills/yuji-brand-voice.md docs/yuji-company/skills/xhs-note-writer.md
```

Expected: all three phrases are found.

- [ ] **Step 4: Verify no placeholder language**

Run:

```bash
rg -n "TBD|TODO|待定|占位|以后再补|implement later" docs/yuji-company/visual-system/xiaoyu docs/yuji-company/skills/yuji-brand-voice.md docs/yuji-company/skills/xhs-note-writer.md
```

Expected: no matches.

- [ ] **Step 5: Commit final verification note if needed**

If no files changed during verification, do not commit.

If a small correction was required, run:

```bash
git add docs/yuji-company/visual-system/xiaoyu docs/yuji-company/skills/yuji-brand-voice.md docs/yuji-company/skills/xhs-note-writer.md
git commit -m "Finalize Xiaoyu visual asset system"
```

Expected: commit succeeds only if verification required a correction.

---

## Implementation Notes

- Do not introduce Xiaoyu as an AI or virtual-person technology in public-facing copy.
- Do not use Xiaoyu in every note by force. The rule is “priority consideration,” not “mandatory appearance.”
- If generated images are weak, do not lower the QA bar. Regenerate before marking assets `可用`.
- If the image tool cannot preserve Xiaoyu's face across angles, stop after `XY-BASE-01` and document the limitation in `assets-index.md` before continuing.
