# City 案子：通用装饰阵列系统 v0.2

## 一、目的：

1、业务算法写死问题修复：

- 农田、花园、院落、路边等用途不再对应独立算法。
- 功能用途只作为 `Shape + Pattern + Content` 的组合结果，同一算法替换内容后必须可表达不同用途。

2、通用装饰能力建设：

- 支持像印章工具一样，在空地或整个 patch 内刷入花草、石子地、农田、水渠、围栏和小型 prefab。
- AI 只选择目标区域、形状、排列、注册内容和策略，不手写 block 坐标或任意 block operation。

3、真实地形适配：

- Patch 只提供 chunk / cell 级规划范围、地貌语义和粗方向，不直接作为 block 级刷入结果。
- Worldgen 按 chunk 读取真实高度、水体、地表和占用，逐格裁剪、降级或跳过。

4、旧版错误口径退场：

- v0.1 七种业务 item schema 破坏性退场，不自动转换成 v0.2。
- v0.2 只接受 `DecorationProgram` 判别联合，禁止继续扩展 `formal_axis_garden`、`parcel_fields` 等业务分支。

## 二、方案：

1、首期交付范围：

- `Shape`：`target_mask`、`rectangle`、`ellipse`、`ring`、`polygon`；圆形是 U/V 半径相等的 ellipse。
- `Pattern`：`uniform_fill`、`cross_section_repeat`、`parallel_rows`、`edge_repeat`、`grid_repeat`、`deterministic_scatter`。
- `Content`：`content_index.json` 注册的无实体 prefab；农田、水渠和石路首期也用 1x1 / 1xN tile NBT，surface catalog / block palette 配置化放第二切片。
- `TargetArea`：首期只接受 D3 patch 引用。AI-facing 禁止 `targetBounds/memberBounds`；纯几何测试直接使用 compiled fixture。
- `path_buffer`、`path_follow`、放射、复杂台地改造和跨 chunk 大 prefab 后续再做，不进入首期验收。

2、顶层计划：

```json
{
  "schemaVersion": "city_decoration_program_plan.v0.2",
  "cityId": "city_test",
  "catalogHash": "sha256:...",
  "styleProfileId": "forest_village",
  "styleProfileHash": "sha256:...",
  "programs": []
}
```

- 程序读取 `config/geomantia/city_decoration/content_index.json`、`templates/*.nbt` 和 `styles/*.json`。内容目录登记可落地的 prefab；风格档案把 AI-facing 语义键映射到一个或多个 prefab 变体。
- 运行时 `config/geomantia/city_decoration/` 是唯一真值。首次 `city_query_decoration_catalog` 发现该根目录不存在时，才安装打包基础目录：`content_index.json`、`styles/medieval_coastal.json` 和 4 个有效 NBT 模板；根目录已存在时绝不覆盖、合并或修复其中任何文件，后续只按现有 config 校验。
- 基础 `medieval_coastal` 必须提供 `crop_tile`、`water_channel_tile`、`field_border`、`gravel_path_tile` 四个语义映射；AI 仍只使用这些语义键，不感知模板文件名。
- AI 的 `contentRef` 是语义键，如 `market_stall`、`crop_tile`、`flower_ground_cover`，不是 `geomantia:oak_market_stall_a` 或 NBT 文件名；规划时按 `styleProfileId` 解析为具体内容与权重，compiled plan 不保留语义键。
- 规划开始时冻结规范化内容目录的 `catalogHash` 与所选风格档案的 `styleProfileHash`；intent、compiled plan、completion 和 active plan 必须携带二者。
- 激活或 worldgen 执行时任一 hash 与当前配置不一致，分别返回 `CITY_DECORATION_CATALOG_HASH_MISMATCH` 或 `CITY_DECORATION_STYLE_PROFILE_HASH_MISMATCH`，不得换素材后静默继续。

3、`DecorationProgram` 契约：

```json
{
  "schemaVersion": "city_decoration_program.v0.2",
  "programId": "farm_west_01",
  "targetArea": {
    "sourceType": "patch",
    "ref": "patch_12",
    "insetBlocks": 1
  },
  "coordinateFrame": {
    "originMode": "target_centroid",
    "orientationMode": "patch_long_axis",
    "quarterTurns": 0,
    "offsetUBlocks": 0,
    "offsetVBlocks": 0
  },
  "shape": {"type": "target_mask", "params": {}},
  "pattern": {"type": "uniform_fill", "params": {"paletteSlotId": "ground"}},
  "contentPalette": {},
  "terrainPolicy": {},
  "conflictPolicy": {},
  "priority": 20,
  "seed": 4815162342
}
```

- 上述是 AI-facing `DecorationProgram` intent；程序必须先把 target 引用和方向策略编译成 resolved target member bounds、世界原点和正交 U/V 轴，再交给几何引擎 / worldgen。
- `programId + seed + compiled coordinateFrame` 固定全局构图；禁止按 chunk 重新取原点、方向或随机种子。
- 含 `offsetBlocks` / `offsetUBlocks` / `offsetVBlocks` 的 Pattern，以 Shape 在对应局部轴的起始边界为 phase 0；`offset` 是相对此边界的位移，禁止以 coordinateFrame 原点或 chunk 边界重新起相。
- `targetArea.sourceType` 首期只接受 `patch`。
- AI-facing 请求出现 `targetBounds`、`memberBounds`、世界 `origin/x/z` 时 hard fail；array zone / dressing mask 引用放后续切片。

4、`Shape` 判别联合：

```json
{
  "type": "ring",
  "params": {
    "centerU": 0,
    "centerV": 0,
    "innerRadiusU": 8,
    "innerRadiusV": 8,
    "outerRadiusU": 16,
    "outerRadiusV": 16
  }
}
```

- `target_mask.params`：空对象。
- `rectangle.params`：`minU`、`minV`、`maxU`、`maxV`。
- `ellipse.params`：`centerU`、`centerV`、`radiusU`、`radiusV`。
- `ring.params`：`centerU`、`centerV`、`innerRadiusU/V`、`outerRadiusU/V`。
- `polygon.params`：至少三个局部 `vertices[{u,v}]`。
- AI-facing Shape 只接受 `type + params`；跨类型字段返回 `CITY_DECORATION_SHAPE_FIELD_UNSUPPORTED`。
- 所有 Shape 只生成候选区域，必须与 target member cells、有效 mask 和真实地形再次求交。

5、`Pattern` 判别联合：

```json
{
  "type": "cross_section_repeat",
  "params": {
    "axis": "u",
    "offsetBlocks": 0,
    "bands": [
      {"paletteSlotId": "fence", "widthBlocks": 1},
      {"paletteSlotId": "crop", "widthBlocks": 5},
      {"paletteSlotId": "water", "widthBlocks": 1},
      {"paletteSlotId": "crop", "widthBlocks": 5},
      {"paletteSlotId": "fence", "widthBlocks": 1}
    ]
  }
}
```

- `uniform_fill`：`paletteSlotId`。
- `cross_section_repeat`：`axis=u|v`、`offsetBlocks`、`bands[{paletteSlotId,widthBlocks}]`。
- `parallel_rows`：`axis`、`paletteSlotId`、`rowWidthBlocks`、`spacingBlocks`、`offsetBlocks`。
- `edge_repeat`：`paletteSlotId`、`spacingBlocks`、`offsetBlocks`。
- `grid_repeat`：`paletteSlotId`、`spacingUBlocks`、`spacingVBlocks`、`offsetUBlocks`、`offsetVBlocks`。
- `deterministic_scatter`：`paletteSlotId`、`cellSizeBlocks`、`densityPermille`。
- AI-facing Pattern 只接受 `type + params`；跨类型字段返回 `CITY_DECORATION_PATTERN_FIELD_UNSUPPORTED`。
- `cross_section_repeat`、`parallel_rows` 与 `grid_repeat` 的 offset 统一按 Shape 局部最小边界计相位；同一程序跨 chunk 后必须保留同一条连续 band，不得在 chunk 边缘重启。
- 农田只是一条 `cross_section_repeat` 配置，不新增 `parcel_fields` 算法；圆形花园只组合 `ellipse/ring + uniform_fill/edge_repeat`。

6、`ContentPalette` 与素材契约：

```json
{
  "slots": [
    {
      "slotId": "crop",
      "phase": "skeleton",
      "entries": [
        {"contentRef": "crop_tile", "weight": 3},
        {"contentRef": "gravel_path_tile", "weight": 1}
      ],
      "required": true
    }
  ]
}
```

- 首期 `Content` 只接受 `contentKind=prefab` 和 config `nbtFile`；`contentKind=surface` / block palette 属于第二切片。
- `content_index.json` 只登记具体 prefab；`styles/<styleProfileId>.json` 以 `semanticRef -> variants[{contentRef,weight}]` 映射到 catalog 内容。一个语义键可映射多个同风格变体，语义权重与变体权重相乘后写入 compiled plan。
- `styleProfileId`、`styleProfileHash` 和语义 `contentRef` 缺失、过期或未映射均 hard fail；不得回退第一件模板或草方块。
- `content_index.json` 首期只登记 prefab，允许字段为 `contentId`、`contentKind=prefab`、`nbtFile=templates/*.nbt`、`placementMode`、`allowedRotations`（角度）、`supportMode=full_footprint`、`replacePolicy`、`maxFootprintHeightSpreadBlocks`、`comfortMarginBlocks`、allowed / blocked surface tags 和 tags；size / envelope 从 NBT 派生，配置不得覆盖。
- `placementMode=above_surface` 只允许 `replacePolicy=replaceable_only`，用于摊位、栅栏、灯具等放在地表上方的 prefab。
- `placementMode=replace_surface` 只允许 `replacePolicy=surface_replaceable`，用于 `farmland_wheat_tile`、`water_channel_tile`、`gravel_path_tile` 等替换地表的 1x1 / 1xN tile。
- 非法组合在 catalog load 阶段 hard fail；AI 仍只引用 `contentRef`，不得覆盖 placementMode 或 replacePolicy。
- 农田、水渠、石路等地表内容首期注册为 `geomantia:prefab/*_tile` 的 1x1 / 1xN NBT；AI 仍只提交 `contentRef`。
- prefab 只读取 `templates/*.nbt` 的方块 palette / blocks；禁止携带或落地实体 NBT，`entities[]` 非空时返回 `CITY_DECORATION_PREFAB_ENTITY_NBT_FORBIDDEN`。
- AI 只能提交语义 `contentRef + weight`，不得内联具体 content id、block state、NBT 路径或 block operation。

7、地形与冲突策略：

```json
{
  "terrainPolicy": {
    "maxSlopeDelta": 1,
    "allowWater": false,
    "invalidTerrainAction": "clip"
  },
  "conflictPolicy": {
    "onConflict": "skip",
    "clearanceBlocks": 1
  }
}
```

- 地表内容可逐格贴地；多方块 prefab 必须先采样完整 footprint，再使用统一 datum 整体放置。
- prefab footprint 高差超过阈值时整体跳过或降级，禁止每列独立贴地造成模板变形。
- `invalidTerrainAction` 只接受 `skip|clip`；`onConflict` 只接受 `skip|replace_lower_priority`。
- 结构、墙体、城门和道路始终优先于装饰；`replace_lower_priority` 只允许替换低优先级装饰。已接受槽位必须写入局部 occupied field。

8、两阶段执行：

- 规划阶段解析 target、固定坐标系和种子、校验判别联合、冻结 content / style hash，先保留规范化语义 intent，再输出只含具体内容的 compiled program、slot projection、planning trace、style resolution trace、quality report 和意图预览。
- 规划 artifact 固定写入 `city_decoration_<citySeedId>/`：`city_decoration_program_plan.json`、`city_decoration_compiled_program_plan.json`、`city_decoration_slot_projection.json`、`city_decoration_planning_trace.json`、`city_decoration_style_resolution.json`、`quality_report.json`、`city_decoration_preview_index.json` 和 `city_decoration_preview_<programId>.png`。
- 全部规划产物成功写完后，最后发布 `city_decoration_planning_complete.json`；schema 为 `city_decoration_planning_complete.v0.2`，含 `cityId`、`catalogHash`、`styleProfileId`、`styleProfileHash`、`completedAt`。workflow 只以该标记判断 `skipExisting`，不得以 compiled 文件存在替代完成态。
- v0.2 active plan 保存全局程序；预展开的 surface operation / placement 只能作为调试产物，不是运行时真值。
- `city_execute_d5` 要求 compiled plan 与 planning completion 同时存在；只存在一个时返回 `CITY_DECORATION_PLAN_INCOMPLETE`。提交结构 registry 前必须无副作用预检 server active decoration plans、catalog 和 ledger；两者均不存在时按 dimension + city 注销旧 active decoration plan，禁止沿用上次装饰。
- Worldgen 由 feature origin 所属 owner chunk 触发；一次只能编译、预检并写入该 owner 的 fragment，禁止从 `WorldGenRegion` 向其他 owner chunk 写方块。
- 当前 owner 的 READY fragment 必须在当前 feature 回调继续前登记 `suppressionBounds`；D5 activation 必须发生在目标 chunk 首次生成前，防止树、草和花先占用装饰目标。
- 当前 owner 的 target state 不可用或预检失败时，只延后该 fragment；其他 owner 在各自回调按同一 `programId + seed + coordinateFrame` 继续落地和记 ledger。无 configured feature 的 owner chunk 仍是单列已知限制。
- 每个 chunk 使用同一世界坐标公式和种子；跨 chunk 行列、圆环和边界不得断线、错位、重复或在 chunk 边缘重启。
- ledger 键至少包含 `dimensionId + cityId + programId + catalogHash + chunkX + chunkZ + fragmentId`，避免重入和版本串用。
- active 文件固定为 server-root `geomantia_city_masks/active_city_decoration_program_plans.json`，schema 为 `city_active_decoration_program_plans.v0.2`；ledger 固定为同目录 `city_decoration_worldgen_ledger.json`，schema 为 `city_decoration_worldgen_ledger.v0.2`。
- 首期 worldgen 仍由 `ConfiguredFeature.place` mixin 触发 decoration registry；registry 执行后用 `suppressionBounds` 抑制同范围后续植被 feature。
- 这是首期限制，不是已解决的可靠 chunk 生命周期 hook：若某个 chunk 没有任何 configured feature 调用，装饰可能漏执行。真实验收必须专门覆盖无 feature chunk；未验证前不得声称所有 chunk 必达。

9、activation 前地形探针：

- `city_probe_decoration_terrain` 只读取已编译的 plan 与 slot projection；二者的 projection schema、cityId 或 catalogHash 不一致时拒绝探针，不得猜测或重建槽位。
- 探针只读取当前已加载的真实区块：不得申请 ticket、同步加载或生成 chunk，不得调用 worldgen、placer、registry、ledger 或任何世界写入，也不写 artifact；结果只在接口响应中返回。
- 每个 program 与 palette slot 至少输出 projected / sampled / loaded / unavailable 数量、coverage、已采样高度范围和相邻槽位最大高差；线性 pattern 的每个 palette slot 额外输出通用 `continuousBandProfiles[]`。profile 定位 `paletteSlotId`、延伸轴、预期/已加载/未加载连续对数量、最大邻接高差、连续已加载段数量和 reason code；水渠只是调用方解释该 profile 的一种配置。
- 未加载覆盖必须显式保留为 unknown，不能按 D3 平均高度、空槽或“可放置”补值；响应以 `activationRecommendation=ready_for_activation|review_terrain_before_activation|await_chunk_load|no_projected_slots` 说明当前人工判断依据。
- 探针是 activation 前人工审阅的证据，不修改 active plan，也不替代 activation 后 worldgen 对地表、水体、硬占用和 prefab footprint 的逐格复核。`ready_for_activation` 也不是自动 activation 授权。

10、v0.1 破坏性退场：

- `city_dressing_brush_plan.v0.1`、`dressingLayoutItems[]` 和七种业务 item schema 不进入 v0.2 planner。
- 同一请求不得同时提交 `decorationProgramPlan` 与 `dressingBrushPlan`；发现旧字段返回 `CITY_DRESSING_LEGACY_SCHEMA_REMOVED`。
- 不自动把 `formal_axis_garden`、`courtyard_dressing`、`roadside_edge` 等旧 item 转换为 v0.2，避免表面成功但构图语义变化。
- 旧 `city_dressing_<citySeedId>/` artifact、active plan 和 ledger 不得被 v0.2 静默读取；发现旧目录产物时显式拒绝，需要重跑规划和激活。

11、验收：

- 通用性：同一 `cross_section_repeat` 只替换 Content 即可表达农田带、花坛带和道路分隔带。
- 形状：`target_mask`、rectangle、ellipse、ring、polygon 结果连续可读，且不会把 patch envelope 当完整可刷矩形。
- 内容：未知语义键、未知具体 content、catalog / style hash 漂移、含实体 NBT prefab 均 hard fail；同一语义键可通过切换风格档案换皮而不改变 Program 构图。
- 地形：水体、陡坡、高差、结构、道路和城墙处正确裁剪或跳过；prefab 无逐列变形。
- 放置语义：farmland / path / water tile 替换地表，摊位 / 栅栏在统一 datum 上方放置；placementMode / replacePolicy 非法组合 hard fail。
- 跨 chunk：分 chunk 编译结果与同一范围整体编译一致，ledger 无漏刷、重复和旧版本串用。
- 触发限制：分别验证有 feature 和无 feature chunk；无 feature chunk 若未触发 registry 必须作为已知缺口记录，不得用其他 feature 场景代替通过。
- 预览：明确区分规划意图和 worldgen 实际结果，能显示 Shape、Pattern 槽位、裁剪与跳过原因。
- 地形探针：完整已加载区域能报告高度范围、邻接高差和长连续带；部分未加载时只报告已采样事实并明确覆盖缺口，绝不生成 chunk 或伪造地形。真实验收在人工审阅该响应后才允许决定是否 activation。
