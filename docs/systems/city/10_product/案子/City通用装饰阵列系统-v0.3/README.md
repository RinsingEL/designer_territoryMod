# City 案子：通用装饰阵列系统 v0.3

## 状态

当前装饰开发真值。v0.3 继承 [v0.2 的 Shape / Pattern / ContentPalette 通用几何](../City通用装饰阵列系统-v0.2/README.md)，本版只升级内容姿态、连续地形 run、fill-only foundation、运行时可观测性和 LandUse 农田职责边界。

本版不修改建筑 Template、StructureStart、Jigsaw、D4/D6 建筑几何或建筑落地主线。

## 内容姿态 v0.3

`content_index.json` 当前 schema 为 `city_decoration_content_index.v0.3`。每个 prefab 除 v0.2 字段外必须显式声明：

| 字段 | 规则 |
| --- | --- |
| `groundPlaneLocalY` | 模板内部地面平面的 local Y，范围 `0..height-1`。 |
| `embedDepthBlocks` | 仅 `placementMode=embed_surface` 可为正数；其他模式必须为 0。 |
| `clearanceMode` | `preserve` 忽略模板空气，不清除现场方块；`clear_template_air` 把模板显式空气纳入预检和清理。 |

`placementMode` 为 `above_surface | replace_surface | embed_surface`。统一放置原点：

```text
placementOriginY = datumY
                 + (placementMode == above_surface ? 1 : 0)
                 - groundPlaneLocalY
                 - embedDepthBlocks
```

`embed_surface` 必须配 `surface_replaceable`；它只把模板按声明深度嵌入，不允许逐列变形或隐式挖空。模板空气如何处理只由 `clearanceMode` 决定。

默认 `medieval_coastal` 素材包含显式 `fountain -> geomantia:decoration/fountain_01` 映射。该 prefab 为 `5x5x5` 广场中心水景，使用 `above_surface + replaceable_only`、一格 comfort margin；只在程序显式请求 `fountain` 时进入 palette，不混入通用 `civic_plaza` 随机池。

v0.2 catalog 可只读加载，运行时按 `groundPlaneLocalY=0`、`embedDepthBlocks=0`、`clearanceMode=preserve` 解释，但文件和 hash 均不自动改写。`city_query_decoration_catalog` 必须返回 `contentIndexSchemaVersion`、`contentPoseUpgradeRequired` 和 `upgradeMode`。只有带 Geomantia managed manifest 且内容精确等于旧打包默认的目录，才允许经 `city_upgrade_default_decoration_catalog(confirmConfigMutation=true)` 显式备份并升级到 v0.3；自定义目录一律拒绝自动升级。

## 连续地形 run

`city_decoration_program_plan.v0.3` / `city_decoration_program.v0.3` 的 `terrainPolicy` 增加：

```json
{
  "maxSlopeDelta": 2,
  "allowWater": false,
  "invalidTerrainAction": "clip",
  "maxContinuousDropBlocks": 4,
  "continuousDropWindowBlocks": 8,
  "foundationMode": "none",
  "maxFoundationDepthBlocks": 0,
  "foundationShoulderBlocks": 0
}
```

- `cross_section_repeat` 和 `parallel_rows` 必须先在完整 target projection 上按延伸轴编译全局 run；run identity、ordinal 和终止判断不得按 owner chunk 重启。
- 每个 run 同时检查水体、相邻高差 `maxSlopeDelta` 和滑动窗口累计落差 `maxContinuousDropBlocks`。
- 首个不安全槽及其后续槽统一 `TERMINATE`；地形暂不可得时为 `DEFER`。最后一个安全槽若内容声明兼容 `terrainDropFallbackContentRef`，冻结为 `END_CAP`；否则保留普通安全内容。不得在各 chunk 独立猜 fallback。
- `allowWater=false` 在首个水体槽前终止；`allowWater=true` 可继续 run，但水体槽及跨水体间隔不得生成 foundation。
- FEATURES 阶段消费激活时冻结的 slot outcome；局部地形漂移、目标不可写或 placement 失败必须保留明确 reasonCode，不得静默跳过。`fill_only` 槽只在运行地表已达到 frozen target ±1 block 时 READY；否则以 `CITY_DECORATION_FOUNDATION_NOT_MATERIALIZED` 记为 `skipped`，不得强抬 datum，也不得作为 deferred 重试。

v0.2 program 可显式兼容读取；缺少的新字段使用无限累计落差窗口、`foundationMode=none` 等旧行为默认值。新规划输出 v0.3，不原地改写旧 artifact。

## Fill-only foundation

`foundationMode=fill_only` 只允许 `cross_section_repeat` / `parallel_rows`。职责分为两阶段：

1. `city_execute_d5` 激活前使用目标 `ServerLevel` 的 `ChunkGenerator.getBaseHeight/getBaseColumn` 采样完整支持 run；禁止加载或生成目标 chunk。采样结果冻结为 `city_decoration_frozen_terrain_runs.v0.1`，随 active plan 持久化。
2. 噪声阶段 `Beardifier` 只读取按 dimension / chunk 过滤后的不可变 foundation segment 快照，计算正密度。多个 segment 取最大贡献而非相加，肩部平滑衰减，深度受 `maxFoundationDepthBlocks` 限制。segment 原始投影参数落在 `[0,1]` 外时贡献严格为零，禁止肩部越过终止端点伸入水体 / 峡谷；单点 run 不生成径向 foundation。配置肩部覆盖到侧向水体或不可用列时，该 segment 的 shoulder 收缩为 0。

`Beardifier.compute` 内禁止 `getBaseHeight`、chunk load、文件读写或 active plan 变更，避免高度查询递归和 worldgen 线程竞态。FEATURES 只做局部复检、模板 datum 对齐和 NBT 放置，禁止用 `setBlock` 填柱。深坑超过上限时 run 在最后安全槽终止；本版不挖方、不架桥、不打隧道。

## LandUse 边界

LandUse 继续负责 area、vegetation policy 和 boundary。`SurfacePolicy.CULTIVATE` 的 interior surface operation 固定禁用，即使旧持久化 material palette 仍含 `minecraft:farmland` 也不得执行；农田内部地表由 Decoration tile / prefab 表达。PAVE 和 FENCE / HEDGE / LOW_WALL 等其他规则不变。

## 激活、账本与预览

- active schema：`city_active_decoration_program_plans.v0.3`；每项包含 compiled plan 和 `frozenTerrainPlan`。v0.2 active 文件可兼容读取；其中连续 pattern 会被明确停用并要求重新执行 D5，非连续 plan 才可使用空冻结计划。旧 activate overload 也不得接受连续 plan。
- ledger schema：`city_decoration_worldgen_ledger.v0.3`；`appliedFragments[]` 继续作为成功幂等真值，`fragmentOutcomes[]` 记录 `skipped | deferred | failed | applied`、reason、run / ordinal、terrain class、fallback decision、pose、foundation target，以及 `foundationPlanned` / `foundationMaterialized` / `foundationApplied`。`foundationApplied` 与 materialized 等价，任何 skipped / deferred outcome 都必须为 false；deferred / failed 不得锁死重试。
- D5 新增 `frozen_city_decoration_terrain_plan.json`、`city_decoration_terrain_activation_trace.json`、`city_decoration_preview_index.json` 和按 program 的激活预览图。激活预览必须区分普通槽、END_CAP、TERMINATE、DEFER 和 foundation 槽；规划期预览仍明确不是实际地形结果。

## 验收

- `above_surface`、`replace_surface`、`embed_surface` 使用同一原点公式；非零 ground plane、嵌入深度、保留空气和清理模板空气均有自动测试。
- 同一线性 run 跨 chunk 保持一个 runId 和连续 ordinal；水域、局部峭壁、累计缓降均在最后安全槽收尾。
- shallow pit 由正密度 foundation 平滑补齐；深坑终止；水体允许继续时不在 fluid segment 造 foundation；终止水列 / 峡谷端点外密度为零，侧向水体收缩 shoulder，单点 run 不造径向地基。
- FEATURES 在已成形地表返回 READY，在 mixin 未生效 / 地表仍为原高度时返回 `CITY_DECORATION_FOUNDATION_NOT_MATERIALIZED` skipped；ledger 的 planned=true、materialized/applied=false。
- mixin 空 segment 为严格零行为；foundation 查询只返回不可变、按 dimension / chunk 过滤的激活快照。
- ledger、activation trace 和激活预览均能解释 run 分类、终止、fallback、foundation 和 reasonCode。
- CULTIVATE interior 不再生成 farmland surface operation，其他 LandUse surface / boundary 行为不回归。
