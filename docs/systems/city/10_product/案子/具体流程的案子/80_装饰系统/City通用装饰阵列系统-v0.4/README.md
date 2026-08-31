# City 案子：通用装饰阵列系统 v0.4

## 状态

v0.4 是 v0.3 连续地形与嵌入落地后的农业分层扩展。它只改变 Decoration content 的组装和 FEATURES 落地顺序，不改变 D3、D4、D6、LandUse、建筑模板、City 自有道路或 Beardifier 的职责。

目标是把原先同一个 NBT 中的“耕地 + 小麦”拆成两个独立内容：基底仍是地表 prefab，小麦是受支撑条件约束的独立 plant 内容。它们在同一个几何 slot 内组合，不能通过两个普通 program 分别投影。

## 设计边界

- 一个外层 `DecorationSlot` 仍独占 owner chunk、datum、terrain run outcome、foundation、suppression bounds、hard-obstacle 检查和与其他 slot 的冲突判定。
- 一个 slot 可声明多个有序 `layers[]`。农业槽至少含 `base` 与依赖 `base` 的 `plant`。
- `base` 先用原版 `StructureTemplate` 正常放置，保留栅栏、楼梯、墙附件的邻居形状更新。
- `plant` 只允许受 catalog 信任的 `CropBlock` 状态，在 base 已成功或已满足后直接种植；不得泛化成普通花草、藤蔓或墙面附件的特殊写入。
- `plant` 使用不触发邻居连锁更新的写入标记，避免 FEATURES 尚未完成照明时触发 CropBlock 生存检查而被清为空气。
- 不允许用两个独立 program 在同一格分别放耕地和作物。它们会绕开既有冲突规则，且可能在 target、坐标系、连续 run 或 owner 上漂移。
- 不把耕地与每一种作物重新烘焙成组合 NBT。基底和作物可独立复用，风格只在 layer 的内容选择处变化。

## 执行顺序

```text
slot terrain / conflict / owner preflight
  -> base prefab placement (normal StructureTemplate shape updates)
  -> plant support and target check
  -> plant direct placement
  -> all required layers applied or already satisfied
  -> slot-level applied ledger
```

任一 required layer 失败时，不写外层 applied ledger。已成功写入的 base 不是可回滚事务，但下次 owner 回调会把精确相等的 base 记为 `already_satisfied`，只重试未完成的 plant。这样 ledger 的完成语义和幂等性仍在 slot 级保持原子。

## 地形与版本边界

连续 run、END_CAP、TERMINATE、foundation 和 datum 只绑定外层 slot 及其 base footprint；plant 不独立生成 terrain run、foundation 或 fallback。plant 的目标必须在同一 owner chunk 内，不能借此恢复跨 chunk prefab 写入。

当前开发主线只接受 v0.4 catalog、program、active plan 和 ledger。v0.2、v0.3 的内容不在运行时解释、不自动迁移、不提供 fallback；需要回到旧行为时使用 Git 切回对应提交。测试存档遇到旧 active plan 时直接清除并从 v0.4 重新规划，历史 ledger 只作为人工诊断记录。

## 验收

- 同一农业 slot 现场同时有 farmland 与 wheat，且小麦不会在首次 worldgen 后消失。
- 栅栏、楼梯和墙面附件仍使用原版模板邻居形状更新，不采用全局 `knownShape=true`。
- 同一 slot 的 base 与 plant 不互相冲突；不同 slot 仍按既有 priority / conflict bounds 冲突。
- plant 失败后外层 ledger 不得写 applied；base 已满足时重试只能补 plant。
- 连续 run 数量、runId、ordinal、foundation segment 数量不因 layer 数量增加而翻倍。
