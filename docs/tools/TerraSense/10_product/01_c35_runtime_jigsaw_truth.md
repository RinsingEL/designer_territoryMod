# TerraSense C3.5 Runtime Jigsaw 真值修正

## 背景

主模块独立 `city_jigsaw_solve` 工具在 `g_market_02` 上做 vanilla jigsaw 实测时，出现了：

- catalog connector 给出 `jigsaw_south_4_0_8`
- runtime 模板实际扫到的 jigsaw 却对不上该 connector

继续追查后确认，问题不在 StructureBinder 的 vanilla adapter 主逻辑，而在 TerraSense 当前 `C3.5` connector 派生口径：

- TerraSense 扫描模板时拿到了原始 jigsaw `orientation`
- 但在生成 `jigsaw_points` / `connectors` 时，把 `orientation` 压成了单个简化 `facing`
- 像 `up_north` 这类垂直 jigsaw 会被错误简化成 `north`
- 最终 catalog 里的 `connectors` 不再等价于 runtime 模板里的真实 jigsaw

这会导致下游把 catalog 当真值时，出现：

- 误把垂直 jigsaw 当成水平 connector
- `connector id` 与 runtime jigsaw 真实几何语义脱节
- solver 明明在按 vanilla jigsaw 求解，却被错误 catalog 输入喂偏

## 本轮目标

- 让 TerraSense 的 `C3.5` jigsaw/connector 真值直接来源于 runtime 模板中的原始 jigsaw 数据
- 不再把 `orientation` 压扁成单个 `facing` 作为唯一真值
- 保留旧 `facing` 作为兼容字段，但它退化为摘要字段，不再是完整语义来源

## 当前决定

### 1. `JigsawMarker` 必须保存原始 jigsaw 语义

TerraSense 扫描模板后，`jigsaw_points` 至少要保留这些字段：

- `local_pos`
- `orientation_raw`
- `front`
- `top`
- `name`
- `target`
- `pool`
- `joint`
- `final_state`
- `facing`
  - 兼容字段，等价于 `front`

这里的真值优先级是：

1. `orientation_raw`
2. `front/top`
3. `name/target/pool/joint`
4. `facing`

### 2. `connectors` 只从“front 为水平”的 jigsaw 派生

`ConnectorSpec` 不再接受“只要 orientation 字符串里包含 north/south/east/west 就当水平 connector”的旧规则。

新的口径是：

- 先从 runtime jigsaw 解析 `front/top`
- 只有 `front` 为 `north/south/east/west` 的 jigsaw，才允许派生成 `connectors`
- `front=up/down` 的 jigsaw 不能再被误识别成水平 connector

### 3. `connector.facing` 退化为兼容字段

`ConnectorSpec` 继续保留：

- `facing`

但语义改为：

- `facing` 只是 `front` 的兼容镜像
- 下游若需要做严肃拼接、真机验证或 vanilla adapter 接入，应优先读取：
  - `orientation_raw`
  - `front`
  - `top`
  - `name`
  - `target`
  - `pool`
  - `joint`

### 4. `stableConnectorId` 继续兼容旧形状，但真值来自 runtime

当前阶段保持 connector id 仍可沿用：

- `jigsaw_<front>_<x>_<y>_<z>`

原因：

- 减少对下游已有读取逻辑的破坏
- 先解决“真值丢失”和“垂直 jigsaw 被误判为水平 connector”的问题

但需要明确：

- id 的生成材料必须来自 runtime jigsaw 的 `front + local_pos`
- 不能再来自被压扁后的字符串猜测

## 不做的事情

- 本轮不要求 StructureBinder 主模块立刻全部切到新 connector schema
- 本轮不要求 TerraSense 自动推导完整 socket 合法性网络
- 本轮不强行改写所有历史 catalog 文件

## 对 StructureBinder 的影响

TerraSense 修正后，StructureBinder 后续应遵守：

- catalog 中的 `connectors` 只作为 runtime jigsaw 的派生索引
- 真机排障时，优先以 runtime 模板扫描结果为准
- 当 catalog connector 与 runtime jigsaw 不一致时，应判为 catalog 真值漂移，而不是 vanilla jigsaw 算法错误

## 验收标准

- TerraSense 扫描出的 `jigsaw_points` 包含原始 `orientation_raw/front/top/name/target/pool/joint/final_state`
- `connectors` 只从 `front` 为水平的 jigsaw 派生
- `up_north` 这类垂直 jigsaw 不再产出伪造的 `north` connector
- `facing` 保留兼容，但不再是唯一真值字段
