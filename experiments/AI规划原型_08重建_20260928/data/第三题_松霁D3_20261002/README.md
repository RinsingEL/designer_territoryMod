# 第三题：第二题松霁原选址 D3

采用第二题_榆岑城市设计_20260929_223645.json 中的 yucen_songji（松霁），坐标 **X=-7744，Z=9664**、village、地方聚落职能原样保留。用途为西北木作修补与旅居交流。此包是第三题当前局部地形输入，替代此前另选城址的样例。

## 正式 D3 运行结果

- 独立实验 run：experiment_q2_songji_20261002；citySeedId：yucen_songji。
- 规划半径 256 方块；范围 X [-8000,-7488]、Z [9408,9920]，边界闭区间口径；网格 32×32，16 方块步长。
- ok=true；1024 地形格、72 Patch；RTF generator_native fastPath，277.041709ms。
- territoryCheckResult=inside；siteReviewStatus=not_required 是现有接口对该输入的返回，不代表新增的人工作业验收。
- 地形来源是生成器先验 estimated_coarse_heightmap，不是已生成世界逐块测量。

## 文件

- [地貌图](city_test_run/steps/d3/landform_review_map.png)
- [群系图](city_test_run/steps/d3/biome_overview.png)
- [地貌审查数据](city_test_run/steps/d3/city_landform_review_package.json)
- [地形数值](city_test_run/steps/land_use/land_use_terrain_field.json)
- experiment_input_provenance.json：第二题原城市输入、答卷校验值和 W/T 来源。
- city_seed_registry.json：显式实验输入。
- D3工具返回.txt：实际调用返回。

## 接入方式与边界

实现仓 tools/city_experiments/prepare_second_question_d3.py 将已有答卷和尺度粗检结果适配为独立 D3 输入；原 W/T 世界身份和领土文件保持原内容复制，源 run 不变，不生成 Patch 选择凭证或审查通过记录。随后调用现有 city_plan_d3；实际扫描、范围验证、地形分类与绘图均由原实现完成。

这只是按用户确认坐标进行的 D3 实验，不是正式 T4 选址验收或城市施工授权。没有运行 D4、生成建筑或改变第二题布局。原始产物中的引用仍相对运行存档 realm_debug，后续离线使用应正规适配，不伪造哈希。建筑内容包与第三题编译循环仍需独立接通。
