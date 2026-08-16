# W 与 T4 生成器原生粗地形预览 v0.1

## 问题

T4 在 T3 国境形成后需要从单国 owned territory 中粗选首都和其他城市的落脚区域。继续用 Minecraft `getBaseHeight` 对整片候选范围做密集扫描，会重复承担完整噪声路由和高度查询成本；直接复用 W 的旧地貌结果，又无法反映 RTF 等世界生成器当前参数下的真实宏观高低起伏。

这个阶段只需要排除大片水体、连续高山和高起伏区域，并不需要提前取得 D3 的最终地表真值。

## 决策

- W 与 T4 分别在自己的请求上提供 `preferGeneratorNativeTerrain` 开关，默认 `true`。两个开关按调用独立生效，不是全局配置：W 关闭不影响后续 T4，T4 关闭也不要求重跑 W。
- 开关开启且检测到兼容 RTF 运行时时，W 的 `prior` 粗扫和 T4 粗览都使用二维 Heightmap；关闭时强制使用 Minecraft prior sampler，并记录 `generator_native_disabled`。W 使用非 `prior` 模式时也强制回退并记录 `sample_mode_requires_minecraft_sampler`。
- 该能力属于 T4，不新增 D1 阶段。T3 先冻结 owned territory，T4 打开 `realm_t4` Patch Explorer 时按需生成粗地形证据。
- 每个 owned W cell 只在中心采样一次；不扫描 wild、contested、blocked 或其他国度 cell。
- 通过通用 `TerrainPreviewProvider` 选择数据源。RTF 激活且运行时 API 可用时走生成器原生二维 Heightmap；否则整体回退现有 `MinecraftPriorAtlasSampler`。
- RTF 适配以可选反射桥接 0.0.5 / 0.0.6，不建立编译期硬依赖，不读取 runtime tile cache，不创建或加载 chunk。
- 粗样本之间只用四邻高度差派生 `slopeProxy` 和 `localRelief`，不追加四方向高度查询。
- Patch Explorer 按 owned territory 内的 W 地貌 Patch 生成候选，并附带高度、水体、起伏、RTF terrain 和 source biome 证据；建议锚点优先非水、低起伏、低坡度，再以边界深度打破并列。
- 粗证据变化必须进入 Patch Explorer source identity。旧 session 或选择凭证不得继续冒充当前来源。

## 主流程

```text
sealed W -> T1/T2 -> T3 owned territory
                    -> T4 realm Patch Explorer 打开
                    -> lazy ensure 单国粗地形证据
                    -> AI 浏览并选择候选
                    -> T4 CitySeed
                    -> D3 step=16 局部精扫与显式审查
                    -> D4 及后续落地
```

W 快路径只替换生成器先验地形采样，不改变 W 的 tile、micro-sampling、地貌聚合和 sealed 规则。Tag Audit 仍使用 Minecraft 真实采样器作为独立复核层，不能被 RTF 粗览替代。

T4 粗览只缩小搜索范围。无论 provider 是 RTF 还是回退实现，产物都必须声明 `advisoryOnly=true` 和 `requiredNextGate=city_d3_site_review`。D3 的精扫、局部真实地貌和人工/AI 接受结果仍是城市能否进入 D4 的唯一最终闸门。

## 产物与缓存

单国输出位于 `<run>/realm_t4_terrain_preview/`：

- `<realmId>_coarse_terrain_evidence.json`
- `<realmId>_coarse_height_water_preview.png`

JSON 记录 run、realm、dimension、territory、W context、provider、采样语义和 source fingerprint；cell 记录采样坐标、高度、水体、Minecraft biome、生成器 terrain/source biome、邻格高度差、坡度代理和局部起伏。summary 提供高度分位、水体比例和分类直方图。

缓存至少绑定 territory、W context、cell step、dimension 和完整 provider provenance。JSON、PNG 或任一来源身份变化时必须整国重建，禁止逐点混合不同 provider 的结果。

W 的 `world_survey_manifest.json` 同样记录完整 `terrainProvider`，并将开关、provider ID、source kind、fast path、fallback reason、source fingerprint 和 sampling semantics 纳入 `configHash`。原版 prior 与 RTF prior 不得复用彼此的 tile / feature cache。

W 批量扫描不得调用 GIS 单区调试导出器生成逐 tile `progress.png`、`preview/*.png` 或对应调试 manifest。W 只保留断点续扫所需的 tile snapshot/meta，以及世界级最终预览和 manifest；单区 GIS refresh 仍保留完整调试导出。逐 tile 调试图不属于 W 正式契约。

面向大世界的开发验收档为半径 `32768`（直径 `65536`）、`cellStepBlocks=256`、`microSampleStrideBlocks=64`、`localSlopeRadiusBlocks=8`。该档用于验证原生快路径的吞吐与产物规模；D3 仍保留 step `16` 的局部最终审查。

## 失败与兼容边界

- RTF 未加载、当前维度未使用 RTF、`GeneratorContext` 不可用或反射契约不兼容时，记录明确 `fallbackReason` 并使用 Minecraft prior sampler。
- provider 已选定后若某个采样点失败，本轮显式失败；不允许在同一证据图中悄悄混用 RTF 与回退高度。
- 粗高度不包含最终 surface rule、结构、植被和玩家改造，不可用于 D4 精确结构锚点、地基或削坡。
- RTF 世界中的固定 NBT 结构落地仍走既有 D4-D7 链路。本案不改结构放置机制，也不因此排斥其他地形 mod。

## 验收

1. 只采样目标 realm 的 owned cell，且每格恰好一次，负坐标和领地空洞不偏移。
2. RTF 0.0.5 / 0.0.6 API 都能产生高度、水体、terrain/source biome；未激活时可回退并保留原因。
3. 不生成 chunk；粗览样本数等于 owned cell 数。
4. 证据参与 Patch Explorer source identity，变化后旧 selection 进入 stale。
5. T2 和 City D4 没有粗地形证据时行为不变。
6. T4 选择仍必须经过 D3 `city_d3_site_review`，不得直接进入 D4。
7. W 与 T4 的开关可独立关闭，关闭后 provider provenance 明确记录回退，且 W 缓存不能与 RTF 快路径互相命中。
8. 半径 32768 验收中 `tiles/` 不出现 `debug_<region>` 目录，不生成逐 tile PNG；最终世界级预览仍完整存在。
