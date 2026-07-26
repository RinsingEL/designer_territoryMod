# 首都 AI 候选选址 v0.1

## 问题

T2 既有路径把国度扩张核心同时写成 `CapitalCitySeed` 坐标，T4 Patch 规划又直接继承这座首都。这会让首都绕过 T3 领土形成后的候选点比较和连续承载面积校验，将“国度从哪里开始扩张”错当成“首都最终建在哪里”。

## 决策

- T2 只确定 `RealmSeed` 和无坐标的 `CapitalCityIntent`。
- T3 完成 owned territory 后，T4 为该国建立空的城市规划会话，会话首先等待首都选址。
- AI 必须使用 `realm_t4` Patch Explorer 浏览候选，再通过专用 `realm_t4_patch_planning_select_capital` 消费 `patchSelectionRef`。
- 首都选定前不能添加普通城市；通用 `add_city` 不接受 `role=capital`；同一会话只能有一座首都。
- finalize 必须校验恰好一座首都，且首都保留 Patch Explorer 选择追溯。
- D3 生成局部真实地貌后，新选首都必须显式审查。接受才能进入 D4；不接受则回到 T4 重新选址，不允许默认改成另一种城市原型继续施工。

## 兼容边界

- 历史 `capital_city_seeds.json` 中的坐标只作为旧国度核心来源，恢复时转成 `CapitalCityIntent`，不直接加入新 T4 会话。
- `realm_t4_build_registry` 保留给固定验收和旧调试链。它可在国度核心生成测试首都，但输出必须标记 `selectionMode=rule_fixture`，不得伪装成 AI 正式选址。
- D3 审查闸门先只强制用于 `source.siteSelectionMode=ai_candidate_selection` 的首都，不追溯破坏历史普通城市。

## 验收

1. T2 产物中不再出现最终首都坐标。
2. T4 create 后 `citySeeds=[]` 且首都状态为待选。
3. 首都容量不足、越界、重复选择或第二座首都都必须阻断。
4. 首都未选、缺少选择追溯或数量不是一座时不能 finalize。
5. D3 后未审查或审查要求重选时，所有 D4 入口都不能开始正式布局。

