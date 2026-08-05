# City 案子：结构语义重标记 v0.1

## 定位

本案用于整理 TerraSense 结构语义，并冻结 City 自己负责的 placement topology。结构包里的功能、规划角色和风格仍由 TerraSense 动态词表维护；结构落地拓扑不是开放词表，必须由 City 固定枚举承载，避免自然语言地形标签演变成另一套不可控规则引擎。

本案只定义目标和框架，具体结构清单由后续人工挑选和 Studio 标注补齐。

## 核心目标

- 由 TerraSense Studio / 白名单维护结构语义，City 不再发明第二套 `functionTag` / `functionType`。
- 先覆盖传统城市功能，让 AI / Codex / 人类都能用同一套术语读懂结构。
- 每个结构允许多标签，但动态标签必须来自白名单，不允许代码自动脑补新标签。
- 每个正式结构必须声明一个或多个 `terrainModes`，当前值域固定为 `SURFACE | EMBEDDED | FLOATING`，多值按 OR 解释。

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

- `functionTerms` 表示结构功能，正式画像至少一项。
- `planningRoleTerms` 表示关键/填充等规划角色，不做 Java enum；连接结构复用填充池，不形成第三种永久等级。
- `terrainModes` 表示结构与地表的拓扑关系，是 City 固定枚举数组，不属于 TerraSense 动态词表，也不从功能标签推导。
- `styleTerms` 表示给 AI / 人工阅读的风格；程序不按它做评分、placement 或 worldgen 判断。
- 尚未完成可信人工重标记时，规划角色和风格显式为空；正式画像的 `terrainModes` 不得为空，禁止代码按结构 id 或退役标签猜值。
- 当前运行时只实现 `SURFACE`：结构 footprint 覆盖的全部 D3 格必须存在、已采样且非水；不按坡度、局部起伏或群系 hard reject。仅声明 `EMBEDDED/FLOATING` 时明确返回不支持。
- `reviewState=approved` 是正式目录唯一准入门禁；质量说明保留在策展资料，不再作为 City 结构语义 term。

禁止：

- 禁止 City 代码根据结构 id 生成新语义。
- 禁止把缺失 tag 的结构自动映射成 `unknown_harbor`、`village_like` 等临时枚举。
- 禁止为了兼容旧功能区流程恢复 City 自建语义白名单。

## 工作流草案

1. 人工挑选一批结构。
2. TerraSense Studio 标注功能、规划角色和风格，并为 City placement topology 选择一个或多个固定 `terrainModes`，完成人工审核。
3. 导出 `StructureProfile.jsonl`。
4. City D4 向 AI 暴露三组原始 terms 与固定 `terrainModes`；风格只供 AI 选择，程序只按 topology 做地形门禁。
5. 真实验收质量和适配风险回写 TerraSense 策展资料，不扩写 City 运行时画像。

## 当前运行时迁移（2026-08-04）

- 当前合并目录固定为 Trek 46 条、Stubbs 15 条，共 61 条 approved profile。
- 61 条画像统一迁移为 `terrainModes=[SURFACE]`，删除退役 `terrainTerms`。
- 既有沙漠、沼泽等环境风貌继续保留在 `styleTerms`，只给 AI 看，不转成群系 hard gate。
- 删除 `structure_terrain_policy.json` 与 `structure_terrain_policy_source.json`；`build_catalog.ps1` 重建目录时必须同时验证 46/15/61 数量和 `SURFACE` 默认值。

## Trek 固定模板首批画像（2026-07-27）

- `tools/city_templates/trek_fixed_manifest.json` 是早期 20 个 Trek B0.6 固定 NBT 的人工审核语义源；导出器不得从结构 id 自动推断标签。当前 61 条合并目录另按上一节迁移规则生成。
- profile identity 使用 `geomantia:city/trek/...`，统一为 `single / structure_template_nbt / city_template_nbt / fixed_footprint`，不得复用旧 `trek:...` Jigsaw assembly 的 `structure_assembly / system_root` 身份。
- 首批可信 canonical terms 只保留居住、商业、农业、功能设施、防御、港口、行政、地标等功能语义；旧沿街、城市边缘、滨水和城市核心 placement term 不自动转换为 `terrainModes`，当前独栋模板由人工批次统一声明 `SURFACE`。
- 旧人工审核记录仍保留作历史证据。例如 `maison` 曾被人工覆盖为“磨坊 + 农业”，新固定模板画像纠正为 `function.residential`，但不改写旧工作区记录。
- 固定模板能否进入正式语义目录只看 `reviewState=approved`；真实游玩质量不再编码为 `qualityTerms`，也不得跳过 runtime metadata 或正式 City template catalog 闸门。
- TerraSense profile 中携带的 `fixedFootprint` 只用于画像展示和一致性检查；D4-D7 的规划几何仍只读取当前世界 NBT 与显式 `city_template_catalog.v0.1`。

## 验收

- D4 trace 中所有结构语义都能追溯到 TerraSense profile。
- City 代码不新增功能、规划角色或风格枚举；placement topology 只使用已冻结的 `terrainModes` 枚举。
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
