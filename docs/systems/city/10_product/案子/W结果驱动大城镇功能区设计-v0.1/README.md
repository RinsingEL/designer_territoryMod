> 原始需求（用户原文）
>
> 目前游戏启动并已经是最新的代码了，麻烦在当前的W的结果的基础上，选一个地方设计一个大城镇。
>
> 这个城镇有以下要求：
>
> 1、必须有农业区，农业区得有风车和谷仓，如果有像马厩啊、农民房屋这种更好。其中最关键的则是田地，得让他形成一大片连续的稻田和水槽交错的田地，中间散落一点稻草人。装饰咱不用木栅栏了，而是用石的栅栏
>
> 2、功能区可以做的繁华一点，各个功能建筑都可以有，而且我觉得正常是不是一个功能建筑如酒馆旁边带着三四个小屋子整齐排列。而且是否应该善用两侧排列的阵列算法？功能区也可以有很多居住的房子的。
>
> 3、得有一个广场，以喷泉为中心，可以加点如长椅的装饰，
>
> 4、行政区则是必须有市政厅，还有警卫厅。
>
> 5、居民区则看你发挥了，首先有很多屋子是肯定的，就看怎么阵列好看了
>
> 6、需要有警卫塔
>
> 最后各个同类型的功能区必须连在一起，尤其是landUse把地板处理为石砖的，城区部分应该就是要地板连在一起。看看现在是代码里自动连一起了，还是需要agent决策驱动呢

# City 案子：W 结果驱动大城镇功能区设计 v0.1

## 状态

当前设计案。既有 W 选址、D4 的 14 个 placement group / 52 个建筑布局、D5/D6 锁定结果和道路 group 空间 MST 已通过上一轮设计验收；但旧农业 Decoration 方案已被本轮 SurfacePrintPlan 主线取代，旧 LandUse active / ledger 必须清理，并重跑 `city_plan_land_use -> city_plan_city_dressing -> city_execute_d5` 后才能验收新农田。首次 worldgen 仍必须从目标区外侧触发，规划与激活不得主动生成区块。

本文不恢复旧 `FunctionZoneMap`。功能区语义由 D4 建筑 group / array provenance 表达，D6 locked footprint 后再生成 block 级 `LandUseAreaPlan`。旧城镇方案、旧选点和旧分区均不作为本案输入。

## 后续锁定决策

- 旧方案全部废弃，不沿用旧选点、阵列数量、分区或 LandUse 分组。
- 农田整体外轮廓必须由 LandUse 成本扩张形成不规则面域，禁止用矩形 bbox 直接填满。
- 农田内部可以存在规则矩形田垄，但整体农业区不得呈完整矩形。
- 农田水槽一律由 `CONTOUR_BANDS` 全局 role mask 直接生成：`CHANNEL_BEFORE_BANK + CHANNEL_WATER + CHANNEL_AFTER_BANK`；不再依赖直线 / 端帽 NBT，也禁止回退 `geomantia:decoration/water_channel_tile`。
- 农业区禁止木栅栏；外边界使用石质矮墙。当前执行能力可用 `boundaryPolicy=LOW_WALL` 映射为 `minecraft:cobblestone_wall`。
- 同类型功能区不再由 AI 枚举配对。兼容地表两侧默认 `autoConnect=true`，初次边界间距不超过 64 格时自动相向扩张；AI 只在需要隔离时关闭某个 group 的自动连接。
- 农业区使用 CULTIVATE 兼容类别自动相向扩张；商业、居民等 PAVE 街区也可自动接触，仍允许被硬障碍或真实道路分隔，最终以入口交通可达验收。
- 城区连通验收对象改为 `PAVE surface ∪ actualRoadMask ∪ plazaWalkwayMask`，不要求所有不同用途的 `PAVE` LandUse 直接接触。

## 一、目标与非目标

### 1.1 目标

本案目标是生成一座可以直接从俯视图和实机游览中读出生产、交易、治理、居住和防御关系的大城镇，而不是一组只满足数量和防撞的建筑。

成功表现至少包括：

- 一片规模足够、外轮廓自然不规则、内部田垄与水槽规则交错的连续农业区。
- 一个以喷泉为明确中心、由建筑立面围合的中心广场。
- 市政厅与警卫厅组成可读的行政院落，并直接连接中心广场。
- 多个繁华功能建筑组，每个主要功能建筑附近有 3-4 栋整齐组织的小型住宅或附属房屋。
- 至少两个具有不同内部秩序的居民街坊，不使用单一撒点或完整矩形网格填满。
- 至少三座警卫塔承担不同方向的观察和入口防御。
- 农业 LandUse 形成连续地表；广场、行政、商业和居民街坊通过铺装面、广场步行面和真实道路组成连续交通网络。

### 1.2 非目标

- 不让 AI 手写每栋建筑的世界坐标。
- 不让 AI 提交逐 block 连接路径、裸扩张成本、64 格阈值或道路具体宽度；AI 只覆写地表布尔、方块、方向和跨区设计关系。
- 不用一个矩形区域代表整片农田、居民区或商业区。
- 不把 RoadWeaver 当作修复功能区碎裂的工具。
- 不为了铺平地表削山、填河、填开放沟谷或制造一整块人工平台。
- 不在本文中改变既有 schema；发现实现缺口时单独进入配置或实现任务。

## 二、W 宏观选址

### 2.1 冻结位置

前两个 W 宏观候选经 D3 否决，第三候选已冻结为本案唯一选址：

| 项目 | 值 |
| --- | --- |
| city seed | `city_w_large_town_c_20260720` |
| W grid | `20370,20378` |
| anchor block | `651840,652096` |
| D3 core | `x=651328..652352, z=651584..652608` |
| 地形格局 | 北侧与东侧临水，西侧有崖地，中南部是平原 / 台地与缓坡交错的内陆带 |
| D3 平坦单元 | plain 412 + terrace 196，共 608 个 `16×16` cell |
| 最大平坦连通块 | 349 cell / 89,344 方格，外包约 `416×752` |
| 主城大窗口 | 中心约 `(651792,652320)`，`224×224` 窗口内 126/196 cell 平坦，无水域或崖壁 |
| 广场优先核心 | `(651872,652368)` 附近，`160×160` 窗口平坦率约 78% |

### 2.2 选址边界

W 只负责宏观选址，D3 patch 与 `16×16` LandUse terrain cell 才是后续建筑候选和功能区边界的地形真值。

- 农业区从主城西北侧进入最大平原 / 台地连通带，沿地形向北和西北分支扩展。
- 中心广场与行政、商业核心使用中南部最稳定的大窗口，不把城镇 anchor 当作必须落点。
- 居民区使用东南侧第二平坦连通块，通过主路与广场连接，允许与主城 PAVE 不直接物理融合。
- 北岸、西侧崖地进入方向和东南主入口分别设置警卫塔，避免在同一侧等距摆成一排。
- D4 只能在 D3 核心与可用 patch 内生成候选；任一功能区触及未知边界或需要大面积整平时，回到该轮 D4 重选。

## 三、总体空间结构

```text
                                  北
北部水岸       [连续不规则田地] [风车 / 农业服务带] [北岸警卫塔]

西侧崖地入口   [西侧警卫塔] [行政院落] [功能商业街]

                 [农田南缘] [中心广场] [东南居民街坊]

                                [工坊 / 市场街] [东南主入口警卫塔]
                                  南
```

空间原则：

- 中心广场是城市组织中心，不放在孤立角落。
- 行政区贴广场北侧或西北侧；市政厅正立面朝向广场。
- 商业功能组沿广场东侧和南侧形成两到三条双排街带，不侵入西北农业连续面。
- 居民区优先放在东南第二平坦连通块，既接近商业，又不侵占农业连续面域。
- 农业区占据主城西北的最大连续平原 / 台地带，农业建筑集中在田地与行政 / 广场核心的交界服务带。
- 警卫塔位于外围观察点和主要入口，不作为孤立 civic LandUse 种子。

## 四、全城共同设计规则

### 4.1 D4 与 LandUse 分工

- Agent 决定功能区的相对方位、先后顺序、邻接关系、建筑主题、阵列类型、地表方案和跨区关系。
- D4 程序根据 patch、方向、阵列参数和 occupied field 生成并选择安全候选。
- D6 锁定 `lockedActualFootprint` 后，LandUse 才能以真实建筑外缘和入口生成区域。
- Agent 不提交逐 block mask、连接路径、连接宽度、64 格阈值或寻路成本；这些都由程序根据地形和固定 profile 计算。
- `mergeSameType` 表示接触后允许融合；LandUse 连接设置中的 `autoConnect` 表示是否参加 64 格自动近邻。连接由第二遍正常扩张形成，禁止事后补桥；`UNIFORM` / `CONTOUR_BANDS` 等刷地算法不参与连接判定。
- 不同 LandUse 类型保持各自语义。需要交通连接时生成道路接缝意图，不把其中一侧强行改写成另一种 LandUse。

### 4.2 AI 可配置的地表意图

`city_land_use_intent_plan.v0.3` 在本次规划请求中用 `surfaceAlgorithmDefaults[]` 提供每座城市的材料默认，再通过 `surfaceOverrides[]` 对最终 group 做少量覆写。服务端 profile / 内置材料只在请求未给值时兜底，不能替代本次城市规划的材质决定。PAVE / CULTIVATE 仍是 LandUse 用途和连接兼容语义，不再充当刷地算法名称。

| 配置 | 默认语义 | 本城镇用途 |
| --- | --- | --- |
| `surfacePrintEnabled` | PAVE / CULTIVATE 为 true | 林场可保持 false；城区和农田保持 true |
| `autoConnect` | 可印刷区域为 true | 警卫塔排除 LandUse；需要明确隔离的街区可设 false |
| `surfaceAlgorithmDefaults[]` | 本次 intent 的算法材料默认优先 | `UNIFORM` 决定城区铺装，`CONTOUR_BANDS` 决定农业 FIELD / CHANNEL 材料 |
| `surfaceBlockId` / `cropBlockId` | group 覆写优先于本次算法默认 | 只用于广场、特殊农田等少数例外，不改变连接兼容类别 |
| 刷地算法 | `UNIFORM` 或 `CONTOUR_BANDS` | 城区统一刷地；农业按连续高程的等高线法向生成条带，平地自动径向回退 |

自动相向扩张必须同时满足：两侧 `autoConnect=true`、兼容类别相同、初次边界 gap `<=64`，并且正式扩张路径没有不可通行地形或硬障碍。是否最终接触由扩张预算和地形共同决定；`not_reached` 是可解释结果，不触发桥线或 hard fail。

### 4.3 跨功能区关系

Agent 还应为需要组织的功能区对配置关系，不把两区边界距离直接解释成必须连接：

| 关系 | 结果 |
| --- | --- |
| `merge` | 两侧语义兼容时保持自动连接开启，让 LandUse 通过正常扩张接触融合 |
| `road_seam` | 两区之间冻结道路候选通廊，LandUse 从通廊两侧退让，由道路连接 |
| `buffer` | 保留自然地表、绿化、原群系或后续装饰过渡带 |
| `separate` | 对相关 group 关闭自动连接，并禁止直接道路缝合 |

道路接缝的距离阈值只决定“是否生成直接道路候选”，不决定道路宽度。道路宽度由道路等级 profile 决定，并使用奇数宽度保持中心线对称；剩余间隔作为路肩、绿化、广场步行面或退回相邻 LandUse。

LandUse 自动近邻使用 65 格空间桶索引 block 边界，只检查周围 3x3 桶；不得枚举两条边界的全量点对。道路接缝仍是后续独立能力，不由自动 LandUse 连接替代。

### 4.4 本城镇的地表配置

| 对象 | 兼容类别 | 自动连接 | 连接口径 |
| --- | --- | --- | --- |
| 3 个农业 seed group | `CULTIVATE` | true | 放在同一服务带，64 格内相向扩张，目标是一个不规则连续农业面域 |
| 中心广场 | `PAVE` | true | 广场自身连续，入口处允许真实道路切入 |
| 市政厅与警卫厅 | `PAVE` | true | 与广场 / 相邻行政铺装自然接触，不生成窄桥 |
| 多个商业街组 | `PAVE` | true | 邻近组可接触；硬障碍分隔时依靠道路和步行带 |
| 两个居民街坊 | 按设计选择 `PAVE` 或 `PRESERVE` | 按选择默认 | 不为跨越远距离强制连接，依靠街路连接 |
| 外围警卫塔 | 无 LandUse seed | 不适用 | 只要求入口接入交通网络 |

若后续加入林场，由 Agent 在 `native_forestry`、`managed_forestry` 或 `orchard` 语义档案中选择。天然林场优先使用 `PRESERVE` 保留原群系；明确经营林需要刷地表时再显式开启。

### 4.5 全城连通验收

| 对象 | 硬约束 | 达成方式 |
| --- | --- | --- |
| 农业生产面 | 最终农业 area 单连通 | D4 服务带邻接 + 64 格自动相向扩张；不使用兜底桥 |
| 行政院落 | `civic_court` 单连通 | 市政厅、警卫厅和院落步行面共同形成连续区域 |
| 商业与居民 | 同一逻辑区内所有关键入口可达 | 由 `road_seam`、广场步行面和 RoadWeaver 实际道路连接 |
| 城区交通网络 | `PAVE surface ∪ actualRoadMask ∪ plazaWalkwayMask` 单连通 | 预规划道路接缝，RoadWeaver 落地后按真实 mask 验收 |
| 道路 | 连接各区 gateway 和关键建筑入口 | 冻结候选 corridor 后交给道路执行层生成实际路线 |

若农业 trace 为 `not_reached`，必须回到 D4 调整 seed group 的服务带落位或扩大合理预算；不得在 LandUse 后追加一格宽桥或矩形补片。

### 4.6 朝向规则

- 广场沿街建筑朝向喷泉或广场中心。
- 市政厅正门朝广场；警卫厅朝主入口或广场侧门。
- 双排商业街的建筑朝向引导线中部。
- 居民庭院组朝向院内；沿街住宅朝向街带。
- 农业建筑正面朝城市到田地的服务通道，不让谷仓大门朝向封闭石墙。

## 五、农业区设计

### 5.1 设计思路

农业区是全城占地最大、最不能被其他阵列切碎的功能区。它不使用一个矩形 target，而由多个农业建筑群沿同一侧边产生 block 级成本扩张，最终融合为一个不规则面域。

推荐拆成三个农业 seed group：

1. `farm_mill_cluster`：风车与风车谷仓，作为农业地标。
2. `farm_storage_cluster`：普通谷仓、农产品仓库和马厩，承担储存与运输。
3. `farmstead_cluster`：2-3 栋农民住宅与附属谷仓，承担生活与生产过渡。

三个 group 必须使用同一个农业规则引用和兼容的 CULTIVATE surface settings，并保持 `autoConnect=true`。不得把三个 group 放到田地三角形或矩形的三个角上，再让扩张填满中间；它们应沿城市侧的农业服务带自然错落排开，让面域向外侧土地展开。

### 5.2 建筑

| 角色 | 固定模板 | 数量建议 | 说明 |
| --- | --- | ---: | --- |
| 风车 | `geomantia:city/stubbs/agriculture/windmill_01` | 1 | 农业地标，高点或田地边缘 |
| 风车谷仓 | `geomantia:city/stubbs/agriculture/barn_windmill_01` | 1 | 与风车形成生产核心，不与风车碰撞 |
| 普通谷仓 | `geomantia:city/stubbs/agriculture/barn_01` | 1-2 | 位于服务带，面向运输通道 |
| 农产品仓库 | `geomantia:city/stubbs/agriculture/farm_storage_house_01` | 1-2 | 靠近城镇和道路一侧 |
| 马厩 | `geomantia:city/stubbs/agriculture/horse_stall_02` | 1 | 与仓储组形成院落 |
| 农民住宅 | `geomantia:city/stubbs/agriculture/farm_home_01` | 2-3 | 靠近田地入口，不散落到远端田块 |

### 5.3 建筑阵列

| group | 阵列算法 | 推荐形态 | 说明 |
| --- | --- | --- | --- |
| `farm_mill_cluster` | `compound_cluster` | `organic_compact` | 风车与风车谷仓保持视觉组合，但不做规则矩形院落 |
| `farm_storage_cluster` | `compound_cluster` | `u_shape` 或 `courtyard` | 谷仓、仓库、马厩围出装卸场 |
| `farmstead_cluster` | `guide_line_dual_side` | 单侧或错位双侧 | 农舍沿服务带排列，避免撒点 |

### 5.4 不规则田地 LandUse

- `LandUse` 使用建筑 footprint 外缘和入口作为多源 seed，在四邻域按坡度、起伏、水体、距离和稳定扰动扩张。
- 输出只认实际 claim 形成的 `memberSpans` / `boundaryLoops`，禁止使用 area bbox 填满。
- 三个农业 group 在 64 格内得到双向 guidance，正式扩张接触后融合并删除内部边界；结构、道路 corridor、异类 LandUse、水体、陡坡或未采样格仍阻断。
- `CityLandUseSurfacePrintPlan.AreaPrint.memberSpans` 必须来自最终不规则 area；owner chunk 只分片执行，不得重算 bbox。
- 禁止用 Decoration `uniform_fill/cross_section_repeat/parallel_rows` 生成耕地、作物或水槽；同一 surface-owned area 的这三类 program 必须在规划 / 激活时 hard fail。
- 农业面域不得大面积贴住 `planningBounds`；触边说明范围不足或面域被矩形边界截断。

建议增加或人工计算以下验收指标：

| 指标 | 建议门槛 |
| --- | --- |
| connected component | 必须为 1 |
| `areaBlocks / bboxAreaBlocks` | 建议不高于 `0.80` |
| planning bounds 触边 | 不允许形成长直边 |
| 内部异类孔洞 | 只允许结构 footprint、道路 corridor 或自然水体形成的可解释孔洞 |

### 5.5 田垄与水槽

视觉横断面：

```text
耕地 5 格 | 橡木半砖 | 1 格水 | 橡木半砖 | 耕地 5 格
```

`CONTOUR_BANDS` 先在完整农业 member mask 上计算连续高程与局部梯度，再沿等高线法向距离按 13 格周期分类。输出全局冻结的 `FIELD` / `BANK` / `WATER` spans 和方向来源：有稳定梯度时为 `CONTOUR_NORMAL`，连续平地为 `RADIAL_FALLBACK`。三格水槽固定解释为 `BANK + WATER + BANK`。结构 footprint、道路 corridor、gate、既有水体及其他 exclusions 在分类前扣除；owner chunk 只裁切结果，不重算等高线或相位。

实现约束：

- 水槽由 LandUse SurfacePrintPlan 的 `CONTOUR_BANDS` recipe 直接刷入，不生成 Decoration program、slot 或直线 / 端帽 NBT placement。
- 默认横截面材料沿用既有视觉：FIELD 为耕地与作物；BANK 底层为泥土并在上层放橡木半砖；中间 WATER 为水。相关材料都可由本次 intent 的运行时算法默认覆写。
- LandUse 先按冻结 mask 处理 FIELD / BANK / WATER base，再只在 FIELD mask 上批量种作物；作物和 boundary 都不能覆盖 BANK / WATER。
- FIELD / CHANNEL mask、方向来源和横截面相位必须全局冻结，跨 chunk 保持一致；不得在 owner chunk 边界重新开始条带。
- 每条 WATER 带的开放端点必须从完整全局邻接关系生成 BANK 封口；不能按 owner chunk 局部判断端点，否则跨 chunk 会出现漏水或重复封口。
- 直接 mask 执行必须验证转角水密、相邻 WATER 状态更新、地形高差处封口、事务回滚和跨 chunk 拼接；不能只凭分类 mask 正确判定世界落地通过。

### 5.6 农业装饰

| 装饰 | contentRef / 语义引用 | 布置方式 |
| --- | --- | --- |
| 稻草人 | `scarecrow` | 低密度 `deterministic_scatter`，只在田垄内部 |
| 草垛 | `haystack` | 谷仓和田地入口附近，权重大于稻草人 |
| 农具架 | `farm_tool_rack` | 农舍、谷仓和服务带边缘 |
| 饮水槽 | `animal_trough` | 马厩与农舍附近，不放入作物行 |
| 蜂箱架 | `beehive_stand` | 田地边缘少量布置 |

稻草人不得形成点阵。建议以较大的 scatter cell 和较低 density 生成，使相邻大田中只出现少量视觉焦点。

### 5.7 石质边界

- 农业 rule 使用 `boundaryPolicy=LOW_WALL`，不使用 `FENCE`。
- 当前默认 material palette 将 `LOW_WALL` 映射为 `minecraft:cobblestone_wall`，满足非木质石围墙要求。
- 只沿融合后的最终外圈 `boundaryLoops` 生成石墙；内部田块和三个农业 group 接触处不生成墙。
- 在农舍服务带、谷仓装卸口和主路接入点保留 gate，不形成封死的连续墙圈。

## 六、中心广场设计

### 6.1 设计思路

广场是全城视觉和交通中心。中心喷泉必须在第一眼可见，建筑立面围绕中心组织，而不是在一块空地上随机散放长椅。

### 6.2 建筑与装饰

| 类型 | 选型 | 数量建议 |
| --- | --- | ---: |
| 中心喷泉 | `geomantia:decoration/fountain_01` | 1 |
| 广场边小商铺 | `town_shop_01`、`bake_shop_01`、`flower_shop_01` | 3-5 |
| 长椅 | `street_bench` | 6-10，面向喷泉或主要通道 |
| 灯柱 | `lantern_post` | 4-8，放在入口与转角 |
| 公告板 | `notice_board` | 1，靠行政区入口 |
| 旗帜柱 | `banner_post` | 2-4，强调市政厅方向 |
| 小摊位 | `market_stall_small` | 少量，避免占满中心视线 |

### 6.3 阵列算法

- 父级使用 `composite_array` 建立广场 parent zone。
- 商铺子阵列使用 `plaza_ring`，优先半环或四边留口布局，全部 `faceCenter=true`。
- 喷泉不作为 D4 建筑 anchor；plaza LandUse 定稿后，先调用关键装饰锚点候选工具，按完整 5x5 footprint、clearance 和周边硬障碍生成候选，由 Agent 选择后把相对 `coordinateFramePatch` 回填给 DecorationProgram。
- 广场至少保留四个方向中的三个通道，不生成完整封闭环。

### 6.4 LandUse

- ruleRef 使用 `plaza`，`surfacePolicy=PAVE`。
- 广场自身必须是连续 PAVE 面；与行政、商业之间可直接接边，也可通过 `road_seam` 对应的石砖道路或步行带连接。
- 广场中心、建筑 footprint 和道路入口之间不得残留狭长自然地表缝隙。

## 七、行政区设计

### 7.1 建筑

| 角色 | 固定模板 | 数量 |
| --- | --- | ---: |
| 市政厅 | `geomantia:city/stubbs/civic/town_hall_01` | 1 |
| 警卫厅 | `geomantia:city/stubbs/civic/guard_outpost_01` | 1 |
| 可选行政附属 | `geomantia:city/stubbs/civic/town_hall_02` | 0-1，不与主市政厅重复职能 |

### 7.2 阵列算法

- 市政厅和警卫厅属于关键结构，先走 D4 key anchor 候选选择，不进入随机 fill pool。
- 两者外侧可用 `compound_cluster` 的 `u_shape` 组织行政院落。
- 市政厅正门朝广场；警卫厅靠主入口一侧，门面朝行政院或入城方向。
- 行政区不使用规则完整矩形庭院，U 形开口必须指向广场。

### 7.3 装饰与 LandUse

- 装饰使用长椅、公告板、旗帜柱、灯柱和少量花箱。
- 行政区使用 PAVE 地表。
- 城区内部行政边界建议保持 OPEN；若使用 LOW_WALL，只能位于外侧边界，广场侧必须通过宽 gate 保持开放。
- 市政厅与警卫厅配置为同一个 `civic_court` 连续性组，必须属于同一 civic 连通组件。

## 八、商业与功能建筑区设计

### 8.1 设计思路

商业区不做单栋功能建筑孤岛。每个主要功能建筑和 3-4 栋小型住宅或附属房屋组成一个可读的混合街组，再让多个街组沿广场连续生长。

### 8.2 功能街组

| 街组 | 主要建筑 | 附属建筑 | 阵列算法 |
| --- | --- | --- | --- |
| 酒馆服务街 | `tavern_01`、`motel_01` | 3-4 栋 `village_house_small_*` / `household_*` | `guide_line_dual_side`，错位双侧 |
| 市场零售街 | `general_store_01`、`town_shop_01`、`bakery_01`、`small_butcher_shop_01` | 4-6 栋小住宅 | `guide_line_dual_side`，两侧朝内 |
| 工坊仓储街 | `town_workshop_01`、`merchant_house_01`、`farm_storage_house_01` | 3-4 栋住宅或工人房 | `composite_array` + 双排子阵列 |
| 文化服务节点 | `library_01`，可选 `theater_01` | 2-3 栋城市住宅 | `compound_cluster`，靠广场但不抢中心 |

### 8.3 连通与装饰

- 所有商业街组使用同一个 commercial ruleRef 和 `central_commercial` 逻辑区，但不要求 commercial LandUse 物理融合。
- 每个商业 array zone 只注册 1-3 个 RoadWeaver gateway，不给每栋小屋单独拉路。
- 商业装饰使用市场摊位、招牌、木箱、桶和少量长椅；物流装饰靠仓库，摊位靠广场。
- 商业 LandUse 使用 PAVE；与 plaza 的连接可由 PAVE 接边或真实道路完成，禁止为了连片生成狭长 commercial 石砖桥。
- `guide_line_dual_side` 只负责建筑秩序，不等于真实道路；RoadWeaver 完成后必须检查道路是否落在两排建筑之间。

## 九、居民区设计

### 9.1 建筑池

- 城市住宅：`city_home_01`、`city_home_02`
- 普通住宅：`civilian_house_01`、`civilian_house_02`、`civilian_house_03`
- 家庭住宅：`household_01` 至 `household_07`
- 小型填充住宅：`village_house_small_01`、`village_house_small_02`
- 可选公共住宅：`dorm_for_the_poor_01`

目标数量为 24-30 栋，不要求每种模板都出现，但同一模板不得连续重复形成复制感。

### 9.2 阵列算法

居民区使用两个相邻的 `composite_array` parent group：

1. 北部居民街坊：拆成两条 `guide_line_dual_side` 排屋带，建筑朝向街中。
2. 东部居民街坊：拆成一个 `courtyard` 子阵列和一个 `organic_compact` 子阵列，形成院落与边角填充。

规则：

- 不用单一完整 grid 覆盖整个居民区。
- 不用 `plaza_ring` 生成住宅环形点阵。
- 允许 1-2 格级局部错位，但主街立面要保持秩序。
- 大住宅位于街角或靠近商业区，小住宅填补内部与边缘。

### 9.3 LandUse 与装饰

- 两个居民 parent group 使用同一 residential ruleRef；若保留自然地表则关闭印刷 / 自动连接，若选择 PAVE 则允许邻近铺装自然接触，但仍可被主路硬分隔。
- 当前建议居民院落保留自然地表，由真实道路接入；不把所有住宅空地铺成整块石砖。
- 装饰使用柴火堆、晾衣绳、花箱和高架菜圃，按街坊 remaining mask 分散布置。
- 居民装饰不得阻塞门口、道路 gateway 或街坊中心通道。

## 十、警卫与防御设计

### 10.1 建筑

| 位置 | 固定模板 | 作用 |
| --- | --- | --- |
| 滨水侧 | `geomantia:city/stubbs/civic/guardian_tower_01` | 观察水岸与西侧入口 |
| 北侧外缘 | `geomantia:city/stubbs/civic/guardian_tower_02` | 覆盖行政和居民区外缘 |
| 南侧农业入口 | `geomantia:city/stubbs/civic/guard_tower_03` | 保护田地入口和南向道路 |
| 可选主入口 | `geomantia:city/stubbs/civic/guard_gate_01` | 明确入城门面，不强制生成完整城墙 |

### 10.2 落位规则

- 警卫塔属于关键结构，逐个选择外围候选，不进入批量住宅或商业 fill pool。
- 外围塔通过 `subjectOverrides mode=exclude` 排除 LandUse，避免形成远离行政核心的孤立 civic 小岛。
- 塔楼入口必须能够接入道路或步行通道，不能落在石墙外且无门。
- 本案不强制完整城墙；如后续启用 City Walls，应以道路、农业石墙和真实 footprint 为约束重新规划。

## 十一、设计与执行顺序

### 阶段 0：W 与世界状态确认

1. 锁定 sealed W 来源和宏观候选。
2. 只读检查目标 region / owner chunk 未到 FEATURES。
3. 若目标区已生成，放弃该候选，不走 late paste。

### 阶段 1：D3 局部精扫

1. 对候选范围和 context margin 执行 D3。
2. 识别城区核心、农业连续面域、水岸、陡坡和未采样区。
3. 输出 D3 preview，由 Agent 选择最终城区朝向和农业展开方向。

### 阶段 2：目录与关键结构确认

1. 查询并冻结本案全部固定模板的尺寸、hash、rotation 和 road entrance。
2. 查询装饰 catalog，确认喷泉、长椅和稻草人可用；水槽不再依赖 Decoration prefab catalog。
3. 校验本次 LandUse intent 的 FIELD、BANK、WATER 与 BANK overlay block ID 均已注册；非法材料不进入世界激活。

### 阶段 3：D4 关键结构

按顺序逐个规划并选择：

1. 市政厅。
2. 警卫厅。
3. 风车。
4. 风车谷仓。
5. 三座警卫塔和可选主门。

每个结构选择后更新 occupied field，后续不得回填到已占用一侧。

### 阶段 4：D4 农业建筑群

农业是面积最大且最怕碎裂的区域，必须在住宅填充前完成：

1. 风车生产组。
2. 谷仓仓储组。
3. 农舍服务组。
4. 检查三个 group 的探测边界 gap 不超过 64 格，且正式相向扩张可以在地形与预算内自然接触。

### 阶段 5：D4 广场与行政院落

1. 建立 plaza parent zone。
2. 用 `plaza_ring` 生成面向中心的商铺边界。
3. 将市政厅和警卫厅组织为向广场开口的行政院落。

### 阶段 6：D4 商业功能街

按“市场零售街 -> 酒馆服务街 -> 工坊仓储街 -> 可选文化节点”的顺序逐组生成。每组都先生成完整候选，再由 Agent 选择，不自动提交最高分结果。

### 阶段 7：D4 居民街坊

1. 北部双排街坊。
2. 东部院落与紧凑簇街坊。
3. 用小型住宅填补 remaining mask，但不得破坏主要通道和农业连续空间。

### 阶段 8：D4 finalize、D5 预案与 D6 锁定

1. 汇总标准 `StructureAnchorPlan`。
2. D5 生成轻量 reservation / wall / corridor 上下文。
3. D6 锁定所有模板的 actual footprint、collision 和 signature。
4. 任一关键结构锁定失败时回到对应 D4 候选，不让后续 LandUse 绕过失败。

### 阶段 9：LandUse

1. 按建筑与 D6 footprint 生成 agriculture、plaza、civic、commercial、residential 探测扩张结果。
2. 本次 intent 用 `surfaceAlgorithmDefaults[]` 传入全城 `UNIFORM` / `CONTOUR_BANDS` 材料默认；Agent 只为少数例外 group 冻结 `surfaceOverrides[]`。农业统一 CULTIVATE，城区按 PAVE / PRESERVE 设计选择。
3. 程序从探测边界用空间桶发现 64 格内全部兼容近邻，并为双方建立 guidance。
4. 正式扩张按方向、地形代价和硬障碍自然接触，不生成补桥。
5. 编译最终 LandUse geometry，检查农业单连通、非矩形和石墙只位于最终农业外圈；`not_reached` 回到 D4 调整。
6. 冻结 SurfacePrintPlan：不规则 member / exclusion spans、解析后的运行时材料、`UNIFORM|CONTOUR_BANDS` recipe，以及 CONTOUR_BANDS 的 FIELD / BANK / WATER spans、`CONTOUR_NORMAL|RADIAL_FALLBACK` 和全局端点封口结果。
7. 检查规划期交通网络候选连通；不要求不同兼容类别在此阶段直接组成单一面域。

### 阶段 10：Decoration

1. 为喷泉生成 1-8 个关键装饰锚点候选，审阅 footprint / clearance / hard obstacles 后选择一个相对坐标 patch。
2. 若后续加入雕像、水井等其他 required 单点装饰，按顺序选；每次都携带前面已固定的单点 program，使其进入装饰冲突避让。
3. 农业散点装饰。
4. 广场普通设施，以及商业、行政和居民生活装饰。
5. terrain probe 与 activation preview 审阅。

本案最终采用的 `city_decoration_program_plan.v0.4` 如下。密度参数已经过正式 planning preview 审阅；后续若再次调整，必须重新生成并审阅 preview。

| programId | target / shape | pattern | 语义内容 | 关键参数 | priority |
| --- | --- | --- | --- | --- | ---: |
| `farm_scarecrows` | `agriculture_main_farmland`，inset 8，`target_mask` | `deterministic_scatter` | `scarecrow` | cell 24、density 250 permille、clearance 2 | 80 |
| `farm_life_accents` | `agriculture_main_farmland`，inset 7，`target_mask` | `deterministic_scatter` | `haystack` / `farm_tool_rack` / `beehive_stand` / `animal_trough` | 权重 4/3/2/1；cell 18、density 700 permille、clearance 2；最终 11 slot | 70 |
| `plaza_fountain_center` | `plaza_central_plaza`，inset 2，局部 `0,0` 单点 | `grid_repeat` | `fountain` | 先由 `city_plan_decoration_anchor_candidates` 生成候选，选择后回填 `coordinateFramePatch`；clearance 2；最终恰好 1 slot | 200 |
| `plaza_bench_ring` | `plaza_central_plaza`，inset 2，椭圆环半径 7..12 | `deterministic_scatter` | `street_bench` | cell 2、density 1000 permille、clearance 1；最终 5 slot | 150 |
| `plaza_lantern_ring` | `plaza_central_plaza`，inset 2，`target_mask` | `edge_repeat` | `lantern_post` | 沿实际 plaza 边缘 spacing 18、offset 2、clearance 1；最终 27 slot | 140 |
| `civic_accents` | `civic_civic_court`，inset 0，`target_mask` | `deterministic_scatter` | `notice_board` / `banner_post` / `street_bench` | 权重 2/3/2；cell 10、density 800 permille、clearance 1；结构 obstacle 继续扣除；最终 9 slot | 100 |
| `commercial_street_life` | `commercial_central_commercial`，inset 3，`target_mask` | `edge_repeat` | `market_stall_small` / `crate_cluster` / `barrel_cluster` / `shop_sign` | 权重 2/3/3/2；沿实际商业边缘 spacing 8、offset 1、clearance 1；最终 3 slot | 90 |
| `residential_street_life` | `residential_east_residential`，inset 0，`target_mask` | `deterministic_scatter` | `firewood_pile` / `clothesline` / `flower_box` / `raised_garden_bed` | 权重 3/2/3/2；cell 14、density 300 permille、clearance 1；结构 obstacle 继续扣除 | 80 |

历史 planning 快照曾由 Decoration 投影水槽 562、作物 slot 10,552；该数字不再是当前验收口径。重跑后，批量耕地 / 作物 / 水槽数量必须从 `city_land_use_surface_print_plan.json` 与 LandUse ledger 读取，Decoration quality 只统计喷泉、稻草人、长椅和生活点缀等稀疏内容。

历史喷泉快照曾由 Agent 手算 target centroid 偏移 `U=-2,V=8`，得到诊断 world point `(651899,652408)`；该值只用于解释旧测试过程，且旧 ledger 最终以 `CITY_DECORATION_HARD_OBSTACLE_CONFLICT` 跳过。后续不得复用该 offset 或 world point，必须重新生成候选。

执行约束：

- SurfacePrintPlan v0.2 owner 直接消费冻结的 FIELD / CHANNEL role spans，先写地表、水槽与 BANK overlay，再只在 FIELD 写作物；边界最后执行且必须避让所有 channel role。任一阶段失败全事务回滚。
- WATER 开放端点与高差终点使用规划期冻结的全局 BANK 封口，不允许 owner 局部生成端帽或引用 Decoration prefab。
- 农业石墙来自 LandUse `LOW_WALL` boundary，不重复使用 `field_border` Decoration。
- fountain 候选必须用完整 footprint + clearance 校验并避开 structure、wall、gate/gateway、LandUse gate/corridor 与已固定关键装饰；Agent 只选择 candidate 并回填相对 patch。若候选为空，回到 plaza 构图或 LandUse 调整，不手写 offset / 世界坐标绕过。
- 当前 scatter 不保证长椅面向 centroid；preview 先验收数量和位置，朝向若明显不自然列入最后修缮或后续补 `face_target` 语义。

### 阶段 11：激活与首次 worldgen

1. `execute_d5` 校验并激活结构、LandUse AreaPlan + SurfacePrintPlan、稀疏 Decoration 和 RoadWeaver 连接计划；道路端点来自已冻结结构入口。
2. 从目标区外侧触发首次 chunk 生成。
3. 查询 D7 ledger，确认所有 planned structure / LandUse owner / Decoration fragment 完整。
4. RoadWeaver 后写真实道路，并拥有最终道路地表覆盖权。

## 十二、最后修缮思路

最后修缮不是重新规划城市，而是消费已经锁定的实际 footprint、LandUse、道路和 ledger 修复可解释的小缺口。

### 12.1 城区连通修缮

- 以真实 LandUse surface、`actualRoadMask` 和 plaza walkway mask 检查所有关键建筑入口是否属于同一可达网络。
- 预期自动接触的兼容组得到 `not_reached` 或出现断裂时，必须回到 D4 / LandUse 重算，不允许用道路掩盖农业失败。
- 被道路或硬障碍分隔的城区可以保持多个组件；只有入口不可达、道路未穿过冻结 corridor 或出现无法解释的自然地表断口时才修缮。
- 小于约 3-5 格、且原本被定义为步行连接的自然地表缝隙，可通过独立石砖步行带 program 补齐；不得把所有跨类型缝隙自动铺满。
- 大面积断裂不得事后铺路掩盖，必须回到功能区关系选择、D4 候选或 LandUse 重新规划。

### 12.2 农田修缮

- 检查整体轮廓是否仍像矩形；不合格时重跑 LandUse，不用装饰删角伪装。
- 检查弯曲水槽的 BANK / WATER / BANK 横截面连续，转角没有露水或缺边。
- 检查水槽跨 chunk 不重启、不重叠、不在边界突然断水；开放端点均由全局封口闭合。
- 检查作物没有覆盖橡木半砖衬边。
- 检查稻草人稀疏且无规则点阵。
- 检查石墙只有外圈，内部融合边界没有残墙。
- 检查谷仓、马厩和农舍入口存在可通行 gate。

### 12.3 广场与功能街修缮

- 清除喷泉与主通道之间过密的摊位或长椅。
- 长椅朝向喷泉或街面，不背对主要空间。
- 商业双排建筑之间必须有真实道路或连续步行带。
- 酒馆、商店和工坊周边的小屋保持整齐，但用模板变化和局部错位避免复制感。
- 木箱和桶只靠仓储与商店后侧，不散落在行政区和喷泉中心。

### 12.4 居民区修缮

- 检查每栋住宅门口可达，避免房屋背面对街。
- 检查两个街坊形态明显不同，不能都退化为 grid 或环形点阵。
- 用柴火堆、晾衣绳、花箱和菜圃填补小型生活空地，不在道路上投影装饰。

### 12.5 防御与入口修缮

- 三座警卫塔必须各自覆盖一个不同方向，且入口可达。
- 农业石墙、主路和警卫塔之间保留明确门洞。
- 若后续生成城墙，城墙不得切断农业服务路或 RoadWeaver 实际道路。

### 12.6 最终人工验收

至少保留以下材料：

- D3 地形 preview。
- D4 最终城市构图 preview。
- LandUse preview，显示 continuity group、同类融合、道路接缝 corridor、农业边界和 gate。
- 喷泉关键装饰候选集与候选预览，显示完整 footprint、clearance、hard obstacles、固定装饰和 `terrainSampling=not_performed`。
- LandUse SurfacePrint preview，显示 FIELD、两侧 BANK、WATER、END_CAP 和跨 chunk 全局相位；Decoration preview 只显示散点装饰。
- D7 placed structure preview 和 worldgen ledger 摘要。
- 城镇四向俯视截图、广场视角、农业区视角和居民街坊视角。

人工只需判断：整体是否像一座连续、繁华、有人生活的大城镇；农田是否真正表现为不规则大面域；水槽、石墙、道路和建筑朝向是否自然。

## 十三、当前能力与待补缺口

### 已有能力

- D4 key / array / composite array、双侧排列、院落、U 形和紧凑簇。
- 固定 NBT 模板、运行时尺寸 / hash 查询和 D6 footprint 锁定。
- block 级两遍 LandUse 成本扩张，以及 64 格内兼容地表的自动双向 guidance；不再有事后补桥。
- LandUse `memberSpans` 驱动的不规则 SurfacePrintPlan 和稀疏 Decoration target mask。
- `UNIFORM` 单方块刷地，以及 `CONTOUR_BANDS` 的 `5+3+5` FIELD / CHANNEL 分类、等高线法向和连续平地径向回退。
- 跨 chunk 全局 FIELD / BANK / WATER mask、端点封口、prepared owner index 和当前 ledger。
- 喷泉、长椅、稻草人、农具、草垛、市场摊位等运行时装饰素材。
- required 单点装饰的 footprint + clearance 候选、固定装饰顺序避让和相对坐标 patch。
- `PAVE -> minecraft:stone_bricks` 和 `LOW_WALL -> minecraft:cobblestone_wall`。

### 执行前需要核对或补齐

- 当前程序没有农业矩形度 hard fail；本案先以 preview + 人工指标验收，后续可新增质量校验器。
- 当前目标契约为 `city_land_use_intent_plan.v0.3`：运行时算法材料默认优先、group 覆写处理例外；旧 v0.2 `global_axis|radial` 不再作为目标输入。跨区 `road_seam / buffer / separate` 关系仍未进入契约。
- 自动相向扩张不保证最终单连通；地形或预算导致 `not_reached` 时必须回到 D4 调整农业服务带，不能补桥。
- 当前 RoadWeaver 连接计划主要消费结构入口，尚未证明能够严格消费冻结的 `road_seam` corridor；实现前必须补齐 corridor 交接或明确受限路线能力。
- 不同兼容类别不会自动连接；本案以道路接缝和最终实际道路网络解决跨类型可达，不恢复跨类型 LandUse 强制融合。
- D3 当前只提供粗格高程；若直接求梯度，等高线可能出现台阶化和方块化。首版必须显式经过连续插值 / 平滑后再分类，并用预览确认轮廓；不能把粗 cell 边界当作真实等高线。
- 弯曲水槽改为直接 mask 落地后，不再受直线 / 端帽素材限制；新增风险转为 WATER 邻接更新、转角水密、全局端点封口和跨 owner 事务一致性，必须用自动测试与实机共同验收。
- 三格水槽由 `CONTOUR_BANDS` 的 CHANNEL 角色掩码直接冻结；作物、边界与水槽的冲突由同一 owner 事务中的 exclusion / role 校验解决，不依赖 Decoration program 优先级。
- `guide_line_dual_side` 的引导线不等于真实道路；RoadWeaver 结果仍需单独验收。
- 居民院落是否整体石砖化暂按“保留自然地表、道路接入”处理；如改为全铺装，需要单独调整 residential rule profile。
