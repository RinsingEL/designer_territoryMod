# City 城际道路

2026-09-20：按用户确认，先连接同国城市。城际路网由程序负责，AI 不直接调用 RoadWeaver，也不提交逐段道路参数。

## 连接与派生出口

同一 run 的 `city_seed_registry.json` 按 realmId 分组，以城市位置构造确定性的最小生成树。首次 D5 编译保存 `inter_city_roads/network.json`（schema `realm_intercity_network`），之后沿用冻结的连接关系，不随状态轮询增删道路。只有一个城市的国度没有城际边；不生成跨国连接。

每座城市的 `steps/d5/inter_city_exit_plan.json`（schema `city_intercity_exit_plan`）记录：

- `streetBands`：从内部街道到城外端点的派生道路。
- `portals`：linkId、otherCityId、城外 point、墙线上 gate。
- `unresolvedLinks`：没有安全出口的连接及原因 `NO_SAFE_CITY_EXIT`。

出口按邻城方向选择墙段，避开墙角、建筑包络及其他墙带，连接现有内部街道。道路连同路缘检查净空；相同端点可以共用城门。D5 据真实穿墙道路重新计算 gateSlots，城区轮廓保持不变。D6 的 sourceStructureAnchorMap 带上派生道路交给室外编译，原始 D4 文件及其验收 hash 不变；续跑比较时识别并剥离派生部分。

没有可用出口只留下连接诊断。城墙仍按自身预留与地形规则施工，执行报告以 `exitRoadStatus=NO_PLANNED_EXIT` 说明无门洞；不再用 `WALL_EXIT_ROAD_REQUIRED` 拒绝整圈墙。

## 城外寻路与水体

只有两端 D5 出口和激活证据齐全，才编译该边的城外路线。未齐全记录 `WAITING_FOR_ENDPOINTS`，不阻塞城市 D7。

复用经适配的 RoadWeaver A*：四邻接、整条道路净宽检查、精确端点、固定搜索域、预算和中断检查。先找避海陆路，失败后允许计算跨水参考路线，再截取两端城市各自通向岸边的部分。中间岛屿不铺路，不把海运或渡口宣称为已建成。

当前内部限制：路面宽 5 格，寻路连路缘检查半径 3 格；栅格步长 16；端点包围盒向外扩 512 格；避海尝试最多 3,000 节点，为允许跨水参考线的后备搜索保留采样容量，后备搜索最多 30,000 节点；单边长度上限 32,768 格；连续水带超过 64 格按岸边终止。地形按 4 格缓存，单边最多 100,000 个采样、30 秒采样预算。预算耗尽保留诊断，不退化为穿障直线。地形使用 RTF 只读预览，其他生成器使用不生成区块的 base-height/biome 查询。

`LAND_CONNECTED` 表示完整陆路方案，窄水体交给现有桥面编译；`SHORE_TERMINATED` 表示两岸陆路方案，明确不是陆路贯通。无路线、端点被占、搜索/采样预算耗尽、距离超限分别记录原因。失败路线以端点签名去重，不在每次城市状态轮询中反复消耗寻路预算。

## 施工与持久化

`inter_city_roads/<linkId>/compiled_road.json` 原子保存 report、独立 LandUseAreaPlan 和 SurfacePrintPlan；`status.json` 保存最近一次工作流观察到的规划/施工状态。规划成功不等于所有区块已施工，实际完成以 LandUse owner 账本为准。

城际计划使用独立 owner（包含连接与 run 身份），空铺地区域、只含道路 feature。复用现有道路分级、桥面和材质执行；材质取稳定排序的 A 端城市道路配置。最终 footprint 再校验一次建筑/墙带冲突。激活后计划不可被不同 hash 覆盖；相同计划重复激活不会重置施工队列。

施工使用 Geomantia 原有 D7 队列，全局每 tick 至多推进一个 owner 动作。加载前检查 owner 及采样邻域的地理开放资格，未开放为 `waiting_for_region`，每 100 tick 复查，不强制解锁。重启仅恢复已激活的城际计划，owner 账本防止重复铺设，不进行结构发现或扩大连接图。

单边规划失败、等待对端、等待地理开放，不令城市主流程失败。现有已落地城市不会自动补出口或重编 D5；功能主要用于后续新设计城市。冻结路网后新增城市与已激活道路重规划尚无专用入口。

## 复用边界与验证

源代码来自本地 RoadWeaver `b48bfab` 的 BasicAStarPathfinder，MIT 版权与许可证、上游 NOTICE 和修改说明随 JAR 保存在 `META-INF/licenses/roadweaver/`。不引入完整 RoadWeaver Mod、自动找村庄、玩家周边扩路、独立施工线程或世界生成 Hook。

自动化覆盖路网确定性/同国边界、全宽绕障与端点、预算失败、海岸/河流、D5 城门和原始设计不变、独立道路 owner 的持久化与重复执行。长距离地形观感、真实城门高程衔接与运行时区块调度仍须游戏实测。
