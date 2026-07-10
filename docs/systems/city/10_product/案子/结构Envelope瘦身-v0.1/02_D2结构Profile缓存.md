# 02 D2 结构 Profile 缓存

## 修改目的

D2 增加结构 profile 本地档案职责，用于在 City 设计前准备结构大小区间和稳定 bbox 信息。该阶段不参与城市构图，只负责把当前运行环境中的结构 registry、datapack、结构配置和生成上下文转成可复用的结构 profile 缓存。

## 方案

### 1. 本 mod 内部 dry-run profiling

D2 profile 通过本 mod dry-run 或后台 warmup 生成。本 mod 在加载后后台 warmup 或结构首次进入 City 规划池时，对当前 registry 中的目标结构执行 dry-run profiling，构造 StructureStart / pieces 但不写世界，以此统计每个结构的 `actualFootprint` 分布、`pieceBoxes`、bbox group、dominant group、stable max group 和稳定性标记。

### 2. 辅助批处理只作为开发加速

辅助 mod 或命令行批处理可以作为开发期加速工具，用于批量预计算并导出 `structure_envelope_facts.json`，但不作为线上必需链路。正式链路必须支持本 mod 自行 dry-run、校验缓存并在缓存缺失或过期时重算，避免离线 profile 与当前 datapack、mod registry、结构配置或生成器上下文不一致。

### 3. 缓存 key 与失效

`collisionEnvelope` 缓存 key 至少绑定 `structureId`、`structureConfigHash`、`sourcePackHash`、`generationConfigHash` 和必要的 seed / context profile。缓存命中时直接使用统计结果；缓存缺失时现场 lazy dry-run；缓存 hash 不一致时自动失效并重算。

### 4. 稳定 bbox 口径

对固定或近固定结构，`collisionEnvelope` 使用稳定实际 bbox 或 dominant bbox group。对 jigsaw 多样化结构，若 bbox group 集中则使用 dominant group，若存在多个稳定变体则使用当前 dry-run 锁定 group，若变体分散但边界可控则使用 stable max group。对村庄、强随机扩张或不可稳定预判结构，标记为例外类型，不纳入通用紧凑阵列口径。

## 可验收提交点

1. 实现 StructureBinder 内部 dry-run profiling 基础能力，提交 profile 生成和测试。
2. 增加本地结构 profile 缓存 key、hash 失效和重算逻辑，提交 cache 逻辑和测试。
3. 生成 dominant bbox group、stable max group 和不稳定结构例外标记，提交 envelope facts 口径和测试。

## 验收需求

1. 对固定或近固定结构，D2 profile 必须输出可复用的稳定 bbox 信息，并能生成 D4 可用的 `collisionEnvelope`。
2. 对 jigsaw 多样化结构，D2 profile 必须输出 bbox group、dominant group、stable max group 或等价稳定性信息。
3. profile 缓存必须绑定结构、pack、配置和生成上下文 hash；hash 不一致时必须失效并重算。
4. 缓存缺失时，本 mod 必须能自行 dry-run 生成 profile，不依赖辅助 mod 或离线批处理。
5. 不稳定结构必须有明确例外标记，不能伪装成普通紧凑阵列结构。
6. 验证用例必须证明缓存命中、缓存失效重算、固定结构稳定 bbox、多样化结构 bbox group 至少四类行为。
