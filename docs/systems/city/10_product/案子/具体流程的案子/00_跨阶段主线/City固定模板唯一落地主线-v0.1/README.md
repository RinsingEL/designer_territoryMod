# City 固定模板唯一落地主线

## 状态

当前正式建筑落地方案。City 只消费固定 NBT 模板，不使用 configured structure、运行时 Jigsaw、随机 envelope 或 FEATURES 阶段补贴。

## 主流程

```text
CityTemplateCatalog
-> D4 选择 templateId / variant / rotation / mirror
-> D5 按精确变换后 footprint 生成 reservation
-> D6 从当前世界重新读取 NBT 并锁定 identity、geometry、owner chunks
-> execute_d5 激活 planned structure registry
-> ChunkGenerator.createStructures 注入 City single-piece StructureStart
-> owner chunk 生成时粘贴固定模板
-> ledger 与 worldgen observation 记录结果
```

## 冻结契约

- NBT 的 `rawSize` 和内容 hash 是几何、身份真值；配置不能覆盖实际尺寸。
- 每个 catalog entry 必须声明允许的旋转、镜像、clearance 和本地 `roadEntrances[]`。
- D4、D5、D6、预览、worldgen 和 ledger 必须使用相同的坐标变换。
- D6 用当前世界中的模板重新校验 hash 和尺寸；旧 artifact 不可替代本次锁定。
- 所有 City 模板统一使用 `structure_start_beard_thin`。Minecraft 为 Beardifier 扩大的内部 bbox 不得回写规划 footprint。
- 每个 start 只包含一个 exact-footprint City piece；运行时不查询 pool，也不追加子 piece。

## 阶段职责

D2 和 catalog query 只暴露可检索的模板事实。D4 负责建筑之间的构图，结构选择必须显式，不允许 planner 临时抽取同名变体。D5 只准备 reservation、mask、道路入口和城墙上下文。D6 锁定实际 identity 与几何后，下游 LandUse 才能把结构 footprint 作为硬排除。

`city_execute_d5` 只激活生成期计划，不立即粘贴建筑。目标 chunk 首次进入结构生成阶段后，City 自有 StructureStart 才执行模板放置。重复 hook、重启或 owner chunk 重入必须由 registry 和 ledger 保持幂等。

## 道路与地形


## 明确拒绝

- configured structure ID、Jigsaw pool、depth 或随机展开参数。
- 统计 envelope、运行时 piece boxes 或动态 bbox 作为规划几何。
- `/place structure`、WorldEdit 或 FEATURES direct paste 作为正式 fallback。
- D6 后静默替换模板、变体、hash、旋转或镜像。
- 根据已落地 bbox 反向修改 D4/D5 计划。

## 验收重点

验证普通、processor 和大型跨 chunk 模板的 hash/尺寸锁定、四向旋转、镜像、入口变换、clearance、owner chunk 完整性、`beard_thin` 地形结果、重启幂等，以及 ledger 与现场方块观测一致性。目标城市的现场落地状态只由本次 run artifact 和观测结果判断，不写入产品契约。
