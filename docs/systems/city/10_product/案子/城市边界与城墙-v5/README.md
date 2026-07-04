# City 案子：城市边界与城墙 v5

## 状态

草案。本文先只记录一个最小流程口径，后续由人工继续掌控细化。

v5 的核心目标不是继续让城墙系统在 D7 后重新找路，而是把职责拆清：

```text
D5 决定城墙平面与 mask
  -> worldgen 尊重 mask 并记录真实地表
  -> D7 确认结构真实落地
  -> 城墙只按真实地表调整高度并决定是否落地
```

## 核心原则

1. **D5 定平面**
   - 城墙的 XZ 线路、corridor、门的大致位置和预留 mask 在 D5 决定。
   - D5 输出的 wall reservation 是后续阶段的平面权威。

2. **worldgen 保护 corridor**
   - D5 激活后，城墙 corridor 应进入生成期抑制。
   - 树、植被、散点地物、非城市结构和 RoadWeaver roadside 小结构不应抢占城墙 corridor。
   - 基础地形、水体和城市 planned structure 本身不因城墙 mask 被取消。

3. **生成期记录地表**
   - chunk 生成或加载到可确认状态时，记录地表摘要。
   - 只记录地表，不记录完整三维 block。
   - 正式缓存优先使用二进制 `.dat`；JSON 只做小范围调试导出。

4. **D7 后不再改线**
   - D7 后城墙不重新绕路、不做大幅 contour shift、不根据 patch 临时改变 XZ 线路。
   - 城墙执行只做垂直适配：高度、台阶、地基、门楼、烽火台落点、是否跳过。

## v5 主流程

### 1. D5：决定平面

D5 是城墙平面的最后决策点。

这一阶段决定：

- 城墙大致围哪里。
- 墙线走哪条 XZ 路径。
- 城门 / 过路口大概在哪里。
- 哪些 corridor 需要在生成期被保护。
- 哪些节点可以尝试放烽火台 / 门楼。

D5 之后，后续阶段不再重新寻找城市边界。

D5 可以参考 D3 patch，但 **不能把 patch 边界当最终墙线**。patch 的职责是告诉系统“这里大概是什么地貌、哪里需要补扫、哪里可能有水体 / 坡地 / 山脊”，不是替代真实墙线。

### 1.1 D4 / D5 覆盖检查

D4 选完结构落点后，系统已经知道结构的 `plannedFootprint`、结构 profile envelope 和候选 source patch。D5 必须用这些信息先做 coverage check：

- `plannedFootprint`
- `reservedEnvelope`
- `collisionEnvelope`
- 预计 wall breathing room
- 预计 gate / tower footprint
- 必要的 corridor margin

如果这些范围贴近 D3 review package / patch scan 边界，D5 不应继续生成不完整墙线，而应要求补扫对应 patch / block 区域。

D6 才能锁定更接近真实生成结果的 `lockedActualFootprint` / `lockedCollisionEnvelope`。因此 v5 的规则是：

- D5 先用 D4 planned footprint 和 envelope 保证“规划覆盖足够大”。
- D6 锁定 actual footprint 后，如果超出 D5 覆盖范围，必须回到 D5 扩大覆盖并重算 reservation。
- 不允许在 D7 后因为发现冲突再临时移动墙线。

### 2. execute_d5：激活生成期保护

execute_d5 只负责把 D5 的决定注册到运行时。

生成期需要知道：

- 这里未来要放墙，不要长树、地物、小结构。
- 这里是 gate corridor，道路可以通过。
- 这里是 planned city structure，允许城市结构生成。

这一步不真实放墙，只是保护未来城墙空间。

### 3. worldgen：尊重 mask，并记录真实地表

玩家 TP / 新 chunk 生成时，worldgen 按 D5 mask 运行：

- 城市结构正常生成。
- 植被、地物、非城市结构避开城墙 corridor。
- 道路只在允许的 gate corridor 穿越墙线。
- 生成期或 chunk 可确认后记录真实地表摘要。

地表记录只服务后续落墙，不反过来改 D5 墙线。

v5 城墙最终落地必须使用 **1 block 级地表数据**，不能再用 16-block D3 cell 作为最终落墙依据。D3 cell 只保留为前期语义 / 覆盖检查参考。

### 4. D7：确认真实世界

D7 只确认 reality：

- planned structure 是否真的生成。
- 实际 footprint / ledger 是否完整。
- surface cache 或真实地表是否可用于落墙。

D7 不重新设计城墙。

### 5. 城墙执行：只做垂直适配

城墙执行阶段读取 D5 墙线和真实地表，只判断如何落地：

- 平地：直接放墙。
- 普通起伏：按中位数高度放墙并补地基。
- 凸起：墙接到凸起地面 / 山体上。
- 凹陷 / 大坑：只在 wall corridor 内填水平地板 / 台基。
- 连续水体：不落连续城墙，标记天然水体边界。
- 保护冲突：跳过并记录原因。

这一步不改路、不改线、不为了节点成功而绕开。

## 实现备注

以下细节由实现侧掌控，除非它们改变上面的流程口径。

### Surface Cache

采用 **region 文件 + chunk bitmap**。

路径建议：

```text
surface_cache/v0/<dimension>/r.<regionX>.<regionZ>.dat
```

一个文件对应 32x32 chunks，也就是 512x512 block columns。文件内维护 chunk bitmap，只有已生成 / 已确认的 chunk 才写 sample。这样避免每个 chunk 一个小文件，也避免整张世界一个大文件。

每个 x/z block column 记录一条地表摘要：

```text
surfaceY
topBlock palette id
fluid flags
biome palette id
temperature quantized
flags
```

用途：

- 墙体 corridor 的真实高度采样。
- 水边 / 液体判断。
- 烽火台 5x5 / 7x7 落点检查。
- 门楼范围的平整度与通道判断。
- 调试图和现场 TP 复核。

缺缓存时可以 fallback 到 `ServerLevel` 现读，但现读不应改变城墙平面。

### D5 Wall Reservation

D5 输出 `wall_reservation_plan.v5`，作为后续平面权威。

最小字段：

```text
schemaVersion = city_wall_reservation_plan.v5
cityId
runId
dimensionId
authority = d5_wall_plane_authority
wallLine[]              # 有序 XZ 中心线 / 节点
wallCorridorMask        # block 坐标 corridor，不能只存 D3 cell
gateSlots[]             # D5 决定的大致 gate / road crossing 保留区
wallNodeSlots[]         # 可选：烽火台 / 角点 / 长墙间隔候选点
maskChannels
fingerprint             # execute_d5、worldgen hook、城墙执行共同校验
```

`maskChannels` 至少包含：

```text
noVegetation
noSurfaceFeature
noRoadsideStructure
noVanillaStructure
wallCorridor
gateCorridor
plannedCityStructureAllowlist
```

D7 后城墙执行必须读取并服从这个 reservation。缺少匹配 fingerprint 时，不允许用旧 D3 patch 临时重算一条新墙线。

### Worldgen Mask 查询

worldgen 抑制 hook 不按整座城市大范围查询，只按即将生成对象的 footprint 查询 mask。

查询规则：

- 树、花草、石堆等 surface feature：用 feature footprint / trunk footprint 与 `wallCorridor` 相交判断。
- RoadWeaver roadside 小结构：用结构 bbox 与 `wallCorridor` / `gateCorridor` 相交判断。
- vanilla / 第三方结构 start：用 structure bbox 查询 `noVanillaStructure`。
- 城市 planned structure：在 `plannedCityStructureAllowlist` 中则允许生成。
- 道路穿越 gate：只能落在 `gateCorridor`，不能因为碰到 `wallCorridor` 就被误删。

查询 margin 使用对象自己的 bbox 加小安全边：

```text
maskQueryPaddingBlocks = 2
```

不为避免个别 feature 而扩大或移动城墙 corridor。

## 城墙执行口径

```text
读取 city_wall_plan / wall reservation
读取 surface cache 或 ServerLevel surface
按 D5 wall line 切 placement units
每个 unit 只判断垂直适配：
  - 平墙
  - 阶梯墙
  - 地基
  - 门 / 门楼
  - 烽火台
  - 太陡 / 水体 / mask 冲突则跳过并记录原因
写 placement report
```

## 高度策略

墙体高度使用 **中位数**，不使用平均值。

目标是尽量让同一段墙的顶部高度接近：

```text
wallTopY = median(surfaceY samples) + nominalWallHeight
```

每个 placement unit 先取 corridor 内地表 sample 的中位数，得到 `unitMedianSurfaceY`。墙体按这个中位数落基准，再让墙顶尽量贴近同一个 `wallTopY`。

处理规则：

- 普通起伏：以 `unitMedianSurfaceY` 为基准放墙，逐列补 foundation。
- 凸起地形：不削山、不改线；墙体直接接到凸起地面 / 山体上，必要时变短或形成嵌入感。
- 凹陷 / 大坑：不按平均值把整段拉低；在 wall corridor 内填一个水平地板 / 台基到 `unitMedianSurfaceY`，再放墙。
- 连续水体：不落连续城墙，标记为天然水体边界。
- 零散小水坑：按普通凹陷处理或记录为局部 fill，不能因此改线。

推荐 reason code：

```text
WALL_PLACED_MEDIAN_HEIGHT
WALL_CONNECTED_TO_RAISED_GROUND
WALL_PIT_FLOOR_FILLED
NATURAL_WATER_BOUNDARY_NO_WALL
WALL_SKIPPED_PROTECTED_MASK
```

## 烽火台 / 门楼失败降级

节点失败主要来自三类：

- footprint 与结构、道路、gate corridor 或其他保护 mask 冲突。
- 5x5 / 7x7 footprint 内地表落差过大，无法形成可站立内部空间。
- 连续水体或天然边界，不适合放独立节点。

v5 不为了节点成功而改线。

降级规则：

- 烽火台失败：能按同一段墙线放普通墙就降级为普通墙；普通墙也不适合就不放。
- 门楼失败：如果这里是真实 gate corridor，保留门洞 / 简单开口，不用门楼强行封路；如果不是必须 gate，则降级为普通墙。
- 任何降级都写入 report，不能静默变成新路径。

## 不做

- 不在 D7 后重新生成城市边界。
- 不让城墙执行阶段改道路。
- 不让城墙执行阶段把墙线推开避结构。
- 不继续依赖 16-block D3 cell 来决定最终落墙。
- 不记录完整三维 block 缓存。

## 待人工继续定

- `nominalWallHeight`、大坑填平台阈值、连续水体判定阈值。
- 连续水体边界未来是否需要码头 / 防波堤 / 木栅栏等表现。
- 门楼失败时的简单开口是否需要独立美术模板。
