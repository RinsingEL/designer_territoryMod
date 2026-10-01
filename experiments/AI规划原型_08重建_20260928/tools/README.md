# 工具用途

日常编辑题目：
- build_t2_packet.py：将第二题源文件同步到独立资料目录。第一题直接读取源文件。

地图与结果导出：
- build_world_materials.py / build_native_climate.py：读取存档既有W数据，输出到data/第一题_国度设定。
- export_expansion_materials.py：读取已成功的T3产物，导出正式国界图及第二题资料；读取data/题目的编辑源文件，不再内嵌或重写题目要求；日常改稿无需运行。
- select_relocated_seed_proposals.py：复现避开初始大陆的离线起点建议；该建议现已完成实机提交，实际状态看result中的T3结果。

实机操作：
- run_relocated_expansion_trial.py：向运行中的游戏提交T1/T2/T3，会改变规划状态；本次已完成，无需为了整理或打包重跑。

历史实验脚本：select_realm_seed_proposals.py、run_seed_expansion_trial.py 对应迁址前方案，输出指向archive/旧结果，仅供追溯。

第二题背景更新：build_t2_context.py 提炼迁址后的奥伦设定、实际环境统计、03完整功能标签及05/06相关摘录。如改动素材可运行此脚本；会重写这些派生说明文件。export_expansion_materials.py 已在导出后调用它，避免旧版摘要覆盖新版背景。


停用的导出和打包脚本保存在 archive/停用导出工具/，仅作历史记录。

榆岑对照：先运行 build_yucen_trial.py 核对当前游戏存档并读取已有T3/W导出五图和领土数据，再运行 build_yucen_context.py 生成同题型背景。两者均不提交游戏规划或生成城市。

- `render_city_preview.py <答卷.json>`：离线读取城市坐标与领土数据，校验候选框归属并输出同名PNG；不连接游戏。第二题答卷须同时交付MD、JSON、PNG。

城市预览现使用 theoreticalScale + anchorBlock 格式，按代码默认规划半径和1.5倍保护范围计算；输出 validation.json 提示非国土粗格与保护重叠。旧 bounds/拟建成长边 格式为历史结果，不再作为新答卷输入。
