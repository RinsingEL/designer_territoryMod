# CityLandformReviewPackage 数据契约

## 版本

| 字段 | 值 | 说明 |
|---|---|---|
| `schemaVersion` | `city_landform_review.v0.1` | City C1.5 地貌审查包初版 |

## 定位

`CityLandformReviewPackage` 是 City 系统 D3 (C1.5) 的主输出。消费 GIS 局部 `LandformPatch` 数据，生成带编号标签的 patch 摘要、图例、AI 上下文和规划上下文，供后续 C2 AI 功能区草案使用。

## 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schemaVersion` | string | 是 | 固定 `city_landform_review.v0.1` |
| `cityId` | string | 是 | 所属城市 ID |
| `grid` | object | 是 | 局部网格，继承 CitySiteContext |
| `targetScale` | object | 是 | `{ scale, radiusBlocks, cellStepBlocks }` |
| `reviewMapImage` | string | D3 端点必填 | 预览图路径；D3 HTTP/MCP 输出必须指向 `landform_review_map.png`，纯 builder 单测可为空 |
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
- C1.5 只复述 GIS metrics/tag/adjacency 事实，不输出“适合建设”“建议建设区域”等 C2 功能区决策文案

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

返回体中：

- `reviewMapImage` 指向该 PNG。
- `debugRefs` 至少包含该 PNG 与 D3 输出目录。
- `landformPatches[].mapLabel` 必须能在 PNG 中对应显示。
