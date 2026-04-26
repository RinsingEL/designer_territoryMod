# TerraSense Runtime Jigsaw 问题与修改记录

## 本轮背景

本轮原始目标是让 StructureBinder 中独立 `city_jigsaw_solve` 工具改为调用 vanilla jigsaw 深度 1 拼接。

在 `g_market_02` 的真机验证中，独立工具已经能稳定区分：

- 旧 synthetic connector
- 真实 jigsaw connector

但在真实 connector 路径上仍出现：

- `parent_connector_not_found_in_template`

于是本轮排障从 StructureBinder 一直追到了 TerraSense 的 `C3.5` catalog 生成链。

## 现场复现记录

测试样本：

- `city_id = city_3120_-3200`
- `group_id = g_market_02`
- `build_area_id = ba_g_market_02_a001`
- `parent_node_id = start_g_market_02`
- `selected_template_id = minecraft:village/taiga/houses/taiga_butcher_shop_1`

对比结果：

### 1. 旧 synthetic connector

输入：

- `parent_connector_id = next_start_g_market_02_south_1`

返回：

- `parent_connector_must_be_real_jigsaw_id`

这说明 StructureBinder 新工具已经正确拒绝旧 `C8` 流程里的 synthetic connector。

### 2. 真实 connector

输入：

- `parent_connector_id = jigsaw_south_4_0_8`

返回：

- `parent_connector_not_found_in_template`

并且接口 warning 显示：

- 期望的 parent connector 世界坐标：`3132,69,-3320 facing=south`
- runtime 模板里实际扫到的 jigsaw：
  - `3134,70,-3320 front=up name=minecraft:bottom`
  - `3135,70,-3328 front=north name=minecraft:building_entrance`

## 中间判断

这一步非常关键：

- catalog 中确实存在 `jigsaw_south_4_0_8`
- 但 runtime 模板实际扫到的 jigsaw 不支持把该点解释成一个“水平 south connector”

这意味着问题不在：

- vanilla jigsaw 的核心拼接逻辑
- 也不在 StructureBinder 的接口收参本身

而在于：

- catalog connector 真值与 runtime 模板里的原始 jigsaw 语义不一致

## 进一步核对

继续拆原版 `taiga_butcher_shop_1.nbt` 后确认：

- 模板内确实有两个 jigsaw
- 它们的局部坐标是：
  - `[4,0,8]`
  - `[7,0,6]`

但它们的原始 orientation 分别是：

- `south_up`
- `up_north`

也就是说，模板里的原始 jigsaw 真值从来就不是单个“north/south/east/west”。

## 问题根因

根因已经定位到 TerraSense 的 `C35Pipeline`：

### 1. TerraSense 扫描时拿到了原始 orientation

TerraSense 扫描模板时，原本就能读到：

- `south_up`
- `up_north`

这种完整 orientation。

### 2. 但后续被压扁成了简化 facing

旧逻辑里：

- `simplifyJigsawFacing(...)` 只要在 orientation 字符串里看到 `north/south/east/west`，就直接返回该方向
- 再通过 `horizontalDirection(...)` 继续筛一轮

结果就是：

- `up_north` 会被错误压成 `north`
- `south_up` 会被错误压成 `south`

### 3. connector 继续基于这个简化 facing 派生

旧 connector 规则是：

- `connector.id = jigsaw_<facing>_<x>_<y>_<z>`
- `connector.facing = marker.facing`

这样一来，catalog 里的 connector 并不是 runtime jigsaw 的完整派生，而是“简化后”的二次产物。

## 本轮修改

### TerraSense 代码侧

本轮已经把 TerraSense 的扫描/派生模型改成保留 runtime 原始 jigsaw 语义。

#### 1. `StructureMetadata.JigsawInfo` 升维

新增保留：

- `target`
- `pool`
- `joint`
- `orientationRaw`
- `front`
- `top`
- `finalState`

保留兼容：

- `facing`
  - 现在仅等价于 `front`

#### 2. `StructurePlacer` 输出完整 runtime jigsaw 信息

现在分析结构时会同时读取：

- `orientation`
- `front`
- `top`
- `name`
- `target`
- `pool`
- `joint`
- `final_state`

#### 3. `C35Pipeline` 不再压扁 orientation

新的扫描逻辑改成：

- 先解析 `orientation_raw`
- 再拆出 `front/top`
- `jigsaw_points` 直接保存完整字段

#### 4. `connectors` 只从 `front` 为水平的 jigsaw 派生

新的 connector 规则：

- 只有 `front` 为 `north/south/east/west` 的 jigsaw 才能派生成 connector
- `front=up/down` 的 jigsaw 不再产出伪造水平 connector

#### 5. `stableConnectorId` 仍保持兼容形状

当前仍然沿用：

- `jigsaw_<front>_<x>_<y>_<z>`

但生成材料已经变成：

- runtime jigsaw 的 `front + local_pos`

而不是旧的字符串压缩结果。

### StructureBinder 排障侧

本轮同时做了这些配套改动：

- `city_jigsaw_solve` 只接受真实 jigsaw connector id
- synthetic connector 直接拒绝
- 失败时返回 parent jigsaw 的期望世界坐标与 runtime 实际候选 jigsaw
- parent/child jigsaw 扫描改为直接从 `StructureTemplate.filterBlocks(..., Blocks.JIGSAW)` 获取

## 当前结论

### 已确认的结论

1. `connector` 不应被视为独立真值
2. runtime 模板里的原始 jigsaw 才是 connector 的上游真源
3. TerraSense 旧版 `C3.5` connector 派生逻辑会把垂直 jigsaw 错误压成水平 connector
4. StructureBinder 在 `g_market_02` 上看到的 mismatch 是 catalog 真值漂移，不是 vanilla jigsaw 理论错误

### 当前完成度

- TerraSense 模型与派生逻辑已完成代码修正
- TerraSense 本地 `compileJava` 已通过
- 辅助 mod 案子文档已建立

### 当前未完成

- 还没有用新 TerraSense 重新导出一版 `C3.5` catalog
- 还没有把新 catalog 回灌到 StructureBinder 再跑 `g_market_02`
- 还没有推进 StructureBinder 消费 `orientation_raw/front/top/name/target/pool/joint` 这些新增字段

## 下一步建议

1. 用新 TerraSense 重导 `C3_5_StructureCatalog.preprocessed.json`
2. 将新 catalog 同步给 StructureBinder
3. 再次真机验证 `g_market_02`
4. 视结果决定是否让 StructureBinder 的 solver 从“读取 connector 摘要”进一步升级为“优先消费 runtime 派生 jigsaw 细节”
