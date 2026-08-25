# City 当前产品案

本目录只保留当前实现仍在运行的产品说明。已替代方案、完成后的开发计划、未来草案和单次测试城市均已删除；legacy/debug endpoint 的精确输入输出只维护在 MCP 契约和测试入口。

## 当前案子

| 案子 | 实现状态 | 当前作用 |
| --- | --- | --- |
| `City意图驱动PCG城市生成-v0.1` | **架构缺陷修订**，待实现 | 城市只以功能明确、界限分明、有主有次为核心；AI 只决定城市意图，全部建筑由 PCG 自动生成。普通坑洼由台基或不落地消化，不再把 Agent Loop 变成逐栋建筑求解器。 |
| `City嵌套阵列与关系位置-v0.1` | active | 正式 Blueprint 允许父阵列排列子阵列，并按 Patch、边界和建筑群关系定位；广场、码头先作为录制结构，异构子阵列分别使用地形限制。 |
| `City阵列拓扑分类与功能约束-v0.1` | 开发中 | 按阵列拓扑归并空间落地模式；功能只提供地形、台基、地表关系和密度约束，功能区扩张不再把所有建筑群当作同一种形状。 |
| `City阵列主从骨架与街带-v0.2` | 新修订需求案，待实现 | 核心规则型阵列硬骨架化：统一固定格距、锁世界轴、禁止 fallback 跳格、槽位留空、不被采样粗网格吸附；GRID 产街巷网、COURTYARD 中心留空最小 4 栋围合、LINEAR 与 CENTER_SYMMETRIC 补强主建筑锚点、COMPACT 产弯曲小巷、ORGANIC_COMPACT 缝隙即路；区内道路全归阵列算法；质量门禁增加视觉几何指标。 |
| `City主从路网与景观层-v0.1` | 已实现，三区真实游玩验收通过 | 密度继续由阵列表达；D4 HIERARCHICAL 父阵列预留并生成宽于区内路、避水避崖避建筑、只走 90° 的城市主路，窄街口以 transition 接入；全部正式路由 SurfacePrint 落地外侧台阶路缘和中间 bottom slab。outward fill 自动冻结带路、有墙界和道路门洞的住宅子区；结构目录可选 FREEFORM/FIELD_GRID 绿化地块，必留门口引路并按城市 style palette 加权落植物。行政/市场居民/农业三区只作为 rtf0810 测试用例；农田林场继续逐 block 不规则景观扩张。 |
| `City景观约束松绑-v0.1` | **设计缺陷修订**，已实现，三区真实游玩验收通过 | 约束只为美观与工整服务，禁止规划洁癖型硬限制；景观只保留地形门禁，required 松绑为"位置形状交给地形、长不出降级警告"，ATTACHED 松绑为种子向外生长，Patch 锁定松绑为允许向周边好地出界；界限分明靠建筑肌理与道路，不靠 Patch 线。 |
| `City功能区预分配与受约束扩张-v0.1` | 开发中 | 功能区先确定最低、目标和上限容量，再按地形与道路约束扩张；建筑群在扩张后的可行范围内落位，避免区域过小或景观被挤成零占地。 |
| `City区域扩张高差边界优化-v0.1` | 下一步优化 | 扩张逐边检查高差；缓坡继续生长，高落差停止并收缩零星边界，连续崖边可自然生成矮墙。 |
| `City台基与地形适应-v0.1` | 开发中 | 硬质城市建筑按完整占地验证并使用连续台基；农田、林场、牧场保留地形且禁止跨越明显断层。 |
| `City景观扩张与区域接力-v0.1` | 最新需求案 | 景观 Parcel 外部可从新起点接力或回到旧起点分支，内部区域继续逐格接力生长；禁止固定图形与失败 fallback。 |
| `City固定模板唯一落地主线-v0.1` | active | 固定 NBT identity、D4-D6 几何冻结、single-piece StructureStart 和 worldgen ledger。 |
| `City单次蓝图户外空间编译-v0.1` | active，Landscape 组合多样性未完成 | CityBlueprint v0.11、Reference Catalog v0.9、单一 Foundation、Landscape/Group 总预算和区域接力；Landscape semantic contentWeights 世界落地仍是独立功能缺口，不影响本案建筑绿化 palette。 |
| `City建筑驱动LandUseAreaPlan-v0.1` | active | D3 terrain field、D6 footprint 排除、LandUse/SurfacePrint 和 owner worldgen 执行。 |
| `City通用装饰阵列系统-v0.4` | active | 分层 Decoration content、placement、terrain outcome 与冻结执行。 |
| `City关键装饰锚点候选-v0.1` | active | required 单点 prefab 的完整 footprint、clearance 候选与相对坐标 patch。 |
| `RoadWeaver结构连接-v0.1` | active optional adapter | 结构入口注册和真实道路交接；缺 Mod 时 `auto` 跳过。 |
| `城市边界与城墙.md` | active | 统一说明 `v1_debug` 到 `v5` 的现行分支、默认值和执行边界。 |

## 维护规则

- 产品案只解释当前职责和取舍，字段真值回到 `20_contracts/`。
- 能力并入主线后继续更新现有案子，不新增“最终版”或并行版本说明。
- 不为已删除实现保留当前目录文档；需要追溯时使用 Git 历史。
- 未进入实现的方向不放入本目录，先在对话中完成方案冻结。
