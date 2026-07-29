# City 案子：结构语义重标记 v0.1

## 定位

本案用于整理 TerraSense 结构语义。当前问题不是 City 需要新增枚举，而是结构包里的 tag / function terms 还不够清晰，导致 D4 选结构和人类验收时难以形成稳定意图。

本案只定义目标和框架，具体结构清单由后续人工挑选和 Studio 标注补齐。

## 核心目标

- 由 TerraSense Studio / 白名单维护结构语义，City 不再发明第二套 `functionTag` / `functionType`。
- 先覆盖传统城市功能，让 AI / Codex / 人类都能用同一套术语读懂结构。
- 每个结构允许多标签，但标签必须来自白名单，不允许代码自动脑补新标签。

## 初始功能框架

首批建议覆盖：

- 行政
- 防御
- 居住
- 农业
- 商业
- 港口 / 水岸
- 工坊 / 生产
- 仓储
- 宗教 / 仪式
- 景观 / 地标
- 道路节点 / 广场
- 市政 / 公共服务

这些不是 City 枚举，只是 TerraSense 白名单候选方向。

## 标注原则

- `functionTerms` 表示用途。
- `placementTerms` 表示适合放在什么地形或城市位置。
- `styleTerms` 表示材质、时代、文化、结构包风格。
- `usageTerms` 表示玩家感知用途或交互属性。
- `qualityTerms` 表示测试状态、推荐程度、是否真实验收过。

禁止：

- 禁止 City 代码根据结构 id 生成新语义。
- 禁止把缺失 tag 的结构自动映射成 `unknown_harbor`、`village_like` 等临时枚举。
- 禁止为了兼容旧功能区流程恢复 City 自建语义白名单。

## 工作流草案

1. 人工挑选一批结构。
2. TerraSense Studio 标注功能、风格、放置、用途、质量标签。
3. 导出 `StructureProfile.jsonl`。
4. City D4 只消费导出的原始 terms。
5. 真实验收后把 `quality.real_playtest`、适配风险等回写 TerraSense。

## Trek 固定模板首批画像（2026-07-27）

- `tools/city_templates/trek_fixed_manifest.json` 是 20 个 Trek B0.6 固定 NBT 的人工审核语义源；导出器不得从结构 id 自动推断标签。
- profile identity 使用 `geomantia:city/trek/...`，统一为 `single / structure_template_nbt / city_template_nbt / fixed_footprint`，不得复用旧 `trek:...` Jigsaw assembly 的 `structure_assembly / system_root` 身份。
- 首批 canonical terms 覆盖居住、商业、农业、功能设施、防御、港口、行政、地标，以及沿街、城市边缘、滨水和城市核心等放置语义；完整词表随 profile 包冻结。
- 旧人工审核记录仍保留作历史证据。例如 `maison` 曾被人工覆盖为“磨坊 + 农业”，新固定模板画像纠正为 `function.residential`，但不改写旧工作区记录。
- `quality.approved_baseline` 只表示已通过本轮人工筛选，可进入语义检索；不得解释为 `quality.real_playtest`，也不得跳过 runtime metadata 或正式 City template catalog 闸门。入口确认另以 manifest 的固定 NBT 证据追溯，不由语义 quality term 代替。
- TerraSense profile 中携带的 `fixedFootprint` 只用于画像展示和一致性检查；D4-D7 的规划几何仍只读取当前世界 NBT 与显式 `city_template_catalog.v0.1`。

## 验收

- D4 trace 中所有结构语义都能追溯到 TerraSense profile。
- City 代码不新增结构语义枚举。
- 同一结构可以被 AI 解释为多个功能候选，但候选词来自 TerraSense 白名单。
- 人工能够按功能框架筛出一组农业区、居住区、港口区、行政区测试结构。

## 暂不处理

- 不在本案决定完整结构清单。
- 不设计复杂 ontology。
- 不做结构推荐排序算法。
- 不做自动 tag 生成。

## 待定

- 第一批结构包范围。
- 每个功能至少需要多少可验收结构。
- 是否需要区分“主结构”和“辅助结构”。
