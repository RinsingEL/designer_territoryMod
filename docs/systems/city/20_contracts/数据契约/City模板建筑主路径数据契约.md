# City 模板建筑主路径数据契约

## 定位与强制口径

本文是 City 固定模板建筑主路径的当前数据真值，覆盖 D2 模板目录、D4 placement plan、D5 active registry、worldgen 交接和 D7 ledger。

City active 主建筑只读取 `StructureTemplate` NBT 和本契约的模板目录，不查询外部 `Minecraft Registries.STRUCTURE`，不使用 Jigsaw pool。凡进入 City catalog 的模板，不分命名空间，目录模型与 D6 都必须把有效 `terrainPosePolicy` 归一为 `structure_start_beard_thin`，并创建 City 自有 `StructureStart`（同一 origin chunk 的多个建筑以多个 piece 共存） 以借用 `beard_thin` 地形适配。该 start 的 terrain-adaptation bbox 只供 Minecraft 内部使用，不能进入 D4-D7 几何、active registry、ledger 或预览。

D2、D4、D6、D7 对同一建筑必须保持以下 identity 完全一致：

```text
templateRef + templateHash + variant + rawSize + rotation + mirror + anchor
```

identity 或由它派生的 world footprint 漂移必须 hard fail。`terrainPosePolicy` 是 D4 -> D6 -> D5 -> worldgen 的冻结 lifecycle 快照，不能由旧 active registry 或运行时目录改写。旧 `structureId`、外部 configured structure、Jigsaw、外部 StructureStart、旧 profile bbox 和 bbox 外侧伪入口不得被静默转换。

## 作者语义权威

### 道路可选树结构

D6 在 D4 建筑及道路、D5 城墙预留冻结后追加内置树模板。资源来自 `geomantia:roadside/`，manifest 保存裁去展示地面后的尺寸、树根局部坐标与来源 hash；D6 仍读取当前世界 NBT 的实际 hash 和尺寸。树不参与建筑功能区推断，也不作为城区建设面的种子。

树条目使用 `placementRole=roadside_tree`、`placementGroupId=__roadside`、`blueprintPlacementPhase=FILL`，携带 `sourceRoadId` 和经过同一 rotation/mirror 变换的世界 `treeRootBlock`。其他 template identity、closed footprint、ownerChunks 和锁定规则沿用主路径。active registry 必须持久化这些字段，并在激活时将已锁定路树的 `maskEnvelope` 追加到运行时 `noVegetationMask` 与 `noVanillaStructureMask`，保护树结构免受后续自然生成覆盖；原始 D5 文件不回写。

`geomantia:roadside/` 模板冻结为 `terrainPosePolicy=structure_start_decoration`，通过 `geomantia:city_roadside_decoration` StructureStart 落地，`terrain_adaptation=none`，不执行建筑地基支撑。树根所在列的 generator base height 决定统一 datum，所有 owner chunk 共用持久化 datum。普通建筑继续使用 `structure_start_beard_thin`。

候选按完整旋转树冠范围计算路侧偏移和间距，避让所有建筑碰撞范围、道路净空、入口、城墙/城门/塔楼预留、景观 reservationSpans 及先前树结构；桥面、水体、陡坎、缺失地形及超出覆盖范围的候选跳过。可选树在 D6 元数据、碰撞或 chunk 状态预检失败时记 `skipped_optional`，累计 `optionalSkippedCount`，不解除主体建筑锁定；主体建筑失败仍按原规则处理。候选统计保存在 `sourceStructureAnchorMap.roadsideTreeReport`。

树不进入建筑模板目录的功能/风格选择；内置资源不替代该目录的作者审批约束。当前新增的是树结构，路灯继续沿用既有 SurfacePrint 能力。

结构的功能和风格必须由整合包作者在游戏开始前标注。模板目录的 `buildingSemantic/style` 与 TerraSense 画像的 `functionTerms/styleTerms` 都是作者配置，AI 只可据此选用、组合结构，不可根据名称或外观猜测并补写语义。

宿主正式规划入口校验所有可引用结构拥有 `reviewState=approved`、非空功能和风格词；未标注、未批准或引用不存在时，返回 `PLANNING_AUTHOR_ANNOTATION_REQUIRED` 并指出结构，停止规划等待作者修正。外观预览用于构图，不具备改写功能/风格标签的权力。NBT hash、rawSize、碰撞、入口等仍是独立的程序事实预检，不由语义标注代替。

## 版本与产物

| 产物 | schema | 作用 | 主要阶段 |
| --- | --- | --- | --- |
| 模板目录 | `city_template_catalog` | 登记模板 NBT、hash、变体、变换限制、道路入口和地形策略 | D2 |
| placement plan | `city_template_placement_plan.v0.1` | 冻结每个建筑的模板 identity、anchor、NBT size、派生 world footprint、碰撞范围和道路入口 | D4 / D6 |
| active template placement registry | `city_active_template_placement_registry.v0.1` | D5 -> worldgen 的 City 内部 active 交接 | D5 |
| server-root active registry collection | `city_active_template_placement_registries` | 同一存档内按城市保存多份 active registry；后续 D5 只替换同一 `cityId` | D5 / worldgen |
| placement ledger | `city_template_placement_ledger.v0.1` | 记录 worldgen NBT 放置、跳过、失败和实际 closed footprint，保证幂等 | worldgen / D7 |

`schema` 必须精确匹配。旧 `schemaVersion`、未知字段、缺失必填字段和静默降级均 hard fail；当前模板目录不承诺旧 Jigsaw 或 StructureStart artifact 兼容。

## 共同几何约定

### Anchor

`anchor` 是 transformed 模板 footprint 的最小角世界方块坐标，不是中心点，也不是道路外侧的辅助点：

```json
{"x": 1200, "y": 72, "z": -340}
```

- `anchor.x / anchor.z` 是 transformed footprint 的 `minX / minZ`。
- `anchor.y` 是模板放置 datum；模板高度从该 y 开始计算。
- D4 选择 anchor 后，D6、active registry、worldgen 和 D7 必须沿用同一 anchor。

### Half-open 与 closed bbox

- 模板 NBT 原始局部范围是 half-open：`[0,width) × [0,height) × [0,depth)`。
- `roadEntrances[].position` 的局部 `x / z` 必须落在 `[0,width) × [0,depth)`，越界即拒绝。
- transformed actual footprint、collision bbox、mask bbox、ledger actual footprint 对外统一表示为 closed block bounds，包含两端：`[minX..maxX] × [minY..maxY] × [minZ..maxZ]`。
- 对 transformed size `width × height × depth`，实际 world bbox 为：`min=anchor`、`maxX=anchor.x+width-1`、`maxY=anchor.y+height-1`、`maxZ=anchor.z+depth-1`。
- collision / mask 只能从 actual closed bbox 按声明的 clearance / mask margin 扩展；任何文档或 artifact 都不得把 half-open `maxExclusive` 当作 closed `max`。

### Rotation 与 mirror

City 的 rotation / mirror 名称和变换顺序与 Minecraft 1.20.1 `StructureTemplate` 原生语义一致：先 mirror，再围绕局部零点 rotation，最后把 transformed footprint 规范化到 `anchor=minX/minZ`。

- `LEFT_RIGHT` 翻转局部 Z 轴：`(x,z) -> (x, depth-1-z)`；入口 `NORTH/SOUTH` 互换。
- `FRONT_BACK` 翻转局部 X 轴：`(x,z) -> (width-1-x, z)`；入口 `EAST/WEST` 互换。
- `CLOCKWISE_90`：`(x,z) -> (depth-1-z, x)`。
- `CLOCKWISE_180`：`(x,z) -> (width-1-x, depth-1-z)`。
- `COUNTERCLOCKWISE_90`：`(x,z) -> (z, width-1-x)`。

worldgen runtime 必须使用数学等价的唯一适配：`getZeroPositionWithTransform(anchor, mirror, rotation)` 作为规范化后的实际 placement origin，`StructurePlaceSettings.rotationPivot` 固定为局部 `ZERO`。禁止把 `getZeroPositionWithTransform(...)` 的返回值再次设为 rotation pivot；该做法会叠加未被 D4/D6 计算的偏移。

运行时必须在写入前逐源坐标或用等价的可验证双射证明：Minecraft transformed footprint、City identity 派生 footprint、D6 `lockedActualFootprint` 和当前 owner fragment 完全一致。任一变换漂移必须 hard fail，不得以 `StructureTemplate.placeInWorld=true` 代替完整性证明。

本次轴语义修正不承诺兼容修复前的非 `NONE` mirror artifact。验收或继续执行前必须重新生成相关 D4/D6 plan 和 active registry；不得仅因 raw size、footprint 尺寸或 template hash 未变就把旧 artifact 作为通过证据。

通用 `BlockBounds` 字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `minX` / `minY` / `minZ` | int | 是 | 包含的最小方块坐标 |
| `maxX` / `maxY` / `maxZ` | int | 是 | 包含的最大方块坐标，必须不小于对应 min |
| `convention` | string | 是 | 固定为 `closed_inclusive_blocks` |

## 带 Jigsaw 独栋模板的离线清洗契约

City 运行时仍不执行 Jigsaw。对于人工从模组资源中收集、视觉与功能上已经能够独立成立，但 NBT 内仍保留 connector 的模板，只允许先经过 `tools/city_templates/jigsaw_template_sanitizer.py` 离线清洗，再作为普通固定 NBT 进入模板目录。

该工具使用三个独立产物：

| 产物 | schemaVersion | 作用 |
| --- | --- | --- |
| 审计报告 | `city_standalone_jigsaw_audit.v0.1` | 只读列出源 hash、rawSize、实体数和每个 Jigsaw 的位置、方向、pool、target、`final_state`；同时给出待人工确认的道路入口候选。 |
| 审核 manifest | `city_standalone_jigsaw_sanitize_manifest.v0.1` | 冻结 `sourceFile`、`sourceSha256`、`targetRef`、`expectedJigsawCount`、`connectorPolicy` 和人工 `standaloneConfirmed`。 |
| 清洗报告 | `city_standalone_jigsaw_sanitize_report.v0.1` | 记录输出 hash、rawSize、替换数量、剩余数量、实体数、入口候选和实际写入状态。 |

准入规则：

1. 审计只提供事实，不根据文件名、pool 名或建筑外观自动断言独栋。
2. manifest 草稿中的 `standaloneConfirmed` 固定为 `false`；只有人工确认完整建筑后才能改为 `true`。
3. 首版唯一允许的 `connectorPolicy` 是 `replace_all_with_final_state`。每个 Jigsaw 必须使用自身可解析的 `final_state` 替换，不能统一猜成 air。
4. 源 SHA-256 或 Jigsaw 数量与审核 manifest 不一致时整项 hard fail；任一 `final_state` 非法、Jigsaw 坐标越界或重复时拒绝。
5. 输出模板必须满足 `remainingJigsawCount=0`。未确认条目只记为 skipped，不得写入输出目录。
6. 水平 connector 可生成局部 `position{x,z}`、方向和边界距离候选，但 `confirmationRequired=true`；它不是正式 `roadEntrances[]`，仍需结合门、门洞或道路接面人工确认。
7. 通用清洗器只报告实体，不改写实体；City active worldgen 本身使用 `ignoreEntities=true`。需要清实体或烘焙 processor 的来源，必须另有显式、可回归的来源适配器。
8. 真正依赖子 pool 才能完整的屋顶、房间、走廊、墙段和多-piece 组装系统不得通过本契约伪装成独栋模板。

清洗输出采用 datapack 目录 `data/<namespace>/structures/<path>.nbt`。服务端 reload 后仍必须通过 `city_query_template_metadata` 回读当前 `StructureTemplateManager` 的 hash 与 rawSize，离线报告不能直接充当正式模板目录。

## 模板目录 `city_template_catalog`

顶层必填字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schema` | string | 是 | 固定为 `city_template_catalog` |
| `templates[]` | object[] | 是 | 不得为空；`templateRef + variant` 唯一 |

每个 `templates[]` 条目必填：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `buildingSemantic` | string | AI-facing 建筑语义；不是 City 自建功能枚举 |
| `style` | string | 风格键 |
| `templateRef` | string | Minecraft resource location，指向可由 `StructureTemplateManager` 读取的 NBT |
| `templateHash` | string | 模板内容的稳定 hash；推荐 lowercase SHA-256，禁止空值 |
| `variant` | string | 模板变体；与 `templateRef` 共同唯一 |
| `rawSize` | object | `{width,height,depth}`，三者均为正整数，来自 NBT |
| `allowedRotations[]` | string[] | `NONE`、`CLOCKWISE_90`、`CLOCKWISE_180`、`COUNTERCLOCKWISE_90` 中的非空子集 |
| `allowedMirrors[]` | string[] | `NONE`、`LEFT_RIGHT`、`FRONT_BACK` 中的非空子集 |
| `roadEntrances[]` | object[] | 模板局部道路入口；每项含 `entranceId`、`position{x,z}`、`direction` |
| `terrainPosePolicy` | string | 模板地形姿态策略，也是 placement lifecycle 配置；所有 City catalog 模板无条件归一为 `structure_start_beard_thin`，不存在 direct-template 分支 |
| `supportPolicy` | string | 支撑 / 基础策略 |

`clearanceBlocks` 已废弃，不再必填；旧目录可保留该字段，但执行统一按 0 处理。新编译的 collision bbox 等于 actual footprint，不附加模板安全距离。布局间距、道路宽度和软地块余量保持独立；历史冻结产物不自动重排。

目录 loader 必须从 NBT 重新确认 `rawSize` 和 `templateHash`。配置不能覆盖 NBT 尺寸，不能把 `nbtFile`、`structureId` 或 TerraSense 静态 footprint 当作 `templateRef` 的兼容别名。

可选作者字段 `groundPlaneY`：

- 模板局部外部地表上边界（脚底）的整数 Y，严格满足 `0 <= groundPlaneY < rawSize.height`。与室内地坪、入口台阶、门槛高度分别记录，不从道路入口推断。
- 新放置统一以 `templateOriginY = surfaceFirstFreeY - groundPlaneY` 计算原点。显式 `0` 有效并覆盖旧推断；字段缺失时兼容已有 NBT 边界土层推断，不能把缺失默认序列化为 0。
- 非整数、字符串、布尔值、显式 null 及越界值返回 `CITY_TEMPLATE_GROUND_PLANE_INVALID`。旋转、镜像只改变 XZ，不改变该字段。
- 此字段属于作者目录元数据，随 D4 候选、阵列 placement plan、D6 `plannedWorldgenStructures` / `structureTemplate`、active registry 和 ledger 保存。D7 同时检查字段存在性和值；不能以相同 NBT hash 忽略地面声明漂移。
- 世界已经持久化的 `templateDatumY` 是放置原点，所有后续分片继续复用，不重新扣除 groundPlaneY，也不因新目录元数据移动已有 StructureStart。
- 不写入原版 StructureTemplate NBT 的未知根字段；目录变更须重新计算内容包 catalogSha256 并正式生成新 Context，不手改旧冻结产物。

可选作者字段 `frontagePolicy`：

- `FIXED_FRONT`（省略时默认）：保持原规则，显式 `frontageEntranceId` 优先，其次唯一命名为 `front` 的入口，再其次唯一入口；其余多入口素材需要明确正面，不自动猜测。
- `ANY_AUTHORED_ENTRANCE`（无固定正面）：作者允许程序从已标注 `roadEntrances[]` 中择优朝向道路/设计目标。显式 `frontageEntranceId` 或命名主入口 `front` 仍优先；无此指定时，每个允许旋转只选一个最佳入口，方向对齐同分按入口 ID 排序，旋转同分保持作者配置顺序。不增加旋转、镜像或新入口。
- 未知值、非字符串、显式 null，以及无入口却声明 `ANY_AUTHORED_ENTRANCE` 均返回 `CITY_TEMPLATE_CATALOG_FRONTAGE_POLICY_INVALID`。多入口本身不是无固定正面的授权。
- 该字段归整合包作者所有，随完整模板目录冻结进 D4 snapshot 并参与 Context hash；AI 不可在蓝图中改写。配置改变后须正式重建受影响 Context/编译产物，不能直接改旧冻结文件。只改该语义不改变 NBT 内容 hash，但内容包 `catalogSha256` 必须按新目录字节更新。
- 配置示例：四向喷泉经作者确认可添加 `"frontagePolicy": "ANY_AUTHORED_ENTRANCE"`。普通房屋、城门等不能仅因存在多个门就批量添加。

目录条目示例：

```json
{
  "schema": "city_template_catalog",
  "templates": [
    {
      "buildingSemantic": "market",
      "style": "coastal_medieval",
      "templateRef": "geomantia:city/market_a",
      "templateHash": "sha256:0123456789abcdef...",
      "variant": "a",
      "rawSize": {"width": 10, "height": 8, "depth": 12},
      "allowedRotations": ["NONE", "CLOCKWISE_90"],
      "allowedMirrors": ["NONE"],
      "roadEntrances": [
        {"entranceId": "front", "position": {"x": 4, "z": 11}, "direction": "SOUTH"}
      ],
      "terrainPosePolicy": "structure_start_beard_thin",
      "supportPolicy": "full_footprint_support"
    }
  ]
}
```

## Placement plan `city_template_placement_plan.v0.1`

顶层必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | 固定为 `city_template_placement_plan.v0.1` |
| `runId` | string | 当前 City run |
| `cityId` | string | 城市 ID |
| `planId` | string | 本次 immutable placement plan ID |
| `placements[]` | object[] | 必填，可按设计顺序排列 |

每个 `placements[]` 必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `anchorId` | string | 本 plan 内唯一的建筑 anchor ID |
| `slotId` | string | D4 设计 slot 引用 |
| `templateRef` | string | 必须命中 catalog |
| `templateHash` | string | 必须与 catalog 和加载 NBT 一致 |
| `variant` | string | 必须命中 catalog |
| `rotation` | string | 必须在该变体 `allowedRotations[]` 内 |
| `mirror` | string | 必须在该变体 `allowedMirrors[]` 内 |
| `anchor` | object | D4/D6 为 `{x,z}`，transformed footprint 最小角；不得为采样 Y 而加载或生成目标 chunk |
| `templateSize` | object | `{width,height,depth}`；从已校验 NBT `rawSize` 原样带入，是 placement 的唯一局部矩形几何 |
| `actualFootprint` | object | D4/D6 的派生输出快照；由 `templateSize + rotation + mirror + anchor` 计算，closed bounds |
| `collisionEnvelope` / `maskEnvelope` | object | 从 `actualFootprint` 按 clearance / mask margin 派生，closed bounds |
| `roadEntrances[]` | object[] | transformed 入口；含 `entranceId`、`relativePosition{x,z}`、`worldPosition{x,y,z}`、`direction` |
| `terrainPosePolicy` | string | 从目录冻结；所有 City catalog 模板在目录模型和 D6 规划期强制归一为 `structure_start_beard_thin`，不得由 D4 item 或 worldgen 覆盖 |
| `templateDatumPolicy` | string | 固定为 `generator_base_height_motion_blocking_no_leaves`；不存在 direct-template datum policy |

`roadEntrances[]` 必须由目录局部入口按同一 rotation / mirror 变换并加 anchor 得到。City 自有道路使用 `worldPosition / direction` 选择真实接入点，禁止使用 `bbox + 外扩距离` 推导入口。`templateFootprint`、`bbox`、`footprint` 不是模板目录或阵列 item 的合法输入；它们不会作为另一套本地尺寸真值保存。

## Active registry `city_active_template_placement_registry.v0.1`

D5 可以写入 City 自己的 server-root active registry，作为 worldgen 交接。顶层必填：`schemaVersion`、`dimensionId`、`cityId`、`planId`、`activatedAt`、`placements[]`。每个 placement 必须原样保留 placement plan 的 identity、anchor、`templateSize`、`terrainPosePolicy`、`templateDatumPolicy` 和 transformed `roadEntrances[]`，并携带 D6 派生并锁定的 world footprint 快照，另外增加：

- `registryStatus=active`
- `worldgenSource=city_template_nbt`

每次 D5 产出的城市级 artifact 仍保持上述单城市 registry。server-root 持久化不得再用后一城市整体覆盖前一城市，而必须写入集合外壳 `city_active_template_placement_registries`：

```json
{
  "schema": "city_active_template_placement_registries",
  "registries": [
    {"schema": "city_active_template_placement_registry", "cityId": "city_a", "plannedStructures": []},
    {"schema": "city_active_template_placement_registry", "cityId": "city_b", "plannedStructures": []}
  ]
}
```

- `registries[]` 以 `cityId` 唯一；同城新 revision 原子替换旧项，不同城市必须共存。
- worldgen 按 owner chunk 在全部城市项中查询，ledger identity 仍使用 `runId + citySeedId + cityId + anchorId`。
- 不同城市可复用相同 `anchorId + templateRef + templateHash`；运行时 piece 查找还必须匹配冻结 `anchorBlock`，不得命中另一城市同名建筑。
- reservation mask 与模板 registry 必须以相同的多城市生命周期激活、持久化和重启恢复，不能只让 LandUse 多城共存。
- 读取旧的单城市 server-root 文件时允许将其提升为仅含一项的集合；这只迁移当前模板 active schema，不兼容 configured structure、Jigsaw 或其他退役输入。

模板 D6 item 的 lock 必须包含 `locked=true`、`templateId`、`templateRef`、`templateHash`、`variantId`、`rawSize`、`rotation`、`mirror`、`anchorBlock`、`actualFootprint`、`lockedActualFootprint`、`lockedCollisionEnvelope`、`maskEnvelope`、`ownerChunks[]`、`terrainPosePolicy` 和 `templateDatumPolicy`。D6 必须重新读取当前世界 NBT，并重新校验 hash、rawSize、变换、footprint、collision、mask 与 owner chunks。`pieceBoxes`、start signature、bbox group 和 envelope sample 均为非法旧字段；运行时单-piece start 的内部 bbox 不写回此 schema。worldgen 不能得到高于 `minBuildHeight` 的 generator datum 时必须失败，不能静默以世界最低高度放置。

## Placement ledger `city_template_placement_ledger.v0.1`

顶层必填：`schemaVersion`、`dimensionId`、`cityId`、`planId`、`entries[]`。每个 entry 必填：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `anchorId` | string | 对应 placement plan |
| `templateRef` | string | identity 原样回写 |
| `templateHash` | string | identity 原样回写 |
| `variant` / `rotation` / `mirror` | string | identity 原样回写 |
| `templateSize` | object | identity 原样回写；本地尺寸只能来自 D2 已校验 NBT |
| `chunk` | object | worldgen owner chunk，含 `x`、`z` |
| `templateDatumY` | int | `placed` 时必填；由 `MOTION_BLOCKING_NO_LEAVES(anchor.x,anchor.z)` 在 worldgen 回调中解析，必须高于 `minBuildHeight` |
| `status` | string | `pending`、`placed`、`skipped`、`failed` |
| `placementSource` | string | 固定为 `city_template_nbt_worldgen` |
| `actualFootprint` | object | `placed` 时必填；closed bounds，必须精确等于 identity 派生结果和 D6 `lockedActualFootprint` |
| `reasonCode` | string | `skipped` / `failed` 必填；成功可为 `TEMPLATE_PLACED` |
| `appliedAt` | string | `placed` / `skipped` / `failed` 的完成时间 |

ledger 幂等键为 `dimensionId + cityId + planId + anchorId + chunk`。重复 worldgen hook 不得重复放置或追加重复 entry；写 ledger 失败不得提前把 entry 标成 `placed`。D7 只汇总该 ledger，不反查 StructureStart，不调用 Jigsaw，不做 late paste。

D7 缺少整体完成记录时，按锁定 footprint 的所有 owner 检查区块状态与精确模板片段证据，不能只看 anchor chunk。已记录的 owner 允许其区块进入 FEATURES 之后，继续等待剩余 owner；pending 授权本身不算完成证据。已生成 owner 缺少匹配片段仍返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，消息列出具体区块。读取状态与世界生成并发时，报错前再次核对片段，整体完成账本在下次观察时汇总，不提前伪造完成。

纯等待为 `ok=true/status=waiting_for_worldgen/reasonCode=WAITING_FOR_WORLDGEN`，自动队列继续轮询。真实失败与等待同时存在时为 `ok=false/status=failed`，保留实际失败原因；waitingSummary 仅作进度信息，不能覆盖错误码。

## 错误码

### 模板目录与几何

- `CITY_TEMPLATE_CATALOG_SCHEMA_UNSUPPORTED`：schema 不支持。
- `CITY_TEMPLATE_CATALOG_FIELD_MISSING` / `CITY_TEMPLATE_CATALOG_FIELD_UNKNOWN`：必填字段缺失或出现未声明字段。
- `CITY_TEMPLATE_CATALOG_JSON_INVALID` / `CITY_TEMPLATE_CATALOG_ROOT_INVALID`：目录 JSON 根或语法非法。
- `CITY_TEMPLATE_CATALOG_DUPLICATE_VARIANT`：`templateRef + variant` 重复。
- `CITY_TEMPLATE_CATALOG_TEMPLATE_UNKNOWN` / `CITY_TEMPLATE_CATALOG_VARIANT_NOT_FOUND`：引用不存在。
- `CITY_TEMPLATE_NBT_NOT_FOUND` / `CITY_TEMPLATE_NBT_READ_FAILED`：模板 NBT 无法读取。
- `CITY_TEMPLATE_HASH_MISMATCH`：目录、plan 或加载内容 hash 不一致。
- `CITY_TEMPLATE_CATALOG_SIZE_INVALID` / `CITY_TEMPLATE_CATALOG_TEMPLATE_INVALID`：NBT 尺寸或模板条目非法。
- `CITY_TEMPLATE_CATALOG_ENTRANCE_INVALID` / `CITY_TEMPLATE_CATALOG_ENTRANCE_OUT_OF_BOUNDS`：入口字段或局部坐标非法。
- `CITY_TEMPLATE_CATALOG_ROTATION_INVALID` / `CITY_TEMPLATE_CATALOG_ROTATION_NOT_ALLOWED`：旋转非法或不在允许集合。
- `CITY_TEMPLATE_CATALOG_MIRROR_INVALID` / `CITY_TEMPLATE_CATALOG_MIRROR_NOT_ALLOWED`：镜像非法或不在允许集合。
- `CITY_TEMPLATE_BBOX_INVALID`：half-open / closed 转换或 bbox min/max 非法。
- `CITY_TEMPLATE_PLACEMENT_IDENTITY_DRIFT`：D2、D4、D6、active registry、worldgen 或 D7 identity 不一致。
- `TEMPLATE_RUNTIME_TRANSFORM_MISMATCH`：Minecraft runtime 变换后的逐点坐标、footprint 或 owner fragment 与 City 规划几何不一致。
- `TEMPLATE_LOCKED_FOOTPRINT_MISMATCH`：identity 复算 footprint 与 D6 `lockedActualFootprint` 不一致。
- `CITY_TEMPLATE_ACTIVE_REGISTRY_MISSING`：worldgen 前未找到对应 active template placement registry。
- `CITY_TEMPLATE_CHUNK_ALREADY_GENERATED`：目标 chunk 已过 worldgen 交接窗口且没有可用 ledger。

### 道路与 legacy

- 城区 `CONNECTION`、区内道路及跨水桥均由 City 自有道路计划与 SurfacePrint 落地。模板入口只作为 City 路网的真实目的地，不再注册给外部道路 Mod。
- 旧 WorldEdit 沙砾道路提供器、外部道路 provider 和 D7 延迟道路后处理均不存在，不得恢复为兼容或调试路径。
- `CITY_TEMPLATE_TRANSFORMED_ENTRANCE_INVALID`：transformed entrance 越界、方向或 anchor 不一致。
- `CITY_TEMPLATE_LEGACY_INPUT_REJECTED`：旧建筑输入被拒绝；响应必须带具体 legacy reason。
- `CITY_TEMPLATE_LEGACY_STRUCTURE_REGISTRY_INPUT`：试图用 `Registries.STRUCTURE` 作为 active 模板来源。
- `CITY_TEMPLATE_LEGACY_STRUCTURE_START_INPUT`：试图提交或消费外部 / configured StructureStart；目录驱动的 City 单-piece terrain start 不属于该输入。
- `CITY_TEMPLATE_LEGACY_JIGSAW_POOL_INPUT`：试图提交或消费 Jigsaw pool / 展开结果。
- `CITY_TEMPLATE_LEGACY_BBOX_ENTRANCE_INPUT`：试图用 bbox 外侧伪入口替代模板 `roadEntrances[]`。

既有旧 City 功能区链路仍按 `LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED` 处理；该错误不能被解释为模板路径兼容成功。

## 兼容策略与硬规则

- `v0.1` 只兼容本契约四种 schema 的精确版本；只要涉及模板建筑 active path，就不兼容旧 `structureId`、`nbtFile`、configured structure、Jigsaw pool、外部 StructureStart、profile safety envelope 或 bbox 外侧 `roadPoint`。唯一例外是冻结 `terrainPosePolicy=structure_start_beard_thin` 后由 City 创建的单-piece terrain start。
- 目录更新必须重新计算 `templateHash`，并使旧 plan / active registry 失效；不能只改文件名、variant 或尺寸字段绕过 hash 校验。
- active registry、worldgen ledger、D7 汇总均必须保留相同 identity；每次使用 `templateSize + rotation + mirror + anchor` 复算并校验 closed `actualFootprint`。缺字段、hash 漂移、变换漂移、派生 footprint 漂移和入口漂移均 hard fail。
- 自动 workflow 只有在 D5 artifact 来源身份仍有效且当前 server-root 集合实际包含该 `runId + citySeedId + cityId` 时，才允许跳过 `city_execute_d5`；仅有旧 artifact 文件不能证明 runtime 已激活。
- 外部 StructureStart / Jigsaw 自动生成的旧测试和旧 artifact 只用于历史保护，不能作为模板专项验收通过依据；City 配置化 terrain start 必须单独验证 policy、datum、piece 和 Beardifier 结果。


## 同区块建筑与细地形基础（2026-09-08）

同一 chunk 的 City StructureStart 必须合并全部固定模板 pieces；幂等检查按 anchorId+anchor 坐标识别，不能因为已有有效 start 就跳过后续建筑。每个 piece 继续独立核对模板身份、footprint 并记载生成片段。

已生成模板的实心底板列下方若为空气或流体，补必要基础；空院落不补统一地板。超过 maximumSolidFillHeight 时采用薄底板和稀疏 `minecraft:blackstone_wall` 支撑，避免整列填实。仅写当前 owner chunk 范围，仍受世界高度约束。
