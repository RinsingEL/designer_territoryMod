# City AI 材质与方块检索数据契约

需求入口：[City AI 材质选择与景观参数](../../10_product/案子/具体流程的案子/00_跨阶段主线/CityAI材质选择与景观参数-v0.1/README.md)。

## 蓝图材质

`cityBlueprint.surfaceMaterials` 为可选字段。省略时使用施工默认材料；外观不改变道路路由或台面范围。新蓝图的规范化输出使用分组材质，旧的平铺 slot 输入仍可读取。它与提交层的建筑选材 `materialSelections` 是不同能力。

```json
{
  "surfaceMaterials": {
    "defaults": {
      "groundAndRoad": {"preset": "stone"},
      "terrace": {"preset": "timber_stone", "materials": {"wallColumn": "minecraft:birch_log"}},
      "bridge": {"preset": "timber"}
    },
    "groups": {"administration": {"terrace": {"materials": {"wallCap": "minecraft:stone_bricks"}}}},
    "roads": {"CITY_BRIDGE": {"bridge": {"preset": "stone"}}},
    "landscapes": {"north_fields": {"cropBlockId": "minecraft:carrots"}}
  }
}
```

- `defaults`：本城市默认覆盖。
- `groups`：以现有 groupId 为键的局部覆盖。已有建设面按最近的保留建筑 footprint 归属取材；距离相同时按 groupId 稳定决胜，不因此新增占地或改变功能区几何。
- `roads`：以实际道路类型为键；同部位的道路类型覆盖优先于功能区覆盖，再继承城市默认。可用类型见 `designGuide.surfaceMaterials.roadKinds`。
- `landscapes`：以本蓝图 landscapeId 为键的景观实例覆盖，不继承城市道路用材。

外观组定义与完整预设集中于 `src/main/resources/geomantia/city_surface_appearances.json`，由同一个目录驱动解析器和 Agent guide：

| 组 | 部位 | 预设 |
| --- | --- | --- |
| groundAndRoad | ground、roadSurface、roadStair、roadCurb、roadBase、accessSurface、accessStair | stone、sandstone |
| terrace | retainingWall、wallColumn、wallCap、wallBand、deck、fill、pier、railing、lowWall、hedge | stone、timber_stone、sandstone |
| bridge | bridgeSurface、bridgeRail、bridgeBeam、bridgePost、bridgePier | timber、stone、sandstone |

每组只接受 `preset` 和可选 `materials`。先展开预设，再覆盖本组 materials；未选择的部位沿用原继承规则。道路作用域接受 groundAndRoad 的道路部位和 bridge，不接受 terrace。新输入不需要重复填整组所有部位。预设名称、越组字段、几何参数和重复 slot 均严格校验；同一 slot 不得同时用旧平铺和新分组形式指定。景观字段保持原结构。

规范化蓝图按组保存展开后的 materials；施工冻结字段保存具体 slot 到方块的映射，因此预设数据以后变化也不会改写已冻结选材。工作流局部修订指定新 preset 时替换这一整组，避免旧组的材料覆盖导致换预设无效；只给 materials 则按字段合并。桥梁部位可使用 CITY_BRIDGE 的覆盖作为普通道路跨水转换后的桥梁默认，显式原道路类型覆盖仍优先。


景观候选字段为 `surfaceBlockId`、`cropBlockId`、`channelBankBlockId`、`channelWaterBlockId`、`channelBankOverlayBlockId`、`boundaryBlockId`；每种景观只开放其现有启用配方中非空的部位，见 `landscapeSupportedSlotsAndDefaults`。不能通过选材新增作物层、树木生成器、布局或改变数量。

所有值只接受已注册的 `namespace:block`，不接受方块状态。当前道路截面要求半砖，道路台阶和路缘要求楼梯方块；灌溉仍只接受现有水方块。已知不支持的多格植物、方块实体等会说明原因。基础类型检查通过不代表任意 Mod 方块都已实机验证。

## 按需检索与预览

通过现有 `city_submit_d4_blueprint` 工具独立提交，保留 runId/citySeedId/contextId：

```json
{"blockMaterials":{"slot":"roadSurface","query":"stone slab","page":0}}
```

省略 query 或留空时，仅返回当前部位默认候选。关键词检索当前注册表中的标识、显示名、已有标签；每页最多 12 项，返回 `hasMore` 和存在后续页时的 `nextPage`。显示名取当前运行环境语言。结果包含方块 id、显示名、Mod 命名空间、基础适用检查、已知拒绝原因及同名配套候选；同名不宣称作者已确认配套。

景观查询同时填写 `landscapeProfileRef`，并验证 slot 在该配方开放范围内。

```json
{"blockMaterials":{"slot":"roadSurface","previewBlockId":"minecraft:stone_brick_slab"}}
```

按需返回当前客户端资源包的 128×128 材质样片，经 `imageEvidence` 传给模型。这是粒子纹理样片，不是完整三维方块外观；独立服务端无客户端纹理、资源不可用或超时时返回 `previewUnavailable`，不生成假图。常规搜索不附图片。

查询不修改草稿、不入编译队列、不扣提交格式重试次数。查询失败仍返回可纠正的字段/原因。

## 默认候选配置

内置数据为 `geomantia/city_material_candidates.json`，可用游戏配置目录下的 `geomantia/city_material_candidates.json` 按部位覆盖，未提供的部位继承内置候选，升级时新增部位不会被旧配置整表遮蔽。格式为 `{部位: [方块id...]}`；每个部位对模型最多显示 4 个默认项，其余方块仍可按需搜索。无需对整个整合包手工分类。

## 冻结与执行

蓝图保留选材，SurfacePrintPlan 的可选 `materialField` 冻结本城覆盖与保留建筑/道路的归属几何，并参与计划哈希。道路选材写入冻结 feature cells；景观覆盖进入实例 surfaceSettings 与打印配方。材料变化不修改道路位置、高程、朝向或景观生长参数。

ChunkFragment 携带该字段；实际执行用它选择铺面、道路底座、台地底板、填充、支柱、挡土墙、栏杆/矮墙/绿篱与接入台阶。朝向、连接状态与地形检查继续由现有放置器负责。旧打印计划没有该字段时仍按原材料执行。

## 落地失败反馈

材料预检或写入失败时，执行结果和 owner failure 的可选 `materialFailure` 提供 `sourceId`、`placementPhase`、`blockId`、`x/y/z`、`reason`。原 reasonCode 与回滚逻辑保留；批量连接收尾等无法归因到单块的失败不虚构具体方块。

## 立面与桥梁施工

新生成的台面外露侧面按墙面、立柱、压顶、腰线分类；柱距使用跨区块稳定的世界坐标节奏，转角优先立柱，低墙仅收边，高墙增加横带。同高相邻台面不因 owner 不同产生内墙。全部立面操作保留在原有台面边界列，不自动扩出步道或码头。

道路在规划水域采样中连续跨水时转换为桥面与桥栏，冻结整个水段及邻接桥头的同一高程；仍受地形采样精度限制。桥梁形成有厚度的桥面与侧梁，桥栏立柱与桥墩使用同一选点；桥墩只在选中的边缘列向下延伸，最多检查 64 格并在现有实体处停止。桥面半砖按 DOUBLE 放置以对齐道路和上方立柱，桥下保留通水空间，不能调用普通台面填土把河封实。道路接入口不给桥栏封口，自动台面扶手和非道路台面楼梯均避让桥面。

本次不做已落地存档热更新。模拟写入与离线规划验证不等同于游戏内观感验收；尚未实现石拱曲线、额外拓宽栈道、灯饰及藤蔓自动布置。
