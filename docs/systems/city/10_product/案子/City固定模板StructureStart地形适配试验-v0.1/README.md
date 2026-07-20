# City 固定模板 StructureStart 地形适配试验 v0.1

## 定位

这是固定模板主线的受限运行时试验，不替换 D2-D6 的固定 NBT identity，也不恢复 configured structure 随机选择、envelope profiling 或 Jigsaw。

模板命名空间与目录 `terrainPosePolicy` 共同决定规划期冻结值：`templateId` 或 `templateRef`
以 `geomantia:` 开头时，目录模型和 D6 一律归一为 `structure_start_beard_thin`；其他命名空间
只有显式填写该值才进入本试验，其余继续使用既有 `FEATURES` owner-fragment direct template
placement。该规则只在目录加载 / D6 规划期生效，D5 与 worldgen 仍只消费冻结值，不迁移旧 active plan。

以下三个模板是已实测的首批样本：

- `geomantia:city/stubbs/agriculture/windmill_01`
- `geomantia:city/stubbs/agriculture/barn_windmill_01`
- `geomantia:city/stubbs/commercial/small_butcher_shop_01`

其他模板即使名称相似，也不会因名称进入试验；必须在模板目录显式设置该精确 policy，并从 D4
重新规划、D6 重新锁定、D5 重新激活。已存在的 active registry 是冻结快照，修改目录不会追溯
改变它。

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

`StructureStart` 只承担原版 structure lifecycle、跨 chunk placement 和 Beardifier 地形适配。D4/D6/D5
必须冻结同一 `terrainPosePolicy`；当其为 `structure_start_beard_thin` 时，D6 的 datum policy 固定为
`generator_base_height_motion_blocking_no_leaves`。piece 持久化 `templateRef`、`templateHash`、anchor、rotation、mirror、raw size 与 datum；其 X/Z bounding box 必须等于 D6 `lockedActualFootprint`。模板仍是建筑内容唯一真值。

试验 datum 的 policy 是 `generator_base_height_motion_blocking_no_leaves`：在 `createStructures` 通过 `ChunkGenerator.getBaseHeight(..., MOTION_BLOCKING_NO_LEAVES, ...)` 获取，并在创建 start 前持久化给所有 owner。不得在稍后的 FEATURES 高度图重新取 datum，否则 Beardifier 和 piece 的垂直基准会分裂。

## 装饰边界

City Decoration v0.4 的 content、冻结 terrain run、FEATURES 落地顺序和 fill-only foundation 全部保持当前实现。此试验不把装饰包装为 StructureStart，也不改变它的 catalog / program 契约。

当前 decoration density 仍加到原版 Beardifier 的结果上；因此真实验收必须观察建筑 beard 区与 decoration foundation 相交时是否过填。这是试验已知风险，不可在没有实机证据时把它宣称为已解决。

## 验收与退出

1. 后续规划的 `geomantia:` 模板必须冻结为 `terrainPosePolicy=structure_start_beard_thin`，并在未生成 anchor chunk 的 `createStructures` 日志中出现 `City template terrain StructureStart`；非 `geomantia:` 模板只有显式选择该 policy 才可创建 start。
2. 每个 start 只有一个 `geomantia:city_template_terrain_piece`，piece box 与 D6 locked footprint 一致。
3. `placed_structure_ledger.json` 的每个 owner fragment 使用同一个 `templateDatumY`，完成项记录 `terrainAdaptation=beard_thin`。
4. 观察风车、谷仓、肉铺在坡地、水岸和旋转状态下的底部地形；不得有模板片段重复写入或 direct FEATURES 写入。
5. 若 `geomantia:` 模板出现 datum 偏移、地形过填、piece 持久化失败或 fragment ledger 不完整，不能只改目录字段掩盖；应回退命名空间归一规则或改用非 `geomantia:` 模板身份，再从 D4 到 D5 重建。既有 active plan 不自动迁移。

该试验通过真实游玩验收前，固定模板唯一落地主线的其余删除门槛不变。
