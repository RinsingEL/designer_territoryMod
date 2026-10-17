# 可组合 NPC 外观素材库 · RFH1 首批方案

2026-10-16 · **资产与接口草案；未接入游戏**。需求入口为用户本轮“多风格文明居民随机生成”原话。本轮先完成共同规范与学院完整组合，再制作蒸汽朋克、精灵风格的少量对照样板。普通居民由程序组合，AI 提供文明/城市偏好及少量关键人物覆盖。

| 交付 | 入口 |
| --- | --- |
| 身体、素材分类、首批数量和制作顺序 | [01 素材规划](01_素材规划.md) |
| 骨架、尺寸、UV、挂点、服装适配 | [02 制作规范](02_制作规范.md) |
| 稳定 ID、池配置、保存同步与渲染接口 | [03 配置与程序接入](03_配置与程序接入.md) |
| 已做检查、未通过的门槛、批量制作任务包 | [04 验证与任务包](04_验证与任务包.md) |
| 可编辑源、PNG、Blockbench 工程、拟议导出与预览 | [实现仓素材包](E:/Mod_Dev/StructureBinder/asset_catalogs/realmfolk_appearance/v1/README.md) |

## 当前实现核对

| 入口 | 代码事实 | 与本方案的差距 |
| --- | --- | --- |
| `ClientViews.CitizenRenderer` | `MobRenderer<CitizenEntity,VillagerModel<…>>`；烘焙 `ModelLayers.VILLAGER`；固定 `minecraft:textures/entity/villager/villager.png`；原版头部、职业、交叉手臂持物图层 | 没有自定义身体、素材目录、分层肤色/眼睛/衣服、独立双手或挂点配饰加载器。新增 PNG/JSON 不会自动替换模型。 |
| `LivingCitizenModel.setupAnim` | 延用村民动画；乘坐时弯腿且 `jacket.yScale=.6`；工作摇交叉手臂，使用物品时抬手与低头 | 现有生活动作能触发姿态，但新骨架的肘、膝、袍片、束发和左右手动画均未接入。不能把旧模型动作成功当作新素材通过。 |
| `CitizenEntity` | 同步 `ROLE/ACTIVITY/APPEARANCE/SLEEP_DIRECTION`；`APPEARANCE` 是 resident/smith 等简短字符串，映射村民职业；实体 NBT 保存 CitizenId、Role、睡眠朝向 | 没有 resolved appearance 资产 ID、颜色、体型、内容版本或完整外观同步。仅有一个 appearance 字符串不等于素材库支持。 |
| `Society.Citizen` / `Design.Profession` / `DesignCodec` | 人物保存职业快照、关系、设施与装备等；职业 `appearance` 仍限制旧七种村民样式 | 需另加外观快照及配置校验，不能把新字段塞入当前 appearance 期待生效。 |
| `Realmfolk.CITIZEN` | `.sized(.6f,1.95f)`；没有按视觉体型驱动的尺寸策略 | 碰撞、眼高、乘坐偏移、床对齐、门与导航适配必须单独做。 |
| `可配置生活行为.md` | 已有 face/hold_item/sit/sleep_bed/sleep_surface/work、临时装备恢复与设施朝向 | 复用行为状态和设施坐标；本轮不改生活动作、库存、设施认领或现有试玩存档。 |
| `asset_catalogs/original_civilizations/文明命名.md` | 当前 AA=魔法学院，SR=蒸汽朋克，FS=精灵风格；前缀与旧目录稳定，风格不是种族证明 | 外观 style 使用 academy/steam/elven 的技术标签，记录 AA/SR/FS 映射。只覆盖首批对照，不替代既有全部风格清单，也不恢复已撤回的虚构文明名。 |

代码核对基于 `E:\Mod_Dev\StructureBinder\addons\realmfolk\src\main\java\com\rinsing\realmfolk\`，不是对未实现能力的推测。现有生活与人口契约继续有效；本目录没有宣布正式契约升级，也没有改变 design.json v2。

## 本轮资产边界

交付 25 个资产 ID、9 个完整组合（3 风格×3 体型）、灰度贴图/配色掩码/面部眼睛层、9 个嵌入贴图的 `.bbmodel` 工程、拟议 `.rfmodel.json` 及离线预览。学院标准体型是先行完整基准，其余八套验证共用规则是否能扩展。不是 25 个成品居民，也不是 25 种全部独立轮廓。

静态PNG与GIF读取作者源中的几何、骨架、UV、颜色快照与动作帧，具备可复现的离线证据。日常构建已与初始化分离；改角点/贴图像素后保留作者源、导出与预览同步变化的检查通过。GIF仅walk/eat/work持续变化，其他姿态保持，动作边界直接切换。

Blockbench官方网页编辑器已打开，模型文件导入因浏览器扩展权限失败，电脑控制工具随后无法确认浏览器URL而终止本轮UI。**模型实开、保存、重新打开仍未通过**；Minecraft加载与实际家具/物品也未验证。按用户最新要求暂停扩大精制数量，编辑器门槛补齐后再正式移交程序接入。

本轮不修改 Java 或正式配置，不构建新 JAR，不进入既有游戏世界。通过离线规范检查后，可安排有限的修整与接口工作；**游戏门槛通过前不开展全池批量精制**。

## 来源与许可

样板是本轮原创方块几何与像素绘制，无第三方皮肤/模型输入，沿用 Realmfolk 的 GPL-3.0-or-later。详见[来源清单](E:/Mod_Dev/StructureBinder/asset_catalogs/realmfolk_appearance/v1/PROVENANCE.md)。工程格式参考 [Blockbench 官方说明](https://www.blockbench.net/wiki/docs/bbmodel/)，资源命名参考 [Forge 1.20.1 资源文档](https://docs.minecraftforge.net/en/1.20.1/concepts/resources/)；自定义 RFH1 模型与池不是 Forge 标准接口。
