# AtlasCell 数据契约

AtlasCell 是 GIS 的最小栅格单元。它不是 Minecraft 方块，也不是区块，而是对一小片方块区域的地貌摘要。

## 设计目标

- 降低逐方块扫描和查询成本。
- 平滑 Minecraft 方块级噪声。
- 为坡度、TPI、地貌分类和 Patch 合并提供统一输入。
- 允许边缘 Cell 表达“部分完成”状态。
- 只记录地形事实和地貌语义，不替结构或城市判断“能不能落地”。

## 数据来源

AtlasCell 默认来自 Minecraft 当前世界生成器的先验采样。v1 优先调用 `ChunkGenerator`、`BiomeSource`、`RandomState` 等接口，取得基础高度、生物群系、海平面关系和可预测表面信息，再由这些信息派生坡度、起伏、TPI 和水距。

GIS 核心契约不依赖原版固定噪声参数。地形 Mod 可能完全改写噪声与生成管线，因此 AtlasCell 不记录“原版噪声值”，只记录当前生成器接口给出的地貌事实。

已生成或已加载 chunk 的真实高度图、方块和流体可以作为后验观测覆盖先验结果，但这不是 Atlas 建库前提。v1 不为了刷新 GIS 大范围预生成 chunk。

## 建议尺度

v1 建议：

| 字段 | 默认值 |
| --- | --- |
| cellStepBlocks | 4 |
| cellSize | 4x4 blocks |
| heightSample | cell 中心点或代表点高度 |

后续可以为不同 LOD 引入 8x8 或 16x16 Cell，但 v1 先保持单一尺度。

## 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| regionId | string | 所属 AtlasRegion 标识。 |
| cellX | int | Region 内或全局 Cell X 坐标。 |
| cellZ | int | Region 内或全局 Cell Z 坐标。 |
| blockMinX | int | Cell 覆盖范围的最小方块 X。 |
| blockMinZ | int | Cell 覆盖范围的最小方块 Z。 |
| sampleSource | enum | prior、observedLoaded、verifiedSurface 等。 |
| elevation | float | 地表高度。 |
| surfaceType | enum | 表面方块粗分类。 |
| biomeId | string | 生物群系标识。 |
| isWater | boolean | 是否水体。 |
| waterDepth | float | 水深估计。 |
| slope | float | 坡度指标。 |
| localRelief | float | 局部起伏。 |
| roughness | float | 粗糙度。 |
| tpiSmall | float | 小尺度 TPI。 |
| tpiLarge | float | 大尺度 TPI。 |
| waterDistance | float | 到最近水体或岸线的距离。 |
| landformType | enum | Cell 级地貌分类。 |
| stateFlags | bitset | sampled、metricsReadySmall、metricsReadyLarge、landformReady、patchReady、edgeDirty 等。 |

## SampleSource

| 值 | 含义 |
| --- | --- |
| prior | 来自生成器先验采样，不主动生成 chunk。 |
| observedLoaded | chunk 已加载或已生成，读取了真实高度图或方块状态。 |
| verifiedSurface | 为局部候选点执行过表面级验证，通常只用于物化前小范围校验。 |

消费者可以把 `observedLoaded` 和 `verifiedSurface` 当作更高可信度结果，但不能要求所有 AtlasCell 都达到这些状态。

## 职责边界

AtlasCell 不提供通用 `buildability` 字段。平原、岸线、浅水、悬崖和山脊对不同结构的价值完全不同，例如灯塔可能偏好岸线或悬崖，港口可能偏好浅水，村镇才更偏好低坡度平地。

GIS 的职责是回答“这里是什么地形”，结构、城市和道路系统的职责是根据自己的 profile 判断“这个地形是否适合我”。

## 状态约束

- `sampled = false` 时，不允许消费者使用指标层和地貌分类。
- `metricsReadySmall = false` 时，坡度、局部起伏、小尺度 TPI 不可信。
- `metricsReadyLarge = false` 时，大尺度 TPI、水距、区域级地貌分类不可信。
- `edgeDirty = true` 时，允许调试显示，但消费者应降低权重或等待补全。
