# LandUse Owner 事务失败粒度过大

## 状态

已修复，待新区块实机复验。

## bug原因：

失败隔离粒度过大：LandUse 将整个 owner 内的 BASE、NBT、CROP、BOUNDARY 和多个 placement 绑定为同一成败边界，任一局部内容不适配都会取消其他正常操作；本次由水槽 prefab 预检触发。

错误未分级：可局部回退的内容不适配与不可写、快照失败等系统错误共用 owner 失败路径。

## 解决方案：

按失败类型分级隔离：完整 footprint 的内容不适配冻结为 placement 级 `FALLBACK`，系统级错误才阻断整个 owner。

按依赖范围补偿：跨 owner 共享并持久化同一决议；fallback 只恢复原本被该 placement 抑制的作物与边界格，不影响其他 LandUse 内容。
