# 附属区域预留 Java 接口 v1

需求依据：2026-09-22 用户确认主 mod 先暴露区域登记、规划避让、生成就绪接口，魔王内容由独立附属开发。玩家主动推进的剧情与战争不属于主 mod 的生成开放条件。

## 公共入口

包：`com.rinsing.geomantia.api.regions`；随 Geomantia JAR 提供，`RegionReservationApi.VERSION = 1`。附属编译依赖主 mod 的公开 API，不直接读取或改写内部规划文件。

| 入口 | 语义 |
| --- | --- |
| `RegionReservationEvent` | Forge 总线同步事件，W 已完成、首次 T1 尚未选取国度之前触发。通过 `context()` 读取地理事实，`reserve(ReservedRegion)` 登记区域。 |
| `RegionPlanningContext` | `runId`、`dimensionId`、`cellStepBlocks`、只读 W cell 列表。每格含 grid 坐标、实际 block 范围、大陆、地貌、高度、水体比例、`reserveAllowed`。 |
| `ReservedRegion(id, mask)` | ID 使用附属命名空间，如 `demon_army:capital`。mask 是一组不可变的 `RegionBounds`，其并集为预留范围。 |
| `RegionBounds(minX, minZ, maxX, maxZ)` | 含边界的 block 矩形，允许负坐标；不依赖 W 的格网步长。须包含建筑、道路、景观和附属自身需要的安全保护范围。 |
| `RegionReservationApi.regions(server, runId)` | 查询该存档规划 run 中冻结的预留列表。 |
| `isReserved(server, runId, dimensionId, bounds)` | 检查矩形是否与该维度的任一预留相交。 |
| `isGenerationReady(server, runId, regionId)` | 查询生成方案就绪状态。 |
| `markGenerationReady(server, runId, regionId)` | 附属持久化并激活自己的生成方案后调用；幂等、单向，并立即使服务端开放缓存失效。 |

事件及所有 server API 必须在服务端主线程调用。登记窗口在事件返回时关闭，不能保存 event 后延迟补登记。一个监听器失败或登记冲突会中止本次 T1，不发布半份预留结果。不同附属没有静默抢占或覆盖优先级，冲突须调整选址。

## 最小接入例子

```java
@Mod.EventBusSubscriber(modid = "demon_army", bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class DemonRegions {
    @SubscribeEvent
    public static void reserve(RegionReservationEvent event) {
        var context = event.context();
        // 仅演示公共类型；正式附属按城堡尺寸选择足够大的连续 mask。
        var cell = context.cells().stream()
                .filter(c -> c.reserveAllowed() && c.waterFraction() < 0.5)
                .findFirst().orElseThrow();
        event.reserve(new ReservedRegion("demon_army:capital", List.of(cell.bounds())));
        // 附属保存 context.runId()，供后续生成方案准备与就绪上报使用。
    }
}

// 事件已结束、附属自己的生成方案已经持久化并激活后，在服务端线程调用：
RegionReservationApi.markGenerationReady(server, runId, "demon_army:capital");
```

附属继续使用自己的模型、动画、实体、技能、战役状态及保存格式。没有新增 HTTP/MCP 管理接口，也不需要主 mod 依赖附属类。

## 规划与持久化

1. W 完整扫描原始地理，不扣除魔王领地，也不因附属登记加载地形。
2. 首次 T1 收集登记，验证覆盖范围、初始探索区及缓冲、附属之间的冲突。正式服务端入口另外检查已加载和磁盘区块；已生成或状态不明的范围拒绝登记，不覆盖旧地形。
3. 登记成功后冻结 mask。T1 候选与 T2 校验、Patch Explorer、T3 两种扩张模型使用同一份排除结果。W 粗格只要与预留相交，就整格排除；T3 可分配面积的分母也相应减小。
4. 正式 T4 检查城市完整保护矩形，并在 finalize 合并名册时复核；失败不消费选择凭证。兼容 fixture 与名册同步入口也不能越过预留。
5. 城际路由将 mask 作为障碍，继续使用既有全路幅和最终施工 footprint 检查；城内建筑与道路仍受城市设计/保护边界约束。
6. mask 文件为当前存档 `realm_debug/<runId>/addon_region_reservations.json`；就绪状态单独保存为 `addon_region_generation_ready.json`，不会让既有 Patch 选择凭证仅因就绪变化而过期。

规划身份绑定 surveyId、维度、种子、格网、范围和 configHash 等稳定 W 事实，排除导出时间和缓存命中统计。不同 W 内容不能在同一 run 下静默复用旧 mask。重新启动或继续同一 run 时恢复已登记内容，不再次触发登记事件。

已有 T1 的旧 run 按空预留兼容，不向已规划区域补插领地。需要新区域的附属应从新的规划 run 开始；旧城与既有区块不会被迁移、清理或重新生成。冻结后没有删除、改边界或从 ready 回退的公共 API，击败 Boss 也不释放规划预留。

## 生成开放与游戏进度

延续现有完整地理区域开放规则：mask 触及的大陆/海域必须等待该附属的生成方案就绪。先等 T3 完成分配，才能判断该大陆是否包含普通国度；附属提前就绪不能提前开放尚未分配的大陆。与普通国度处在同一大陆时，还要等待该大陆原有城市和名册条件。独立的附属大陆不需要虚构普通国度或城市来获得开放资格。

地图揭示、移动/传送和区块调度使用同一结果，既有视距/生成依赖缓冲继续生效。该能力遵循 `planning_area_access` 的总开关及托管维度设置。

`generationReady` 表示附属的结构/地表生成准备已完成，不等于建筑已经全部落地，也不等于玩家击败 Boss。主 mod 信任附属的上报；附属应在真正完成准备后上报。默认地形、植被和其他第三方模组的世界生成不会被这份规划预留一概取消；需要改变它们的附属须使用自己的生成能力。

## 验证入口

- `RegionReservationStoreTest`：冻结、冲突原子性、负坐标、存档隔离、就绪幂等、稳定 W 身份和损坏数据。
- `RealmPlanningServiceTest`：登记只执行一次、T2 拒绝预留格、两种 T3 模型避让。
- `RealmT4PatchPlanningServiceTest`：中心点合法但完整保护圈越界时拒绝，且不消费凭证。
- `PlanningAreaAccessPolicyTest`：未就绪锁定对应大陆、不影响其他大陆，独立附属大陆开放与缓存变更。
- `geomantia_regions` GameTest：公开 API 查询、维度隔离、就绪上报与实际 FULL 区块重新调度。
