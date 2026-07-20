# City 案子：建筑驱动 LandUseAreaPlan v0.1

补充文档：

- [建筑素材采集名称表](./建筑素材采集建议表.md)
- [装饰素材采集与简易制作清单](../City通用装饰阵列系统-v0.2/装饰素材采集与简易制作清单.md)

## 状态

当前开发案。首期以配置默认关闭的可选层接入现有 City workflow；实现、契约、自动测试完成后再单独决定是否切默认。

## 一、目的

建筑后置派生：在 D4 已确定关键建筑、普通建筑、阵列和组合关系之后生成土地使用区域，不恢复“先画功能区再塞结构”的旧主线。

城市空间连续化：把农田、花海、林场、鱼塘、广场、庭院和市场等内容组织成跨越多个 chunk 的连续不规则区域，避免直接沿用 D3 member cell 或 chunk 方格形成生硬边缘。

通用区域生成：以一套多源行动力扩张算法生成不同用途的区域形状，具体用途只改变土地需求、扩张成本、合并规则、地表策略和装饰内容，不为农田、花海或广场分别维护专用形状算法。

D4 设计延续：保留 D4 显式 group、array zone 和 composite array 的组合意图，使喷泉与商铺可共同形成广场，多个住宅可共同形成街坊，而不是让每栋建筑都独立生成一圈区域。

自然环境保护：土地使用区域只描述几何归属和用途，不自动等同于植被抑制 mask；林场可以保留原版或地形模组生成的树木，仅在围栏、道路、建筑净空和装饰实际槽位抑制植被。

结果可解释可复现：固定输入、规则版本和 seed 必须得到相同区域，并能解释每个 block 被某个区域取得、阻断、争夺或保留为空地的原因。

## 二、方案

阶段位置：D3 负责 LandUse 粗格地形事实，D4 负责 block 坐标建筑、阵列落位和 group provenance；D5 先生成不会依赖最终 LandUse 几何的轻量预案，D6 再锁定实际 footprint。`LandUseAreaPlan` 只能在 D6 locked plan 之后定稿，随后交给 DecorationProgram，最后由 `execute_d5` 激活 worldgen 计划。

扩张主体：算法以 `LandUseSeedGroup` 为竞争主体；每个主体包含稳定 group ID、用途、结构引用、种子几何、目标面积范围、行动力预算、成本档案、合并策略、边界策略、植被策略和地表策略。

显式分组：D4 已明确为 group、array zone 或 composite array 的结构先合并成一个 `LandUseSeedGroup`，组内成员不互相竞争；混合类型结构允许由组合关系得到新的整体用途，例如“喷泉 + 朝内商铺”得到 `plaza`。

普通建筑：未被显式分组的建筑各自成为独立扩张种子，按建筑实际 footprint 和 TerraSense 用途事实派生土地需求；后续只有在用途和合并策略兼容时才自动融合。

种子几何：多源起点优先使用建筑 footprint 外缘、真实 road entrances 和组内朝向关系，不把建筑中心点作为唯一种子；入口方向、建筑背面和阵列内侧可以获得不同扩张成本。

土地需求：目标面积由“建筑 footprint 面积乘用途倍率 + 用途额外土地需求”派生，同时保留 `min/preferred/max` 范围；农舍可以以较小建筑取得大面积农田，教堂或大建筑也不会仅因 footprint 较大就无限取得外部土地。

行动力扩张：参考国度 T3 的多源行动力模型，在局部 block 网格上用稳定优先队列按累计成本扩张；LandUseAreaPlan 复用预算停止、地形成本、屏障、竞争和未占区域思想，不直接复用国度粗尺度 WorldCell 实现。

扩张成本：单步成本由基础移动成本、坡度、高差、水体、悬崖、建筑和道路障碍、距种子距离、紧凑度、入口方向、用途亲和与确定性扰动共同组成；成本档案由程序根据用途派生，不让 AI 提交不可解释的裸参数表。

同类融合：不同主体具有相同土地用途且 `mergeSameType=true` 时，扩张前沿接触后合并为连续区域，不再互相挤占，并删除接触处内部边界；主路、河流、围墙或显式分区可以阻止同类融合。

近邻桥接：常规行动力扩张结束后，同 `ruleRef` 的不同 LandUse 主体可在 `nearbyMergeMaxBridgeBlocks` 限额内，穿过未归属、已采样、平缓且非水体的自然 block 取得最短桥接路径。建筑 footprint、gate / D5 corridor、异类 LandUse claim、未采样格、陡坡与水体都是硬障碍。`[商业] [行政] [商业]` 的行政区域不会被改写；商业仅在存在合规空地路径时绕开它形成连续区域。候选按路径长度、ruleRef、稳定组件 ID 排序，只接受尚未属于同一并查集簇且路径仍未被占用的候选，因此每次规划不会重复处理同一组件或形成桥接环。

异类竞争：不同土地用途到达同一 block 时由累计成本、土地需求完成度和竞争权重决定归属；成本接近时允许记录 contested 边界，已经达到最大面积的主体停止继续争夺。

开放空间：算法不要求把城市范围全部分完，未被任何主体取得的 block 保留为 natural、wild、corridor、blocked 或 unreachable，供自然地貌、道路缓冲、未来扩建和野外内容继续使用。

Block 级结果：D3 的 16/32 格 member cell 只作为允许范围和粗地形成本来源，最终区域成员、边界、入口、孔洞和排除区必须细化为 block 坐标；内部可使用 scanline spans 或多边形压缩保存，但不能把 chunk 当作形状单位。

生成期边界：规划阶段不得为了读取真实 block 而主动加载未生成 chunk；worldgen 在每个 owner chunk 内使用同一全局区域、坐标系和 seed，并结合当前真实地表逐 block 裁剪，跨 chunk 不重新起算扩张、边界或装饰相位。

几何策略分离：`LandUseAreaPlan` 只提供区域几何、来源和用途；`surfacePolicy`、`vegetationPolicy`、`boundaryPolicy` 和 DecorationProgram 分别决定换地板、保留或清理植被、生成围栏围墙以及布置装饰，禁止把区域成员直接全量复制为 `noVegetationMask`。`CULTIVATE` 只保留用途语义，不生成 interior farmland surface operation，农田内部由 Decoration tile / prefab 接管。

PAVE 微整地：新默认 material palette 以保留键 `MICRO_FILL_SUBGRADE=minecraft:dirt` 开启硬质铺装区的 fill-only 微整地。FEATURES 只读取真实最上层高度，用 7x7 局部中位高度判定目标；仅补高 1..3 格、连通低洼最多 16 格且 X/Z 跨度均不超过 4 格的同 area 封闭小坑。低洼跨出 PAVE mask、进入 footprint / corridor / gate、连接成开放沟谷、邻近水体或需要更深填充时保持原地形。不得削高地、填地下洞穴、填山谷或把整个 LandUse 区域做成 foundation。

下游交接：区域输出至少保留 group 来源、成员几何、结构 footprint 排除区、道路排除区、boundary loops、gate slots、claim cost 和来源种子；DecorationProgram 后续增加 LandUseAreaPlan target 引用，D5 只为实际地表替换、边界和装饰投影生成精确 mask。

广场组合：喷泉与中心阵列商铺先组成 `plaza` group，以喷泉、商铺朝内入口和阵列内侧为多源种子，在排除建筑 footprint 与主路后扩张并闭合内部空隙；区域地表可统一替换，边缘和内部再分别布置花坛、长椅、路灯和摊位。

农田花海与林场：农田和花海使用相同区域扩张器但采用不同土地需求、紧凑度、地形成本和 DecorationProgram；CULTIVATE 不由 LandUse 铺 farmland，边界仍可按 policy 生成；林场优先利用已有森林群系并保留自然树木，只生成边界、入口、林间路和少量功能建筑。

鱼塘处理：已有水体鱼塘可以由区域扩张选择连续水面并装饰岸线；需要新挖池塘时，LandUseAreaPlan 只负责平面区域和边界，体积挖掘、池底分层与注水必须交给独立的受控地形改造能力。

确定性规则：固定 `cityId + groupId + ruleVersion + seed` 决定扩张顺序和扰动，相同成本使用稳定坐标与 ID 排序打破平局，禁止因 chunk 生成顺序不同产生不同区域。

## 三、锁定主流程

首期顺序固定为：

```text
D3 LandUseTerrainField
-> D4 v0.2 anchors / group provenance
-> D5 轻量预案
-> D6 locked actual footprint
-> LandUseAreaPlan
-> DecorationProgram
-> execute_d5 激活
-> 首次 FEATURES owner-chunk worldgen
-> RoadWeaver 真实道路后写覆盖
```

- D5 预案仍可先准备结构、城墙、道路入口和 reservation 上下文，但不得在 D6 前冻结 LandUse 区域。
- LandUse 使用 D6 `lockedActualFootprint` / `lockedCollisionEnvelope` 做硬排除，避免计划穿过真实结构体积。
- DecorationProgram 可以引用 `LandUseAreaPlan.areaId`，沿同一 block mask、坐标系和 seed 生成地表细节与功能装饰。
- RoadWeaver 不属于 LandUse 扩张器。LandUse 不猜测其最终路线；真实道路后写并拥有最终地表覆盖权，区域的用途归属不因道路穿越而消失。

## 四、首期输入真值

### D3 LandUseTerrainField

D3 在现有 patch 摘要之外补 `city_land_use_terrain_field.v0.1`。每个粗格保留高度、高差 / 坡度、水体、群系和可达性等地貌事实，供 block 级扩张插值成本使用。它是只读规划事实，不允许为了提高精度主动加载未生成 chunk。

### D4 v0.2 provenance

D4 anchors 必须携带可重建组合关系的稳定 provenance：显式 placement group、array / composite array 路径、来源 design slot、结构语义和 anchor identity。LandUse 以显式 group 为一个主体；未进入任何 group 的 anchor 才成为独立主体。不得从相邻 bbox 反猜 group。

### D6 locked footprint

最终种子几何和结构排除区只认 D6 locked plan。D4 planned footprint 可用于早期预览和 D5 预案，不得作为最终 LandUse 穿越判断的权威。

## 五、规则与人工覆写边界

- 程序通过 `config/geomantia/city_land_use/profiles/<profileId>.json` 加载 `LandUseRuleCatalog`，由结构语义派生用途、面积范围、成本档案、融合 / 近邻桥接策略和 surface / vegetation / boundary / decoration policy；`settings.json.profileId` 选择档案。规则改动会改变 rule profile hash，既有 LandUse plan 必须重跑后才能激活。
- bundled `default_v0_1` 包含 `industry`：`function.矿业`、`mining`、`mine`、`quarry`、`workshop` 等语义统一派生为工业区域，并使用 `decorationPolicy=industry`。
- AI / 人工只允许提交稳定 group、成员 anchor 和 `ruleRef`，或对 group / anchor 执行 `set_rule`、`exclude`；不得提交裸面积、行动力、竞争权重、近邻桥接阈值或逐项成本。
- 规则优先级为 `subjectOverrides` > `groupOverrides.ruleRef` > D4 结构语义自动解析；未知 target、成员冲突或未知规则必须 hard fail，无法从语义解析的主体 warning 并跳过。
- 固定输入、规则 profile、`seedSalt` 和版本必须得到完全一致的 spans、边界和 claim trace。

## 六、开关与生成边界

- 外部配置根目录为 `config/geomantia/city_land_use/`：`settings.json` 的 schema 为 `city_land_use_settings.v0.1`，bundled 默认值为 `enabledInWorkflow=false`、`profileId=default_v0_1`；同目录 `profiles/default_v0_1.json` 是 `city_land_use_rules.v0.2` 规则真值。每条 rule 的 `nearbyMergeMaxBridgeBlocks` 决定一次近邻桥最多可新增多少自然 block，`0` 表示关闭；默认商业 / 工业为 24，农业 / 林场为 32，广场 / 行政为 16，住宅 / 通用聚落为 20，鱼塘为 0。既有 `v0.1` 用户档案兼容读取并映射到同一默认阈值，目录或缺失的 bundled 文件会补装，但绝不覆盖用户已有 settings / profile。
- `city_run_workflow.enableLandUseLayer` 是单次请求覆写，优先于 settings。独立调用 `city_plan_land_use` 本身就是显式规划，不受 workflow 开关阻止。
- `confirmWorldMutation=false` 时只产出规划与预览，不激活 worldgen registry。激活前必须只读检查所有 member / boundary owner；任一已到 FEATURES 整体拒绝 `CITY_LAND_USE_CHUNK_ALREADY_AT_FEATURES`，磁盘状态无法证明时整体拒绝 `CITY_LAND_USE_CHUNK_STATUS_UNKNOWN`。
- worldgen 只处理尚未经过 FEATURES 的当前 owner chunk。运行期遇非 `WorldGenRegion` 或已生成 chunk 返回 `CITY_LAND_USE_OLD_CHUNK_NOT_BACKFILLED`，不写方块、不补 ledger。
- owner 内按稳定坐标顺序先执行 PAVE 微填基层与抬高 surface、再执行 boundary，LandUse 完成后才进入 Decoration；任一方块写失败必须逆序回滚，整 owner 成功后才记录 applied ledger。
- 首期不回填旧 chunk、不自动回滚已落地 chunk、不削地、不挖三维鱼塘、不把整个 LandUse mask 复制成植被抑制区。旧 active palette 没有 `MICRO_FILL_SUBGRADE` 时保持原行为，不静默启用微整地。

## 七、首期验收

- 显式 group、array / composite group 和未分组单建筑都能得到正确主体，且同组成员不互相竞争。
- 至少覆盖接触同类融合、近邻同类桥接、绕开异类功能区、最大面积停止、自然空地、道路后写和固定 seed 确定性；三组同类近邻只接受两条桥接，不得形成循环。
- 输出为 block spans / boundary loops，而不是 chunk 或 D3 cell 形状；跨 chunk 分片执行与整图结果一致。
- 林场能保留自然植被，农田 / 广场等只按 policy 生成精确 surface、boundary 和 Decoration 投影。
- active plan hash、owner fragment 和 ledger 幂等；旧 chunk 拒绝、写失败回滚和重启恢复有自动测试。
