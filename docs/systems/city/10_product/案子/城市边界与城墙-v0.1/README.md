# City 案子：城市边界与城墙 v0.1

## 状态

已完成 v0.1 临时城墙闭环，并入当前 City 主线。

本案不恢复“先画功能区硬边界再塞结构”。城墙只在 D7 ledger 完整后，以真实落地结构的 `actualFootprint` 并集为来源，生成临时正交矩形外圈。

## 当前口径

- 新增 `city_plan_city_walls` / `city_execute_city_walls` HTTP 与 MCP 入口。
- `city_plan_city_walls` 读取 D7 `placed_structure_ledger.json`。
- 默认 `wallMarginBlocks=24`，`segmentLengthBlocks=15`，`gateWidthBlocks=7`。
- 边界来源是所有 `actualFootprint` 的 union 外扩，不是旧功能区边界。
- v0.1 只生成临时矩形 / 正交边界，snap 到 15 格段。
- 城门是“7 格缺口 + 两侧小塔楼”，不做完整门楼。
- 执行后端为 `vanilla_setblock`，不依赖 WorldEdit。
- 单段高度差超过 5 blocks 跳过并报告 `WALL_TERRAIN_TOO_STEEP`。

## 模板

模板来自用户提供的 `GPT城墙设计.txt` 口径，当前内置：

- `wall_straight_15`
- `wall_tower_small`
- `wall_gap_gate_7`

`CityWallTemplateCatalog` 定义纯模板元数据，`MinecraftCityWallArtifactWriter` 会导出：

- `city_wall_templates/wall_template_library.json`
- `city_wall_templates/wall_straight_15.nbt`
- `city_wall_templates/wall_tower_small.nbt`
- `city_wall_templates/wall_gap_gate_7.nbt`

这些 `.nbt` 是 vanilla structure-template 风格的压缩 NBT artifact；v0.1 执行时仍使用 setBlock 几何后端，后续可切换到 `StructureTemplate.placeInWorld`。

## 当前 artifacts

`city_plan_city_walls` 输出：

- `city_wall_plan.json`
- `city_wall_preview.png`
- `city_wall_templates/*`

`city_execute_city_walls` 输出：

- `city_wall_placement_report.json`

## 验收

- 城墙 plan 必须在 D7 ledger 完整后生成。
- `boundaryMode=temporary_rectilinear_actual_footprint_union`。
- `sourceActualFootprintUnion` 来自真实 `actualFootprint`。
- 城墙 preview 能显示 source footprint、wall bounds、wall segments、tower 和 gate gap。
- 城墙段不得压结构 actual footprint。
- 陡坡段必须跳过并写 `WALL_TERRAIN_TOO_STEEP`。
- `.nbt` 模板 artifact 可被 MC NBT 读取。

## 暂不处理

- 不做最终边界算法。
- 不做复杂城门、门楼、转角美化、破损变体。
- 不做军事防御逻辑。
- 不把城墙边界反向作为 D4 功能区硬边界。
- 不接 RoadWeaver 或地形适配结果做墙体曲线。

## 后续方向

- 用 D3 水岸、山脊、崖壁和 RoadWeaver 道路结果替换矩形边界。
- 增加角楼、门楼、破损墙、木栅栏、农田篱笆、码头岸线等主题边界。
- 城墙执行从 setBlock 后端升级为 `StructureTemplate.placeInWorld`。
- 城墙与 terrain adaptation 联动，补挡墙、台基和坡道。
