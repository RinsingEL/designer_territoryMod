# City 固定模板 StructureStart 地形适配试验 v0.1

## 定位

这是固定模板主线的受限运行时试验，不替换 D2-D6 的固定 NBT identity，也不恢复 configured structure 随机选择、envelope profiling 或 Jigsaw。

试验只覆盖以下三个已实测模板：

- `geomantia:city/stubbs/agriculture/windmill_01`
- `geomantia:city/stubbs/agriculture/barn_windmill_01`
- `geomantia:city/stubbs/commercial/small_butcher_shop_01`

其他 City 模板继续使用既有 `FEATURES` owner-fragment direct template placement。范围之外的模板不能因为名称相似而进入试验路径。

## 执行模型

```text
D4 / D6 固定 template identity
  -> createStructures anchor chunk
  -> generator base-height 冻结 datum
  -> 一个 geomantia:city_template_terrain StructureStart
  -> 一个 CityTemplateTerrainStructurePiece
  -> Beardifier terrain_adaptation=beard_thin
  -> 原版按 piece bounding box 逐 chunk 处理固定 NBT
  -> 每个 owner 写 template fragment，全部完成后发布 placed ledger
```

`StructureStart` 只承担原版 structure lifecycle、跨 chunk placement 和 Beardifier 地形适配。piece 持久化 `templateRef`、`templateHash`、anchor、rotation、mirror、raw size 与 datum；其 X/Z bounding box 必须等于 D6 `lockedActualFootprint`。模板仍是建筑内容唯一真值。

试验 datum 的 policy 是 `generator_base_height_motion_blocking_no_leaves`：在 `createStructures` 通过 `ChunkGenerator.getBaseHeight(..., MOTION_BLOCKING_NO_LEAVES, ...)` 获取，并在创建 start 前持久化给所有 owner。不得在稍后的 FEATURES 高度图重新取 datum，否则 Beardifier 和 piece 的垂直基准会分裂。

## 装饰边界

City Decoration v0.4 的 content、冻结 terrain run、FEATURES 落地顺序和 fill-only foundation 全部保持当前实现。此试验不把装饰包装为 StructureStart，也不改变它的 catalog / program 契约。

当前 decoration density 仍加到原版 Beardifier 的结果上；因此真实验收必须观察建筑 beard 区与 decoration foundation 相交时是否过填。这是试验已知风险，不可在没有实机证据时把它宣称为已解决。

## 验收与退出

1. 仅以上三个模板在未生成 anchor chunk 的 `createStructures` 日志中出现 `City template terrain StructureStart`。
2. 每个 start 只有一个 `geomantia:city_template_terrain_piece`，piece box 与 D6 locked footprint 一致。
3. `placed_structure_ledger.json` 的每个 owner fragment 使用同一个 `templateDatumY`，完成项记录 `terrainAdaptation=beard_thin`。
4. 观察风车、谷仓、肉铺在坡地、水岸和旋转状态下的底部地形；不得有模板片段重复写入或 direct FEATURES 写入。
5. 若出现 datum 偏移、地形过填、piece 持久化失败或 fragment ledger 不完整，撤回 `CityTemplateTerrainStartPolicy` 中的该模板 ref，即刻回到原 direct-template 路径。

该试验通过真实游玩验收前，固定模板唯一落地主线的其余删除门槛不变。
