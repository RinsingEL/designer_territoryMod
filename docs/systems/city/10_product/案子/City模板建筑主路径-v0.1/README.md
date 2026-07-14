# City 模板建筑主路径 v0.1

一、目的：

1、城市建筑尺寸与方向不可控问题修复：
   1. 固定建筑直接读取 StructureTemplate NBT 的真实尺寸，不再以 Jigsaw 的多次采样结果作为排布依据。
   2. City 在规划时明确建筑变体、旋转、镜像和道路入口，使同一计划可复现。
   3. 阵列、簇和外扩间距以旋转后的真实 bbox 计算，消除因稳定最大包络造成的无意义远距。

2、结构包络过度膨胀问题修复：
   1. 固定模板禁止使用 D2 的随机最大包络、TerraSense 静态尺寸和实际落地尺寸混合排布。
   2. Template 的原始 bbox、旋转后 bbox 与碰撞 bbox 使用同一模板真值；碰撞 bbox 只额外保留必要通行边距。
   3. 例如原始尺寸为 `10×10` 的模板，其碰撞 bbox 应控制在约 `15×15` 至 `20×20`，不得膨胀为远大于建筑本体的预留方块。

3、城市布局责任错位问题修复：
   1. 城市内不再把随机选模板、随机旋转和随机拼接交给 Jigsaw。
   2. 建筑多样性由 City 按固定 seed 选择模板变体，不以不可见的 Jigsaw 展开替代城市设计。
   3. 地形适配、阵列形态、功能区密度与建筑间关系继续由 City 决定。

4、道路衔接来源不清问题修复：
   1. Template 落地不依赖 Minecraft StructureStart 或 RoadWeaver 的自动结构发现。
   2. City 按模板配置的道路入口主动向 RoadWeaver 注册端点与连接，使道路与建筑布局使用同一真值。

5、建筑资源可配置化与规划性能优化：
   1. AI 选择语义建筑类型与风格，不直接选择 NBT 文件名或 Jigsaw 结构 ID。
   2. 模板、变体、允许朝向、道路入口和地形姿态由配置索引维护，可替换皮肤而不改规划逻辑。
   3. 固定模板直接读取游戏接口提供的尺寸，取消 D2 多点重采样、最大包络聚合及其缓存开销。

二、方案：

1、模板建筑主路径：
   1. 将城市可规划建筑定义为 Template 建筑；每个条目对应一个或多个固定 NBT 模板。
   2. 模板加载使用 Minecraft StructureTemplate 接口直接读取原始尺寸；按 City 指定的旋转、镜像换算真实 bbox，不自行猜测模板大小。
   3. 碰撞 bbox 以旋转后真实 bbox 加配置化的小范围通行边距生成；Template 不允许套用 Jigsaw 的稳定最大包络。
   4. D4 直接按真实 bbox 做候选、阵列和外扩布局；D6 锁定同一 bbox；D7 按同一模板与方向落地。

2、模板目录与语义选择：
   1. 模板目录按语义类型、风格、变体、道路入口、允许方向和地形姿态建立配置索引。
   2. AI 只提交功能语义与风格意图；City 以固定 seed 选定具体模板变体并写入计划。
   3. 模板内容可由结构方块制作和验证后导入目录；模板更新后以内容版本重新计算尺寸与规划。

3、Jigsaw 退出城市候选库：
   1. Jigsaw configured structure 不再作为 City 常规建筑、阵列填充或外扩成员。
   2. 既有 Jigsaw 能力保留给野外随机内容、原生村庄或显式兼容场景，不参与 City 的紧凑布局主链。
   3. 原先使用 Jigsaw 的城市语义建筑逐步替换为等价的固定模板变体。

4、RoadWeaver 衔接：
   1. 每个模板在配置中声明一个或多个局部道路入口。
   2. City 按最终旋转换算入口世界坐标，在 D5 向 RoadWeaver 注册端点与连接。
   3. 道路生成以 City 已锁定的建筑 bbox 和入口为准，不依赖对世界 StructureStart 的反查。

5、地形与落地：
   1. 模板保留地形姿态配置，明确可平整、可基础支撑、可沿坡或必须拒绝的落地方式。
   2. 地形不满足模板要求时，City 先调整候选点或拒绝该模板，不以改变建筑尺寸换取落地。
   3. 装饰阵列继续依附最终模板 bbox 和道路入口生成，保持结构、道路与生活装饰的相邻关系。

## 实施边界与状态

本案自本节起作为 City 模板建筑的当前主路径口径。状态为“v0.1 文档与数据契约锁定，按本契约接入 active worldgen”；既有 StructureStart / Jigsaw 方案只保留历史保护和迁移对照，不得继续解释为模板建筑 active 主路径。

- D2 只读取模板目录和 `StructureTemplate` NBT 真值，读取尺寸与内容 hash；模板建筑不查询 `Minecraft Registries.STRUCTURE`，不构造 `StructureStart`，不使用 Jigsaw pool。
- D4 选择 `templateRef`、`templateHash`、`variant`、`rotation`、`mirror` 与 anchor；本地几何只取已校验的 NBT `rawSize`，并派生 world `actualFootprint`，不维护独立 template bbox；AI 仍只提交建筑语义 / 风格意图，不直接提交 NBT 文件名作为选择逻辑。
- D5 允许保留 City 自己的 active template placement registry，作为 D5 -> worldgen 的交接；该 registry 只登记已锁定的模板计划、占用和入口，不把模板包装成 Minecraft StructureStart。
- D6 和 D7 必须沿用同一 placement identity：`templateRef`、`templateHash`、`variant`、`rawSize`、`rotation`、`mirror`、anchor；`actualFootprint` 必须由这组字段复算，任何漂移都必须 hard fail，不得用旧 profile、Jigsaw bbox 或默认模板补齐。
- D5 注册 RoadWeaver 的入口必须来自模板 `roadEntrances[]` 的 rotation / mirror 变换结果；不得从 bbox 外侧点伪造道路入口。缺 mod 的 `auto` 跳过道路，`roadweaver` hard fail，旧 debug road 只有显式 `worldedit_debug` 可用。

## Anchor 与 bbox 约定

- `anchor` 是模板变换后 footprint 的最小角世界方块坐标：`anchor.x / anchor.z` 对应 transformed X/Z footprint 的 `minX / minZ`，`anchor.y` 是模板放置 datum；anchor 不表示 bbox 中心，也不表示 bbox 外的道路点。
- 模板原始局部坐标使用 half-open 范围：`[0,width) × [0,height) × [0,depth)`；`roadEntrances[].position` 必须落在原始 X/Z half-open 范围内。
- 经过 rotation / mirror 后，transformed footprint 仍从相对坐标 `(0,0)` 归一化，世界实际建筑 bbox 使用 closed block bounds：`min = anchor`，`max.x = anchor.x + transformedWidth - 1`，`max.y = anchor.y + height - 1`，`max.z = anchor.z + transformedDepth - 1`。
- `collisionBBox` 和 `maskBBox` 也使用 closed bounds；只能在 transformed actual footprint 外按契约声明的 clearance / mask margin 扩展。计划、预览、ledger 不得混用 half-open 与 closed 的 max 值。
- 每条模板入口先按同一 rotation / mirror 变换局部坐标和方向，再加 anchor 得到 `transformed roadEntrances[]` 的世界位置；入口越界、方向不一致或模板 hash 不匹配均拒绝注册。

## 不做事项

- 不为 City active 主建筑查询 `Registries.STRUCTURE`、生成 `StructureStart`、展开 Jigsaw pool，或以这些对象的随机结果回写模板 footprint。
- 不以 D2 随机最大包络、TerraSense 静态尺寸、bbox 外侧伪入口或世界扫描结果替代模板 NBT、模板 hash 和 transformed roadEntrances。
- 不自动把旧 `structureId` / Jigsaw / StructureStart payload 转换为模板 placement；旧输入按契约错误码 hard fail。RoadWeaver 缺失时也不隐式回退 WorldEdit debug road。
