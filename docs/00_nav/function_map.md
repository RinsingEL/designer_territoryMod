# Function Map

## 开发协作

- AI 协作开发规范：`./AI协作开发规范.md`
- 地貌驱动主线 Workflow：`./地貌驱动主线Workflow.md`
- AI 语义检索规则：`./AI语义检索规则.md`
- 实现仓库结构规范：`./实现仓库结构规范.md`
- 代码导览编写规范：`./代码导览编写规范.md`
- 从 0 到 1 设计开发流程：`./从0到1设计开发流程.md`
- Bug 修复流程：`./Bug修复流程.md`
- dev_docs 组织规则：`./dev_docs组织规则.md`
- Git 提交规则：`./Git提交规则.md`

## GIS 地貌基础设施

- 总入口：`../systems/gis/README.md`
- 方案：`../systems/gis/10_product/系统概述.md`
- v1 开发计划：`../systems/gis/10_product/开发计划.md`
- v1.1 开发计划：`../systems/gis/10_product/开发计划-v1.1-Step参数化最小闭环.md`
- Dregora 标准 W 粗扫驱动的 GIS 指标聚合计划：`../systems/realm_planning/10_product/开发计划-v1.3-Dregora标准W粗扫与GIS指标聚合.md`
- 高步长局部指标封装与地貌判定修正计划：`../systems/realm_planning/10_product/开发计划-v1.5-高步长局部指标封装与地貌判定修正.md`
- 多尺度 GIS 地貌特征栈与面域验收计划：`../systems/realm_planning/10_product/开发计划-v1.6-多尺度GIS地貌特征栈与面域验收.md`
- 半径刷新：`../systems/gis/10_product/功能设计/半径刷新与Atlas构建.md`
- 指标层：`../systems/gis/10_product/功能设计/GIS指标层.md`
- 地貌分类：`../systems/gis/10_product/功能设计/地貌分类与地貌区.md`
- 预览调试：`../systems/gis/10_product/功能设计/预览图与调试图.md`
- 数据契约：`../systems/gis/20_contracts/数据契约/`
- 配置表：`../systems/gis/20_contracts/配置表/`
- 代码导览：`../systems/gis/30_code_guide/代码导览.md`
- 刷新流程实现指南：`../systems/gis/30_code_guide/flows/半径刷新实现指南.md`
- GIS 主链 Review 清单：`../systems/gis/30_code_guide/review/GIS主链Review清单.md`
- GIS G1-G7 设计 Review 流程图：`../systems/gis/30_code_guide/diagrams/GIS_G1-G7设计Review流程图.md`
- GIS 刷新代码流程图：`../systems/gis/30_code_guide/diagrams/GIS刷新代码流程图.md`
- 测试与验收：`../systems/gis/40_tests/`

## 国度规划系统

- 总入口：`../systems/realm_planning/README.md`
- T 阶段国度与城市种子方案：`../systems/realm_planning/10_product/T阶段国度与城市种子方案.md`
- W / T 阶段主流程设计：`../systems/realm_planning/10_product/功能设计/W-T阶段主流程设计.md`
- v1.1 W 粗 Patch 与 T 阶段重建计划：`../systems/realm_planning/10_product/开发计划-v1.1-W粗Patch与T阶段重建.md`
- v1.2 W 粗扫 / T3 / T4 质量重构计划：`../systems/realm_planning/10_product/开发计划-v1.2-W粗扫T3T4质量重构.md`
- v1.3 Dregora 标准 W 粗扫与 GIS 指标聚合计划：`../systems/realm_planning/10_product/开发计划-v1.3-Dregora标准W粗扫与GIS指标聚合.md`
- v1.4 T3 行动力国度扩张模型计划：`../systems/realm_planning/10_product/开发计划-v1.4-T3行动力国度扩张模型.md`
- v1.5 高步长局部指标封装与地貌判定修正计划：`../systems/realm_planning/10_product/开发计划-v1.5-高步长局部指标封装与地貌判定修正.md`
- v1.6 多尺度 GIS 地貌特征栈与面域验收计划：`../systems/realm_planning/10_product/开发计划-v1.6-多尺度GIS地貌特征栈与面域验收.md`
- W / T 阶段数据契约：`../systems/realm_planning/20_contracts/数据契约/W-T阶段数据契约.md`
- W / T 阶段 MCP 接口契约：`../systems/realm_planning/20_contracts/接口契约/W-T阶段MCP接口.md`
- 代码导览：`../systems/realm_planning/30_code_guide/代码导览.md`
- W / T 主链实现指南：`../systems/realm_planning/30_code_guide/flows/W-T主链实现指南.md`
- 国度规划主链 Review 清单：`../systems/realm_planning/30_code_guide/review/国度规划主链Review清单.md`
- 国度规划 W / T 代码流程图：`../systems/realm_planning/30_code_guide/diagrams/国度规划W-T代码流程图.md`
- 测试入口：`../systems/realm_planning/40_tests/测试入口.md`
- 真实游玩验收计划：`../systems/realm_planning/40_tests/真实游玩验收计划.md`

## City 系统

- 总入口：`../systems/city/README.md`
- 案子状态索引：`../systems/city/10_product/案子/README.md`
- 固定模板唯一落地主线：`../systems/city/10_product/案子/City固定模板唯一落地主线-v0.1/README.md`；当前开发路径，破坏性删除 configured structure、StructureStart、Jigsaw、envelope profiling 和建筑 late materialize，City active 建筑只使用固定 NBT `StructureTemplate`。
- 当前主线案：`../systems/city/10_product/案子/D3-D6结构落地驱动城市重构-v0.1/README.md`
- D4 设计构图候选闭环：`../systems/city/10_product/案子/D4设计构图候选闭环-v0.1/README.md`
- D4 设计构图候选闭环 v0.2：`../systems/city/10_product/案子/D4设计构图候选闭环-v0.2/README.md`
- D4 阵列布局 Agent Loop v0.2 / v0.3：`../systems/city/10_product/案子/D4阵列布局AgentLoop-v0.2-v0.3/README.md`；v0.2 为当前显式 loop，v0.3 已接入 `composite_array` 嵌套阵列显式路径。
- D4 阵列候选选择闭环 v0.4：`../systems/city/10_product/案子/D4阵列候选选择闭环-v0.4/README.md`；已接入显式 `create -> query -> plan -> select -> finalize` 闭环。常规外扩仍需 focus / direction / target patch；仅 `newFunctionalArea=true` 先做全局 patch 搜索，再用 `selectedGlobalPatchRef` 生成候选，不切默认 workflow。
- D4 连续外扩候选 v0.5：`../systems/city/10_product/案子/D4连续外扩候选-v0.5/README.md`；当前开发路径。常规外扩以父结构 D2 bbox、方向和目标实体间距生成近中远连续候选，D3 patch 后置筛选 / 评分，可跨界；不再预选 target patch。
- City 通用装饰阵列系统 v0.3：`../systems/city/10_product/案子/City通用装饰阵列系统-v0.3/README.md`；当前装饰真值，在 v0.2 通用几何上增加内容姿态、全局连续地形 run、fill-only foundation、activation trace / preview 和显式 catalog 升级。
- City 关键装饰锚点候选 v0.1：`../systems/city/10_product/案子/City关键装饰锚点候选-v0.1/README.md`；当前开发案，让喷泉、雕像、水井等 required 单点 prefab 先由程序按完整 footprint、clearance 与硬障碍生成 1-8 个候选，再由 Agent 选择相对坐标 patch，禁止继续手算世界点。
- City 建筑驱动 LandUseAreaPlan v0.1：`../systems/city/10_product/案子/City建筑驱动LandUseAreaPlan-v0.1/README.md`；当前开发案，D6 locked footprint 后由 group / 单建筑生成 block 级用途区域和 SurfacePrintPlan，64 格内兼容区域自动相向扩张；intent v0.3 运行时传入 `uniform|contour_bands` 算法材料默认，刷地独立消费最终 mask，随后接稀疏 Decoration / execute_d5，RoadWeaver 后写覆盖，旧 chunk 不回填。
- City 建筑群生活感设计 v0.1：`../systems/city/10_product/案子/City建筑群生活感设计-v0.1/README.md`；当前设计案，使用现有 D4 / LandUse 表达功能结构，增加建筑朝向与生活装饰；首个切片为临河 / 海的农业、商业、行政综合城镇，道路另案。
- W 结果驱动大城镇功能区设计 v0.1：`../systems/city/10_product/案子/W结果驱动大城镇功能区设计-v0.1/README.md`；当前设计案，基于 sealed W 未生成候选定义农业、广场、行政、商业、居民和警卫区的建筑、装饰、阵列、设计顺序与修缮；农田使用不规则 LandUse 扩张和 `CONTOUR_BANDS` 等高线条带刷地，水槽由全局 FIELD / BANK / WATER mask 直接落地；同类兼容区域默认 64 格内相向扩张，城区按铺装面与真实道路联合网络验收。
- City 装饰填充层 Plan v0.1：`../systems/city/10_product/案子/City装饰填充层Plan-v0.1/README.md`；旧显式实现，七种业务 item 与提前展开刷入计划待 v0.2 破坏性替代，不自动兼容。
- 结构 Envelope 精修：`../systems/city/10_product/案子/结构Envelope精修-v0.1/README.md`
- 结构 Envelope 瘦身：`../systems/city/10_product/案子/结构Envelope瘦身-v0.1/README.md`；当前推进到 04 D4 阵列形态首切片，补 `compound_cluster` 参数化和 grid / courtyard / l_shape / u_shape / organic_compact 验收。
- 后续案：`../systems/city/10_product/案子/RoadWeaver结构连接-v0.1/README.md`
- 后续案：`../systems/city/10_product/案子/结构地形兼容适配-v0.1/README.md`
- 后续案：`../systems/city/10_product/案子/城市边界与城墙-v0.1/README.md`
- 后续案：`../systems/city/10_product/案子/城市边界与城墙-v0.2/README.md`
- 后续案：`../systems/city/10_product/案子/城市边界与城墙-v0.3/README.md`
- 后续案：`../systems/city/10_product/案子/城市边界与城墙-v5/README.md`
- 后续案：`../systems/city/10_product/案子/结构语义重标记-v0.1/README.md`
- 后续案：`../systems/city/10_product/案子/City结构风格化换皮-v0.1/README.md`
- 历史概述：`../systems/city/10_product/系统概述.md`
- 历史过程：`../systems/city/10_product/过程设计/C1-C4城市规划过程.md`
- 历史过程：`../systems/city/10_product/过程设计/C5-C8结构落地交接过程.md`
- 历史计划：`../systems/city/10_product/开发计划-v0.1-City城市构造最小闭环.md`
- 历史计划：`../systems/city/10_product/开发计划-v0.2-D7受控Jigsaw物化.md`
- 历史计划：`../systems/city/10_product/开发计划-v0.3-D7计划驱动Jigsaw拓展.md`
- 历史计划：`../systems/city/10_product/开发计划-v0.4-D7受控Jigsaw真实粘贴与验收.md`
- 历史计划：`../systems/city/10_product/开发计划-v0.5-D7Jigsaw落地拦截与规则增强.md`
- 历史案：`../systems/city/10_product/案子/D6结构池规划-v0.1/README.md`
- 历史案：`../systems/city/10_product/案子/D7条件包装结构生成-v0.1/README.md`
- 历史案：`../systems/city/10_product/案子/D7剩余结构起点候选-v0.1/README.md`
- 城市规划数据契约：`../systems/city/20_contracts/数据契约/城市规划数据契约.md`
- 结构落地交接契约：`../systems/city/20_contracts/数据契约/结构落地交接契约.md`
- City LandUse 数据契约：`../systems/city/20_contracts/数据契约/CityLandUseAreaPlan数据契约.md`
- City 调试 MCP 接口：`../systems/city/20_contracts/接口契约/City调试MCP接口.md`
- 代码导览：`../systems/city/30_code_guide/代码导览.md`
- 测试入口：`../systems/city/40_tests/测试入口.md`
- 影响面：`../systems/city/40_tests/影响面.md`
- D6-D7 临时真实结构测试配置：`../systems/city/40_tests/D6-D7临时真实结构测试配置.md`

## 待重建系统

旧城市、世界阶段文档已从当前真值目录清理。City 系统已重新建立文档入口，但当前仍处于方案与契约设计阶段，尚未在实现仓库建立新主链。其他未开发系统不进入当前核心系统入口，也不在实现仓库预建空 package。后续重建时，先读 `地貌驱动主线Workflow.md` 确认 W / T / C 主链职责；涉及国度、城市名册和城市生长种子时，进入国度规划系统入口；涉及城市局部规划、功能区、道路和结构落地交接时，进入 City 系统入口；随后按 `从0到1设计开发流程.md` 明确系统边界，并在 `systems/<系统>/10_product`、`systems/<系统>/20_contracts`、`systems/<系统>/30_code_guide`、`systems/<系统>/40_tests` 重新补入口。

## 开发工具

### 代码过程浏览可视工具

- 总入口：`../tools/code_process_viewer/README.md`
- 方案：`../tools/code_process_viewer/10_product/`
- 测试：`../tools/code_process_viewer/40_tests/`

## 辅助 Mod

### TerraSense

- 总入口：`../tools/TerraSense/README.md`
- 方案：`../tools/TerraSense/10_product/`
- 契约：`../tools/TerraSense/20_contracts/`
- 代码导览：`../tools/TerraSense/30_code_guide/代码导览.md`
- 测试：`../tools/TerraSense/40_tests/`

## 历史资料

- 历史归档目录：`../90_archive/`
