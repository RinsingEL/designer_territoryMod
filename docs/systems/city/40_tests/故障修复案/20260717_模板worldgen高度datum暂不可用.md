# 模板 worldgen 高度 datum 暂不可用

## 状态

- 状态：代码已修复，自动测试通过，待新区域实机复验。
- 系统：City 固定 NBT 模板 worldgen 落地。
- 现场：`落地测试`，run `city_stubbs_farm_playtest_20260717_01`，city `city_stubbs_farm_test_01`。
- 边界：本记录不修改现行模板落地契约，也不授权 `debugLateMaterialize` 作为正式补偿路径。

## 现象

Stubbs 农庄实测中，风车和肉铺完成 D7 template ledger，谷仓 `barn_windmill_01` 一直为 `WAITING_FOR_TEMPLATE_MATERIALIZATION`。谷仓 D6 locked footprint 为 `660169,659500..660199,659524`，跨 9 个 owner chunk。

## 排查与证据

1. 日志确认谷仓的 9 个 owner chunk 都命中 City worldgen registry，不是 D5 未激活、LandUse、植被 mask、RoadWeaver 或模板检索阻止。
2. 多个 owner 回调记录 `TEMPLATE_DATUM_SURFACE_UNAVAILABLE`；执行层在高度图 datum 小于等于 `minBuildHeight` 时记录失败并跳过 `template.placeInWorld(...)`。
3. 已加载后的游戏内高度图将锚点定位到 `660169.5, 106, 659500.5`；手动 `/place template geomantia:city/stubbs/agriculture/barn_windmill_01 660169 107 659500 counterclockwise_90` 成功。
4. 同一农田投影区实际高度为 `106..120`，存在陡坡但不是虚空或基岩坑。手动成功说明 NBT、资源定位和该锚点地形均可落地。

## 根因确认

根因不是“谷仓不能放在该处”，而是旧执行层把模板级 datum 错当成 owner 回调级临时值：每个 owner 都在自己的 `FEATURES` 回调中重新读取 `MOTION_BLOCKING_NO_LEAVES(anchor)`。

Forge 1.20.1 / Minecraft 1.20.1 源码确认：`FEATURES` center 在调用 `applyBiomeDecoration(...)` 前只 prime 当前 center 的 post-features heightmap；距离 1 依赖 chunk 至少到 `CARVERS`，距离 2 只要求 `BIOMES`。因此三乘三 owner 模板的远端回调可以在 anchor chunk 尚无 `MOTION_BLOCKING_NO_LEAVES` 时执行。此时 `WorldGenRegion#getHeight(anchor)` 读取未 prime 的 anchor heightmap，会得到无效最低高度。

另一个独立但同源的问题是：某个 owner 成功写入模板 fragment 后，模板方块可能抬高 anchor heightmap；后续 owner 再查同一 anchor 时会读到修改后的值。现场普通风车的 9 个 fragment 因此出现 `109` 与 `110` 两种 datum。旧 completed ledger 取最后一次回调的值，不能证明整栋模板使用同一高度。

## 已实施修复

1. 每个 owner 在首次 `FEATURES` 写任何方块前，先原子持久化 `templatePendingFragments[]`；该记录是后续受控重试的必要证明，落盘失败时禁止继续写 fragment。
2. 只有 anchor owner 能在自己的 `FEATURES` 回调中读取已 prime 的真实 `MOTION_BLOCKING_NO_LEAVES(anchor)`，并把唯一 `templateDatumY` 冻结到 `templateDatums[]`。不使用 `ChunkGenerator#getBaseHeight`，因为该接口只保证基础 terrain column，不能等同 surface / carver 后的当前契约。
3. 非 anchor owner 不再查询 anchor heightmap；datum 尚未冻结时保留 durable waiting，冻结后只复用该值。fragment ledger 和最终 completed ledger 都强制与 frozen datum 一致，第二个不同值以 `TEMPLATE_DATUM_CONFLICT` 拒绝。
4. owner 已越过 `FEATURES` 时，只允许 Forge `ChunkEvent.Load` 登记、server tick 确认 FULL 后处理此前存在 pending proof 的 owner。重启后可恢复同一 pending 事务；没有 pending proof 的既有旧 chunk 不会进入该路径。
5. worldgen ledger 改用同目录唯一临时文件和原子替换；pending、datum、fragment / completed 的内存状态在落盘失败时回滚。最终 ledger 仍只在全部 owner fragment 成功且 datum 一致后生成一次。

本修复没有修改 rotation / mirror / pivot，也没有改变 `templateDatumPolicy=worldgen_surface_motion_blocking_no_leaves` 的真值口径。

## 修复验收

- 自动测试已覆盖：8 个非 anchor owner 先进入等待、anchor owner 后冻结 `105`，九个 fragment 全部复用 `105`，最后一个 owner 才生成唯一 completed ledger。
- 自动测试已覆盖：首个 fragment 冻结 `109` 后，第二个 owner 尝试用 `110` 会得到 `TEMPLATE_DATUM_CONFLICT`，不增加 fragment、不提前 completed。
- 自动测试已覆盖：pending / datum / fragment 重载后保持幂等；ledger 落盘失败不留下内存 datum / pending，也不授权世界写入。
- `./gradlew.bat test --tests "com.rinsing.geomantia.systems.city.*" --tests "com.rinsing.geomantia.platform.http.CityPlanningEndpointHandlerTest"`：325 项通过，0 failure / 0 error。
- 在新的未生成坡地测试区复测谷仓；手动 `/place template` 只能作为定位证据，不能替代 City worldgen 正式验收。
