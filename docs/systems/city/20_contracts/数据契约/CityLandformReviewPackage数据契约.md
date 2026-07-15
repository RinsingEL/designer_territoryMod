# CityLandformReviewPackage 数据契约

## 版本

| 字段 | 值 | 说明 |
|---|---|---|
| `schemaVersion` | `city_landform_review.v0.1` | City C1.5 地貌审查包初版 |

## 定位

`CityLandformReviewPackage` 是 City 系统 D3 (C1.5) 的主输出。消费 GIS 局部 `LandformPatch` 与成员 cell 数据，生成带编号标签的真实预览图、patch 薄索引、AI 上下文和规划上下文，供当前 D4 anchor / array 候选、设计 loop、城墙 reservation 和预览链路读取。旧 `PatchGroupPlan` 下游已删除。

## 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schemaVersion` | string | 是 | 固定 `city_landform_review.v0.1` |
| `cityId` | string | 是 | 所属城市 ID |
| `grid` | object | 是 | 局部网格，继承 CitySiteContext |
| `targetScale` | object | 是 | `{ scale, radiusBlocks, cellStepBlocks }` |
| `reviewMapImage` | string | D3 端点必填 | 预览图路径；D3 HTTP/MCP 输出必须指向 `landform_review_map.png`，纯 builder 单测可为空 |
| `patchScanPaddingBlocks` | int | D3 端点必填 | patch 上下文相对 `grid.blockBounds` 的额外扫描 padding；默认 128 |
| `patchContextBounds` | object | D3 端点必填 | D3 实际用于收集 patch/memberCells 的 bounds，等于 city grid 外扩 padding |
| `refreshedRegions[]` | object[] | D3 端点必填 | 本次 D3 刷新的 GIS region 列表，至少含 `regionId`、`regionX`、`regionZ`、`patchCount` |
| `legend` | array | 是 | 图例，颜色/标签/地貌类型 |
| `landformPatches` | array | 是 | GIS patch 摘要列表 |
| `planningContext` | array | 是 | City 补充的规划上下文 |
| `aiPromptContext` | string | 是 | 给 AI 的紧凑文字说明 |
| `debugRefs` | array | 是 | 调试图/报告路径 |

### landformPatches[] 子结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `landformPatchId` | string | 是 | GIS `LandformPatch.patchId` |
| `mapLabel` | string | 是 | 图上编号，如 `平原01`、`海岸02` |
| `displayLandformName` | string | 是 | 中文地貌名，如 `平原`、`海岸` |
| `landformType` | string | 是 | GIS 主地貌类型 contractName |
| `areaBlocks` | int | 是 | 面积估算 |
| `cellCount` | int | 是 | 包含 cell 数量 |
| `areaClass` | string | 是 | tiny/small/medium/large |
| `centerBlock` | object | 是 | `{ x, z }` patch 中心坐标 |
| `blockBounds` | object | 是 | patch block 包围盒，用于回查与缺少成员格子时的降级预览 |
| `geometryMode` | string | 是 | 正常为 `patch_member_cells`；只有缺少成员格子时降级为 `patch_envelope` |
| `memberCells` | array | 是 | GIS patch 真实成员 cell 薄索引，元素含 `{ cellX, cellZ, blockMinX, blockMinZ }` |
| `metricsSummary` | object | 是 | 高度/坡度/水距摘要 |
| `landformTags` | array | 否 | GIS 地貌标签（flat/gentle/steep/waterfront/low_confidence） |
| `overlayTags` | array | 否 | GIS 叠加标签（near_water/edge_dirty/fragment） |
| `summaryFacts` | array | 是 | 机器生成的事实摘要，只复述 metrics/tag/adjacency |
| `neighborLandformPatchIds` | array | 是 | 相邻 patch ID 列表 |

### metricsSummary 子结构

| 字段 | 类型 | 说明 |
|---|---|---|
| `meanElevation` | number | 平均海拔 |
| `minElevation` | number | 最低海拔 |
| `maxElevation` | number | 最高海拔 |
| `meanSlope` | number | 平均坡度 |
| `meanWaterDistance` | number | 平均距水距离 |

## 标签规则

- 按 LandformType 排序（WATER→SHORE→PLAIN→TERRACE→SLOPE→CLIFF→RIDGE→VALLEY→BASIN→UNKNOWN），组内按 cellCount 降序
- 全局编号从 01 开始
- 低置信度（confidence < 0.5）会在 facts 中标记
- 碎片 patch（FRAGMENT flag）会在 facts 中标记
- C1.5 的主输入是 `landform_review_map.png`；JSON 是图上 `mapLabel` 到 GIS patch / 成员 cell / metrics 的索引，不替代看图
- C1.5 只复述 GIS metrics/tag/adjacency 事实，不输出“适合建设”“建议建设区域”等 C2 功能区决策文案
- `grid` 是城市核心规划域；`patchContextBounds` 是额外 patch 覆盖域。D4 候选必须受 `grid` 约束，不能把 padding 区当成新的城市核心可选域。
- D3 必须按 `patchContextBounds` 覆盖多个 GIS region。只刷新中心 region 会导致靠近 region 边界的结构 / v4 城墙缺少 patch 背景。

## 面积分级

- tiny: cellCount ≤ 3
- small: cellCount ≤ 12
- medium: cellCount ≤ 48
- large: cellCount > 48

## 实现位置

- 实现类：`com.rinsing.geomantia.systems.city.domain.model.CityLandformReviewPackage`
- Builder：`com.rinsing.geomantia.systems.city.application.CityLandformReviewBuilder`
- 预览图：`com.rinsing.geomantia.systems.city.infrastructure.preview.CityLandformReviewMapRenderer`
- HTTP 端点：`POST /realm/city/plan_d3`
- MCP 工具：`city_plan_d3`

## D3 调试产物

`POST /realm/city/plan_d3` / `city_plan_d3` 必须写出：

- `run/realm_debug/<runId>/city_d3_<citySeedId>/landform_review_map.png`
- `run/realm_debug/<runId>/city_d3_<citySeedId>/city_landform_review_package.json`

返回体中：

- `reviewMapImage` 指向该 PNG。
- `debugRefs` 至少包含该 PNG 与 D3 输出目录。
- `patchScanPaddingBlocks`、`patchContextBounds`、`refreshedRegions[]` 必须可用于复核 patch coverage。
- `landformPatches[].mapLabel` 必须能在 PNG 中对应显示。
- `landformPatches[].memberCells` 必须能回查预览图中的 patch 形状；缺失时只能显式降级到 envelope。
