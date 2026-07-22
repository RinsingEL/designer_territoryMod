# City Worldgen 方块观测数据契约

## 定位

`city_worldgen_block_observation.v0.1` 是 City 世界写入的调试证据，不是新的落地完成 ledger。

- Structure、LandUse、Decoration ledger 只证明对应执行器成功提交及幂等状态。
- 方块观测证明 Minecraft 在后续生命周期回调中实际返回了什么 `BlockState`。
- 两者必须分开解释；禁止再把 `appliedOperationCount`、`appliedPrefabPlacementCount` 或“已落地 N 个”直接当成现场方块存在证明。

首版只跟踪 City 自己触达的位置，不扫描完整 chunk，不监听其他模组的任意写入，也不为查询加载或生成 chunk。

## 采集阶段

| `phase` | `sourceCallback` | 语义 |
| --- | --- | --- |
| `post_features` | `ChunkGenerator.applyBiomeDecoration:TAIL` | City 在 HEAD 写入后，等待本次完整 biome decoration 回调结束，再从 `WorldGenLevel` 读取实际状态。可发现同一 FEATURES 流程中的后续覆盖。 |
| `post_retry_tick` | `Forge.ServerTickEvent:END` | 模板首次生成延迟重试成功后，在该 tick 回调末尾读取实际状态。 |
| `chunk_save` | `Forge.ChunkDataEvent.Save` | 目标 chunk 进入保存回调时，从待保存 `ChunkAccess` 再读一次。它是首版最晚的持久化检查点。 |

`post_features` 或 `post_retry_tick` 之后，同一目标 chunk 的待保存检查集按坐标合并，后一次写入覆盖同坐标的旧期望但不得丢掉其他坐标；`chunk_save` 捕获后移除。服务器重启时不恢复该临时检查集，已有 JSONL 历史仍可查询。

回调只读取 touched positions 并把不可变状态快照送入内存队列，不在 worldgen/save 回调里构造大 JSON 或做文件 IO。server tick END 每 tick 最多刷出 2 条；停服前刷完。查询必须同时读取 JSONL 与尚未刷盘的队列并按 `observationId` 去重，因此不得因为延迟刷盘短暂返回假 `NOT_OBSERVED`。

## 存储

每个维度和 chunk 独立追加：

```text
<server-root>/geomantia_city_masks/worldgen_block_observations/
  dim_<base64url(dimensionId)>/chunk_<x>_<z>.jsonl
```

JSONL 每行必须是一个完整、紧凑 JSON object；禁止用 pretty-print JSON 跨多行写入。写入失败只记录诊断日志，不得中断 worldgen 或把 ledger 回滚为失败。

## 记录结构

```json
{
  "schemaVersion": "city_worldgen_block_observation.v0.1",
  "observationId": "4dc2d5a7-a5f5-4b7f-8187-ea52b623710c",
  "observedAt": "2026-07-22T03:00:00Z",
  "phase": "chunk_save",
  "sourceCallback": "Forge.ChunkDataEvent.Save",
  "dimensionId": "minecraft:overworld",
  "ownerChunkX": 12,
  "ownerChunkZ": -4,
  "chunkX": 12,
  "chunkZ": -4,
  "watchedBlockCount": 2,
  "matchedExpectedBlockCount": 1,
  "mismatchedExpectedBlockCount": 1,
  "postWriteExpectedBlockMismatchCount": 1,
  "matchedPostWriteStateCount": 2,
  "changedSinceWriteCount": 0,
  "actualAirBlockCount": 1,
  "rolledBackWriteCount": 0,
  "blocks": [
    {
      "x": 193,
      "y": 64,
      "z": -63,
      "source": "land_use_direct",
      "expectedBlockId": "minecraft:wheat",
      "postWriteState": {
        "blockId": "minecraft:air",
        "properties": {}
      },
      "postWriteMatchesExpectedBlock": false,
      "actualBlockId": "minecraft:air",
      "actualState": {
        "blockId": "minecraft:air",
        "properties": {}
      },
      "matchesExpectedBlock": false,
      "matchesPostWriteState": true
    }
  ]
}
```

约束：

- `blocks[]` 只包含当前 City capture 中最终未回滚的 watched position；同一位置多次写入时，以未回滚的最后一次写入为准。LandUse 会同时登记主坐标和四个横向邻居，以覆盖 fence/wall 等连接属性重算。
- `expectedBlockId` 是写入请求或模板 NBT 声明的目标方块 ID；`postWriteState` 是写入 API 返回后立即从 Minecraft 读到的完整状态；`actualState` 是生命周期回调再次读到的完整状态。
- `postWriteMatchesExpectedBlock=false` 表示执行器声称写入成功，但写入返回后现场就不是目标方块。`matchesExpectedBlock=false` 表示生命周期回调时目标方块不存在。`matchesPostWriteState=false` 表示方块在写入后到回调之间发生了 ID 或 properties 变化。
- `postWriteState.properties` 与 `actualState.properties` 保留全部 BlockState 属性，因此 age、朝向、连接状态等变化进入 `matchedPostWriteStateCount/changedSinceWriteCount`；`matchedExpectedBlockCount` 仍只比较模板或请求声明的 registry ID。
- `actualAirBlockCount > 0` 不自动等价于 bug，因为显式模板空气也可能是期望值；判断必须同时看 `expectedBlockId` 和 `matchesExpectedBlock`。
- `source` 当前可为 `city_structure_template`、`land_use_direct`、`land_use_prefab`、`city_decoration_prefab`、`city_decoration_plant` 等 City 写入来源。
- 本契约不保存 BlockEntity NBT，避免把容器内容、文本或玩家相关数据带入调试产物。

## 查询

MCP `city_query_worldgen_observations` / HTTP `POST /realm/city/query_worldgen_observations` 按以下字段查询：

- 必填：`dimensionId`、`chunkX`、`chunkZ`。
- 可选：`phase=post_features|post_retry_tick|chunk_save`。
- 可选：`limit=1..100`，默认 10，只返回最近匹配记录。
- 可选：`includeBlocks`，默认 true；false 时只返回计数摘要。

响应 `status=OBSERVED|NOT_OBSERVED`，并返回 `pendingSaveVerification`、`pendingPersistenceCount`、`artifactPath`、`observationCount`、`observations[]`。查询只读 sidecar、内存待刷盘 observation 和 pending-save 标记，不获取 chunk ticket，不调用 `getChunk(...)`，不触发加载、生成或保存。非法 dimension、phase 或 limit 必须返回参数错误，不得静默归一。

## 验收口径

- 执行器 ledger 成功但 `postWriteExpectedBlockMismatchCount > 0` 时，必须按“代码返回成功、方块当场未真实落地”处理；`mismatchedExpectedBlockCount > 0` 表示回调现场不一致；`changedSinceWriteCount > 0` 表示写入后的 BlockState 被改变。三者都不能仅凭 ledger 宣称真实落地。
- 农田作物缺失案例必须能直接从对应 chunk 的 `blocks[]` 看见期望作物、实际 air/其他方块与坐标，无需 AI 再解析 region 数据。
- 自动测试覆盖当场未落地、回调不匹配、同 ID properties 改变、air、pending-save 快照合并、phase/limit/dimension 严格校验、非法 JSONL/字段跳过、维度目录无碰撞和 `includeBlocks=false`。
- 最终仍需在新生成 chunk 上完成真实 Forge 回调验收；普通 JUnit 不能替代 `WorldGenLevel` 与 chunk save 生命周期。
