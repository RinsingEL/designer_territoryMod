# City 案子：结构地形兼容适配 v0.1

## 状态

已完成 v0.1 诊断闭环，并入当前 City 主线。

本案 v0.1 不先实现自研台基、削坡、填土和地形重写，而是先在 worldgen-time placement 主线中记录 terrain adaptation / Beardifier 相关 trace。目标是区分两类问题：

- 结构包自身 `terrain_adaptation=none` 或适配弱。
- City planned structure 注入时序没有被 Beardifier / terrain adaptation 看到。

## 当前口径

- 结构仍走 worldgen-time placement，不回退 late paste。
- D6 preflight 锁定 actual bbox / piece boxes / signature。
- worldgen planned structure 记录 ledger 时同步记录 terrain adaptation 诊断字段。
- D7 trace 汇总 `terrainAdaptationReport`。
- hook 不可用时报告 `CITY_TERRAIN_ADAPTATION_HOOK_UNAVAILABLE`，不能静默声称兼容成功。
- 结构为 `terrain_adaptation=none` 或 Beardifier 未命中时报告 `TERRAIN_ADAPTATION_NOT_APPLIED`。

## 当前 ledger / trace 字段

`placed_structure_ledger.json.placedStructures[]` 增加：

- `terrainAdaptation`
- `terrainAdaptationHookAvailable`
- `beardifierSeen`
- `terrainAdaptationReasonCode`

`structure_materialization_trace.json` 增加：

- `terrainAdaptationReport.schemaVersion=city_terrain_adaptation_report.v0.1`
- `status`
- `hookUnavailableCount`
- `terrainAdaptationNoneCount`
- `beardifierSeenCount`
- `items[]`

## 当前判断口径

| 条件 | reason |
| --- | --- |
| hook 不可用 | `CITY_TERRAIN_ADAPTATION_HOOK_UNAVAILABLE` |
| Beardifier / terrain adaptation 被观察到 | `TERRAIN_ADAPTATION_OBSERVED` |
| configured structure 为 none 或未命中 | `TERRAIN_ADAPTATION_NOT_APPLIED` |

v0.1 的 `terrainAdaptationHookAvailable` / `beardifierSeen` 默认仍可能为 false；这不是宣称“地形适配失败”，而是明确告诉验收者：当前只完成诊断汇总，还没有把 Beardifier 观察 hook 做成强保证。

## 验收

- D7 trace 必须能看到 `terrainAdaptationReport`。
- 浮空、硬切、台基缺失等问题必须能从 trace 判断是否属于 `terrain_adaptation=none` / hook unavailable / not seen。
- active path 不允许用 late paste 或清树补丁伪装地形兼容成功。
- 结构 bbox / signature / ledger 防撞逻辑不能被地形诊断影响。

## 暂不处理

- 不做完整地形重写。
- 不实现自研台基 / 削坡 / 填土主线。
- 不让地形适配改变 D4 结构选择或 D6 防撞结果。
- 不接入第三方地形兼容 mod 的正式 API。

## 后续方向

- 增加 Beardifier / terrain adaptation 观察 hook，确认 planned structure 是否进入 Beardifier。
- 检测 configured structure JSON 的 `terrain_adaptation` 来源与具体值。
- 对 `terrain_adaptation=none` 的结构提供 profile 级 foundation policy。
- 对城墙、港口、桥梁单独设计地形融合策略。
