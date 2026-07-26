# 潮汐王冠首都“潮门城”百建筑设计 v0.1

## 状态

当前设计案。本文把 sealed W/T 结果实例化为一座崖岸型首都设计。D3 已完成真实局部 GIS 刷新，用户已确认按崖岸型继续；本轮 D4 已生成 80 个唯一建筑 anchor，质量通过但尚未执行 D5/D6 或世界写入。建筑数量仍只代表规划结果，只有 D6 locked footprint、worldgen ledger 和现场观察全部完成后，才可以宣称真实落地。

本案沿用 City 当前固定模板唯一落地主线：D3 局部地貌事实 -> D4 建筑锚点 / 阵列 -> D5 预案 -> D6 locked footprint -> LandUse / Decoration -> execute_d5 -> 首次 worldgen。本文不恢复旧 FunctionZone、Jigsaw 或 late paste。

## 一、选址依据

本案选择当前最新 sealed W/T 运行 `realm_w_mryvxhga_62af05d6` 中的潮汐王冠首都。

| 项目 | 当前事实 |
| --- | --- |
| W/T run | `realm_w_mryvxhga_62af05d6` |
| W 状态 | `sealed=true`，`schemaVersion=realm_planning.v1.2` |
| W/T 质量 | `passed=true`，总分 `86.97`，`hardBlocks=[]` |
| 国度 | 潮汐王冠 `realm_tide_crown` |
| 国度主题 | 沿海贸易与河口航运国度 |
| 国度产业 | 渔业、贸易、造船 |
| 国度材料 | 石、木、铜 |
| 国度偏好 | 海岸、平原、河流；本案按 D3 实况改用崖岸地形 |
| 城市种子 | `city_realm_tide_crown_capital` |
| 城市身份 | `capital` |
| 理论规模 | `capital`，进入 City 后映射为 `CityScale.CITY` |
| 粗锚点 | grid `(35, 2)`，block `(4480, 256)` |
| T4 粗范围 | `planningRadiusCells=4`，不能直接当作 C1 最终城市边界 |
| T4 条件 | `land`、`inside_realm` |
| D3 实跑 | 161 个地貌 patch、20 个 GIS region、2304 个 terrain cell；规划范围部分越出国度边界 |
| D3 选址门槛 | 平原仅 2 个连续候选，最大 3072 blocks；主导地貌为崖壁 / 山谷 / 水域 |
| D4 初始地貌选择 | `CLIFF-02` 高崖台地、`VALLEY-04` 中心谷地、`SHORE-02` 水岸、`WATER-01` 连续水域 |
| D4 实际补丁使用 | 关键与数组实际消费 `CLIFF-02`、`CLIFF-01`、`CLIFF-03`、`CLIFF-04`、`VALLEY-01`、`WATER-01`；`VALLEY-04` / `SHORE-02` 因连续空间不足未进入最终 anchor map |

### 选址解释

潮汐王冠拥有沿海贸易、河口航运、渔业和造船的明确城市语法，且首都已经由 T4 登记为必定存在。D3 没有证实连续平原核心，但确认了大面积连续崖壁、中心谷地和近距离水岸。用户已确认保留该城市种子，改为“崖岸型首都”：行政与防御占高位，商业与居民沿谷地和坡折展开，仓储与港口下沉到水岸。

如果 D3 证明粗锚点周围没有可承载城区的水岸 / 平原连续面，必须回到同一 sealed W 的 City Patch Explorer 重选已展示候选；不得静默改到另一块地，也不得把 W 粗 patch 当成城市内部地貌真值。

## 二、城市定位

“潮门城”是潮汐王冠的首都、崖岸转运中心和内陆农业腹地的总集散地。城市空间采用“高崖行政台地 + 中层谷地街坊 + 低层水岸港储 + 外围观察塔”的三级组织方式：

```text
                 高崖 / 内陆方向
              [行政院落 / 观察塔]
                      |
        [上层居民] - [中心广场] - [谷地商业]
                      |
          [坡折农田、风车与谷仓]
                      |
             [水岸港储 / 码头入口]
```

这只是 C2 的相对构图意图，不是建筑世界坐标。每一栋建筑仍必须由 D4 候选生成，由 Agent 选择整组候选，再由 D6 锁定真实模板 footprint。

## 三、规模门槛与建筑预算

本案按首都级大城市执行，目标为 **99 栋可物化建筑**，硬门槛为不少于 80 栋。下表只统计 D4 的建筑结构，不把道路、城墙、农田、水槽或装饰 prefab 算作建筑。

| 功能片区 | 建筑预算 | 设计作用 | LandUse / 阵列 |
| --- | ---: | --- | --- |
| 农业生产与仓储带 | 12 | 生产、储粮、农户与牲畜运输 | `CULTIVATE`，三个 group，`autoConnect=true` |
| 中心广场与广场边建筑 | 4 | 首都公共中心与沿广场服务 | `PAVE`，`plaza_ring` / `composite_array` |
| 行政院落 | 3 | 市政厅、警卫厅和行政附属 | `PAVE`，`compound_cluster/u_shape` |
| 商业、工坊与文化街 | 30 | 交易、住宿、加工、文化服务 | `PAVE`，多组 `guide_line_dual_side` |
| 居民街坊 | 45 | 城市人口主体与生活街区 | 两个 `composite_array`，排屋 + 院落 |
| 外围防御 | 5 | 三向观察、主入口和滨水防御 | 不创建独立 LandUse 面 |
| **合计** | **99** | **满足大城市不少于 80 栋** | |

### 本轮 D4 冻结结果

99 栋仍是本案设计目标；真实 D4 按地貌候选和碰撞包络冻结为 80 栋，已达到大城市硬门槛。`structure_anchor_map.json` 的 80 个 `anchorId` 唯一，质量 `passed=true`、`score=100`、`hardBlocks=[]`。

| D4 分组 | 实际数量 |
| --- | ---: |
| 崖地农业 | 12 |
| 崖顶广场 | 4 |
| 崖顶公共支撑与传令所 | 4 |
| 崖顶商业分片 | 10 |
| 居民分片 | 40 |
| 关键行政 / 门塔 / 港口 | 5 |
| 防御塔组 | 5 |
| **合计** | **80** |

水岸小 patch 和中心谷地只保留为叙事与关键节点输入；当候选组无法满足不重叠条件时，D4 选择拆分到连续崖台，不通过放宽 `candidateLegalRegion` 凑数。

### 建筑与装饰的计数边界

计入 99 栋的对象必须有 D4 `StructureAnchorPlan` 项，并在 D6 产生 `lockedActualFootprint`。喷泉、长椅、灯柱、旗帜柱、公告板、市场摊位、稻草人、草垛、石质农业矮墙、沟渠水带和道路均不计入建筑数量。

如果某个固定模板尚未通过目录 hash / 尺寸 / 入口校验，不能用装饰物替补，也不能把同一栋建筑重复记账；应回到该阵列生成完整候选或调整模板目录，然后重新计数。

## 四、建筑清单

### 4.1 农业生产与仓储带：12 栋

农业区不再假设连续平原，而从 `VALLEY-04` 的谷地缓坡和 `CLIFF-02` 下缘可用台阶开始，三个 group 沿等高线服务带错落排布。农田、沟渠和谷仓允许分布在多个连续 terrace component，但每个 component 必须有明确的谷地连接与坡折 gate，不能用矩形 LandUse 填满崖壁。

| group | 模板 | 数量 | 说明 |
| --- | --- | ---: | --- |
| `farm_mill_cluster` | `geomantia:city/stubbs/agriculture/windmill_01` | 1 | 田地边缘的首个生产地标 |
| `farm_mill_cluster` | `geomantia:city/stubbs/agriculture/barn_windmill_01` | 1 | 与风车形成生产组合 |
| `farm_storage_cluster` | `geomantia:city/stubbs/agriculture/barn_01` | 2 | 面向装卸服务路 |
| `farm_storage_cluster` | `geomantia:city/stubbs/agriculture/farm_storage_house_01` | 2 | 储粮与农产品转运 |
| `farm_storage_cluster` | `geomantia:city/stubbs/agriculture/horse_stall_02` | 1 | 与仓储组围出装卸院 |
| `farmstead_cluster` | `geomantia:city/stubbs/agriculture/farm_home_01` | 5 | 靠近田地入口的农户住宅 |
| **小计** |  | **12** | |

阵列选择：`farm_mill_cluster` 使用 `compound_cluster/organic_compact`；`farm_storage_cluster` 使用 `compound_cluster/u_shape`；`farmstead_cluster` 使用单侧或错位双侧 `guide_line_dual_side`。最终农业面必须是一个连通、不规则、不得贴满 planning bounds 的 LandUse 区域。

农业表面使用 `CONTOUR_BANDS`：FIELD 与两侧 BANK 组成田垄，中间 WATER 组成水槽；跨 chunk 的相位、开放端封口和 owner 分片均按 SurfacePrintPlan 全局结果执行。农业边界只沿最终外圈使用石质 `LOW_WALL`，禁止木栅栏。

### 4.2 中心广场与广场边建筑：4 栋

中心广场位于行政院落和商业街之间，至少保留三个方向的宽通道。喷泉是中心装饰锚点，不计入建筑预算。

| 模板 | 数量 | 说明 |
| --- | ---: | --- |
| `town_shop_01` | 2 | 面向广场的零售店 |
| `bake_shop_01` | 1 | 与农业供应链相连的烘焙店 |
| `flower_shop_01` | 1 | 广场生活服务与视觉焦点 |
| **小计** | **4** | |

广场执行 `PAVE`，喷泉、长椅、灯柱、旗帜柱和公告板必须在 plaza LandUse 定稿后经过关键装饰候选流程生成，禁止手算世界坐标。广场不得被装饰填满，喷泉与行政院正门之间必须保持清晰视线和步行通道。

### 4.3 行政院落：3 栋

| 模板 | 数量 | 说明 |
| --- | ---: | --- |
| `geomantia:city/stubbs/civic/town_hall_01` | 1 | 市政厅，正立面朝中心广场 |
| `geomantia:city/stubbs/civic/guard_outpost_01` | 1 | 警卫厅，靠近主入口一侧 |
| `geomantia:city/stubbs/civic/town_hall_02` | 1 | 行政附属，不与主市政厅重复为核心地标 |
| **小计** | **3** | |

市政厅和警卫厅是 D4 关键建筑，必须先于批量阵列逐个生成候选并选择。三栋建筑组成向广场开口的 `u_shape` 行政院落，统一进入 `civic_court` PAVE 连通组；广场侧不得用窄墙封死。

### 4.4 商业、工坊与文化街：30 栋

商业区不是四栋孤立功能建筑，而是主要功能建筑带附属住宅 / 工人房的混合街组。双排建筑之间应由真实道路或连续步行带连接，`guide_line_dual_side` 只表达建筑秩序，不代替 RoadWeaver。

| 街组 | 模板 | 数量 | 阵列 |
| --- | --- | ---: | --- |
| 酒馆服务街 | `tavern_01` | 1 | `guide_line_dual_side` |
| 酒馆服务街 | `motel_01` | 1 | `guide_line_dual_side` |
| 酒馆服务街 | `village_house_small_01` / `household_01` | 4 | 两侧错位附属房 |
| 市场零售街 | `general_store_01` | 1 | `guide_line_dual_side` |
| 市场零售街 | `town_shop_01` | 2 | 两侧面向内街 |
| 市场零售街 | `bakery_01` | 1 | 靠近广场与粮食流线 |
| 市场零售街 | `small_butcher_shop_01` | 1 | 靠近市场后勤侧 |
| 市场零售街 | `village_house_small_02` / `household_02` | 5 | 商户与伙计住宅 |
| 工坊仓储街 | `town_workshop_01` | 2 | `composite_array` 双排子阵列 |
| 工坊仓储街 | `merchant_house_01` | 2 | 商住混合 |
| 工坊仓储街 | `farm_storage_house_01` | 1 | 农业入城转运节点 |
| 工坊仓储街 | `civilian_house_01` / `household_03` | 5 | 工人房与附属住宅 |
| 文化服务节点 | `library_01` | 1 | 靠近广场但不抢喷泉中心 |
| 文化服务节点 | `theater_01` | 1 | 可选文化地标，目录缺失时必须显式降级为未满足 |
| 文化服务节点 | `city_home_01` / `city_home_02` | 2 | 文化服务人员住宅 |
| **小计** |  | **30** | |

四个街组都使用 `central_commercial` 语义和 `PAVE`，但不要求每组商业面物理融合。每组只注册有限 RoadWeaver gateway，避免为每栋附属房单独拉长距离道路。

### 4.5 居民街坊：45 栋

居民区分布在 `CLIFF-02` 的中上层台阶与 `VALLEY-04` 的上缘过渡带，拆成两个高差不同但相互可达的 parent group，避免完整矩形网格和单一撒点。

| 街坊 | 模板 | 数量 | 组织方式 |
| --- | --- | ---: | --- |
| 北部排屋街坊 | `city_home_01` | 4 | `guide_line_dual_side`，街角大宅 |
| 北部排屋街坊 | `city_home_02` | 4 | `guide_line_dual_side`，街角大宅 |
| 北部排屋街坊 | `civilian_house_01` | 5 | 沿街住宅 |
| 北部排屋街坊 | `civilian_house_02` | 4 | 沿街住宅 |
| 北部排屋街坊 | `household_01` / `household_04` | 6 | 小庭院家庭住宅 |
| 北部排屋街坊 | `village_house_small_01` | 3 | 边缘填充，不连续复制 |
| **北部小计** |  | **26** | |
| 东部院落街坊 | `city_home_02` | 3 | `courtyard` 院落角点 |
| 东部院落街坊 | `civilian_house_03` | 5 | 院落与商业过渡 |
| 东部院落街坊 | `household_05` | 4 | 院落家庭住宅 |
| 东部院落街坊 | `household_06` | 3 | 院落家庭住宅 |
| 东部院落街坊 | `household_07` | 2 | 边缘住宅 |
| 东部院落街坊 | `village_house_small_02` | 2 | `organic_compact` 边角填充 |
| **东部小计** |  | **19** | |
| **居民合计** |  | **45** | |

北部 parent group 使用两条 `guide_line_dual_side` 排屋带；东部 parent group 使用 `courtyard` + `organic_compact` 子阵列。居民院落默认保留部分自然地表，由真实道路接入，不把整片住宅空地刷成石砖；生活装饰只能落在 remaining mask，不得堵塞门口和道路 gateway。

### 4.6 外围防御：5 栋

| 位置 | 模板 | 数量 | 作用 |
| --- | --- | ---: | --- |
| 高崖外缘 | `geomantia:city/stubbs/civic/guardian_tower_01` | 1 | 观察高崖外侧与主入口 |
| 谷地北缘 | `geomantia:city/stubbs/civic/guardian_tower_02` | 1 | 覆盖行政台地与居民上层 |
| 水岸折口 | `geomantia:city/stubbs/civic/guard_tower_03` | 1 | 保护谷地下行路与港储带 |
| 入口节点 | `geomantia:city/stubbs/civic/guard_gate_01` | 2 | 高崖主入口和水岸入口 |
| **小计** |  | **5** | |

五栋防御建筑分别走外围关键 anchor 候选，不进入批量 fill pool，也不创建远离城区的孤立 civic LandUse。每座塔都必须有 RoadWeaver 入口或宽步行通道；如果 D3 证明某侧不是水岸，滨水塔应改为“西侧入口塔”语义，而不是保留错误地貌叙事。

## 五、D4 规划顺序

1. **D3 / Patch Explorer 已冻结**：D3 已完成；D4 依次消费带有当前占用快照的 `psel_*` 凭证，不手写或扩大 `candidateLegalRegion`。
2. **关键 anchor**：已完成 5 个关键建筑，包含高崖王城、谷地议政塔、崖顶城门塔、北崖瞭望塔和港口水上商栈。
3. **崖地农业群**：已完成 12 栋崖地农场 / 农业磨坊数组；农业 LandUse 仍待 D5/D6 锁定后生成。
4. **崖顶公共与商业**：已完成 4 栋广场、3 栋公共支撑、1 栋传令所和 10 栋商业建筑；中心谷地因空间不足不强行填充。
5. **港口与水岸**：港口关键结构已落在 `WATER-01`；`SHORE-02` 保留为后续岸线扩展候选，未把失败的岸线组写入 anchor map。
6. **分层居民与防御**：已完成 40 栋居民和 5 栋防御塔，分布到多个连续崖台，所有当前合并阶段均通过碰撞检查。
7. **D4 计数门**：当前汇总 80 个独立建筑 anchor，检查 `anchorId` 唯一、质量通过、collision 无硬阻断，达到大城市不少于 80 栋门槛；99 栋目标尚未完成，不将其虚增到 D4 结果。
8. **D5 / D6**：下一阶段如接受当前 80 栋冻结结果，则按这 80 项生成 reservation / mask 并锁定 `actualFootprint`；如仍要求 99 栋，必须先开启新的 D4 扩展轮次。
9. **LandUse / Decoration**：D6 成功后生成农业 `CULTIVATE + CONTOUR_BANDS`、广场 / 行政 / 商业 `PAVE`、居民 `PRESERVE` 或局部 PAVE；喷泉等 required 装饰先走关键装饰候选。
10. **worldgen 验收**：只在新存档、目标 owner chunk 尚未到 FEATURES 时执行 `execute_d5`；D7 / observation 只以现场实际方块和完整 owner fragment 统计真实落地数量。

## 六、验收口径

### 自动结构门

| 指标 | 门槛 |
| --- | ---: |
| D4 独立建筑 anchor | `>=80`，本案目标 `99` |
| D6 locked 建筑 | 必须与 D4 选定数量一致，目标 `99` |
| 农业建筑 | `12` |
| 广场边建筑 | `4` |
| 行政建筑 | `3`，必须包含市政厅和警卫厅 |
| 商业 / 工坊 / 文化建筑 | `30` |
| 居民建筑 | `45` |
| 防御建筑 | `5`，至少三座不同方向的观察塔 |
| 建筑重复计账 | `0` |
| D6 collision overlap | `0` |
| 未锁定模板替补 | `0` |

### 空间与生活感门

- 农业 LandUse 必须是一个连通、不规则面域，不能使用 bbox 填充；三个农业 group 之间的兼容距离和自动相向扩张必须有 trace 证据。
- 农田使用 FIELD / BANK / WATER 全局 role mask；水槽横断面为“田地 5 格 | BANK | WATER | BANK | 田地 5 格”的等高线条带语义，跨 chunk 不重启相位。
- 农业外圈是石质 `LOW_WALL`，不出现木栅栏；农舍、谷仓和主路入口保留可读 gate。
- 市政厅和警卫厅与中心广场属于同一可达 civic 关系；广场喷泉可见，至少三个方向保留通道。
- 商业双排之间存在真实道路或连续步行面；道路不得穿过建筑 body、屋顶或墙体。
- 两个居民街坊具有不同内部秩序：北部为街道双排，东部为院落 + 有机紧凑簇；不得退化为单一完整 grid。
- 五栋防御建筑各自承担不同外围方向，且每栋有入口可达性。
- 预览至少包含城市总览、农业视角、中心广场视角、商业街视角和居民街坊视角；现场结构数量必须来自 D7 ledger / worldgen observation，不能只读 D4 计划数量。

## 七、当前不做的事

- 本案不在 T4 重新生成城市名册，也不修改潮汐王冠的城市种子。
- 本案不在没有 D3 证据时断言粗锚点就是河口或海岸；地貌不匹配时回到同一 sealed W 的候选探索。
- 本案不把 99 栋建筑压成一个大 configured structure，不恢复 Jigsaw 深度或 late paste。
- 本案不把装饰、农田、水槽、道路和城墙计入建筑数量。
- 本案本轮不要求完整城墙；如后续启用 City Walls，必须基于真实 `actualFootprint`、道路和农业 gate 重新规划。
- 本案不把“计划 99 栋”写成“世界已有 99 栋”；等待 chunk、worldgen ledger 未完成或 observation 缺失时，状态只能是 `planned` / `waiting` / `partial`。

## 八、下一步

D4 已完成并达到 80 栋硬门槛，`structure_anchor_preview.png`、80 项分组与空间层级已完成审阅。下一步决定按当前 80 栋进入 D5/D6，或针对 99 栋目标开启新的连续外扩候选轮次；无论哪条路径，都不能跳过 D5/D6 的真实 footprint 锁定。
