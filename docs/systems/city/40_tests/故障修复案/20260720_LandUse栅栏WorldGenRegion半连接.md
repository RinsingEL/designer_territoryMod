# LandUse 栅栏 WorldGenRegion 半连接

## 状态

已修复，待新区块实机复验。

## 现象

LandUse `boundaryPolicy=FENCE` 的连续橡木栅栏只显示单侧横杆。保存区块中的相邻栅栏已经是 `south=false / north=true` 等非对称 BlockState，因此不是客户端模型或渲染异常。

## 根因

第一次修复在当前格写入前调用 `Block.updateFromNeighbourShapes`，随后依赖 `Block.UPDATE_ALL` 通知既有邻居。Forge GameTest 使用 `ServerLevel`，该路径会通知邻居并双向通过；真实 FEATURES 使用 `WorldGenRegion`，其 `setBlock` 直接写入 `ChunkAccess`，不消费 flags，也不反向刷新先落地的栅栏。边界按稳定坐标顺序写入后，后写格能连接先写格，先写格无法连接未来格，形成系统性半连接。

## 修复口径

- 不改 LandUseAreaPlan、boundary loops、材质 palette 或 owner ledger。
- 写块后显式重算当前格及四个水平邻居中的 `CrossCollisionBlock`，同时覆盖 fence / wall。
- 中心 owner 的相邻格只在 FEATURES `WorldGenRegion` 的 write radius 1 内刷新；兼容入口若提前处理相邻 owner且外侧邻居不可写，本次 owner 恢复并等待中心回调重试，不引入远 chunk 写入。
- 单次刷新失败时恢复当前格和四个水平邻居快照；owner transaction 继续负责此前 mutation 的逆序回滚。
- 已完成旧区块不回填，只有修复后首次生成的 owner 使用新行为。

## 验收

- JVM：忽略全部 write flags 的访问器先写 `(15,y,z)`、后写 `(16,y,z)`，两格必须分别得到 `east=true` 与 `west=true`。
- JVM：模拟既有邻居刷新失败，新格和邻居必须恢复写入前状态。
- JVM：模拟连接邻居超出 write radius，必须拒绝远写、恢复主格且不留下半连接。
- Forge GameTest：只验证真实 Minecraft BlockState / ServerLevel 适配器冒烟，不再冒充 `WorldGenRegion` 集成测试。
- 实机：全新未生成 LandUse 边界中抽查同 owner 和跨 owner 连续栅栏，双方连接属性必须对称；旧截图现场不作为修复后验收样本。
