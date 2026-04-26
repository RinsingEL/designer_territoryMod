# C1 城市边界生成重构方案

## 定位

本方案单独处理城市最初边界生成问题。

当前 `C1 / createCity` 在城市创建时直接扩张出 `claimedChunks`，后续 `C2` 只是把这个结果画出来。因此，城市外轮廓过于方正、核心/主城/过渡区比例异常、外层被挤压等问题，根因应优先在 C1 边界生成阶段解决。

本方案不讨论具体建筑落地、不讨论 C8/Jigsaw 结构拼接，也不要求马上接入图像模型。它的目标是先把“城市允许范围”和“层级热力”从旧的 4 方向 chunk 泛洪扩张中解耦出来。

## 当前问题

### 1. 边界过于方正

当前实现使用 chunk 级 4 方向邻接扩张：

```text
north / south / east / west
```

这会天然产生强烈的直角折线与网格膨胀痕迹。即使地形代价有水体惩罚，边界仍会更像算法占格，而不是顺应海岸、坡地、山脊和开阔平地的城市轮廓。

### 2. C1 过早决定了最终轮廓

`claimedChunks` 一旦生成，后续 C2/C3/C5/C6 都在它的基础上继续处理。若 C1 轮廓已经不自然，后续阶段只能补救，无法从根上恢复城市构图。

### 3. 层级分配像排序切片

当前 layer 分配是按扩张成本排序后按权重切分。这个方法可以保证数量占比，但不保证空间关系自然：

- core 可能变成狭长条
- urban 可能像通道
- buffer / transition 可能被挤成边角
- 层级不一定形成包裹、半包裹或沿地形展开关系

### 4. 后续 AI 草图被错误边界限制

如果 C3 AI 总体设计草图只能在旧 C1 方正边界内作图，图像模型的构图能力会被上游边界限制。因此 C1 应先提供更自然的候选城市边界。

## 重构目标

C1 的新目标不是直接产出最终建筑布局，而是产出一个可被后续阶段消费的“城市设计画布”：

- 自然城市外轮廓
- 可建范围
- 禁建/保留边界
- 核心、主城、过渡的软层级热力
- 非监督自动审查结果
- fallback 候选

C1 输出应服务于 C2/C3，而不是替 C3/C8 做完城市设计。

## 新职责边界

### C1 负责

- 根据中心点、目标规模、地形、水体、坡度和国境生成城市候选边界
- 输出软边界和 chunk snap 结果
- 输出层级热力，而不是硬切碎片
- 做自动校验、自动重试和 fallback
- 为 C2/C3 提供城市允许范围与设计画布

### C1 不负责

- 不生成具体建筑槽位
- 不决定具体道路网细节
- 不生成 C8 节点链
- 不直接选择 Minecraft 结构模板
- 不把 layer 分配当作最终功能分区

### C2 负责

- 基于 C1 画布生成网格地形底图与可视化输入
- 展示 C1 边界、软层级和地形关系

### C3 负责

- 在 C1 画布和 C2 地形底图基础上生成 AI 总体设计草图
- 把边界内部的宏观构图交给 AI 草图表达

## 推荐生成策略

### 总体流程

```text
输入 CityConfig / world settings
-> 读取地形、水体、坡度、国境、已有城市
-> 生成候选边界热力场
-> 提取软边界
-> snap 到 chunk / block 网格
-> 生成 core / urban / transition 热力层
-> 自动校验
-> pass 则固化为 C1 boundary plan
-> retry / auto_fix / fallback 处理失败情况
```

### 候选边界不再从 4 方向泛洪直接产生

建议改成两层：

1. 连续空间热力场
2. 离散网格 snap

先在 block 或高分辨率栅格上生成连续边界倾向，再转换成 chunk 级 `claimedChunks` 或更细的 `allowed_polygon`。这样可以减少强烈 chunk 方格感。

### 热力场输入

热力场可以只使用少量稳定因子：

- 距离城市中心
- 距离水体/海岸
- 坡度/roughness
- 是否在国境内
- 是否与已有城市重叠或过近
- 是否符合开局配置中的 density / coastal preference

不建议引入大量风格参数。城市设计风格应主要留给 C3 AI 草图和 C7 导演意图。

### 边界形状原则

边界应：

- 顺应海岸、河流、山脚和开阔平地
- 允许凹凸、留白和不完整外缘
- 避免长直角矩形边
- 避免包进大片水域或陡坡
- 避免为了达到 chunk 数量强行填满狭窄地

### 层级从硬分片改成软热力

C1 不应直接把 chunk 切成死板的 `CORE / URBAN / BUFFER` 最终分区。

建议输出：

- `core_heat`
- `urban_heat`
- `transition_heat`
- `preserve_heat`

后续 C3/C5 可以根据这些 heat map 生成更自然的区域。若仍需兼容旧逻辑，可从 heat map 派生 `LayerAssignment`，但应标记为兼容字段。

## 非监督审查

因为本项目目标是游戏开始配置一次、后续完全自动生成，所以 C1 审查不能依赖人工确认。

同时，StructureBinder 是通用国度生成器，不应默认把水体、陡坡、密林、悬崖、地下、浮空等地形条件当作全局硬拒绝。是否允许水城、山城、沼泽城、港口城、地下城或特殊生态城市，应由国度设定、城市类型与世界配置决定。

因此，C1 审查分为两层：

- 硬合法性：只检查跨国度、城市重叠、数据不可解析、生成无法继续等绝对问题。
- 软适配性：水体、坡度、roughness、海岸、森林等只影响风险、偏好、buffer/transition 语义和后续地形适配策略。

### 状态枚举

```text
pass
retry
auto_fix
fallback
fail_safe
```

### 硬合法性检查

硬合法性只覆盖“无论什么国度设定都不能接受”的问题。

| 检查项 | 失败处理 |
| --- | --- |
| 城市边界越出所属国度/允许主权范围 | auto_fix 裁剪，严重则 retry / fallback |
| 与已有城市硬重叠 | retry 或调整边界；无法解决则 fallback |
| 与同批次新城市硬重叠 | 批量重排或 fallback |
| 中心点不在所属国度内 | retry 或重新选址 |
| 边界为空、不可解析或碎成无法连通的孤岛 | retry / fallback |
| 连续失败后无 fallback | fail_safe |

### 软适配性检查

软适配性不直接拒绝城市，只给后续阶段提供风险与语义提示。

| 检查项 | 默认处理 |
| --- | --- |
| 水体占比高 | 标记为 `water_city_candidate`、`waterfront_heavy` 或 `requires_foundation` |
| 陡坡/roughness 高 | 标记为 `terraced_city_candidate`、`requires_terrain_adaptation` |
| 海岸线复杂 | 倾向生成港口、滨水 preserve、buffer 或 waterfront transition |
| 森林/生态敏感 | 倾向生成 preserve / buffer，不直接拒绝 |
| transition 面积偏低 | 记录 warning，并优先让 buffer 语义吸收风险 |
| 外轮廓过方 | 记录 shape warning，可重试优化，但不作为通用硬失败 |
| 与其他城市距离过近但未重叠 | 记录 spacing warning，由国度密度设定决定是否重试 |

### 方正度检查

方正度只应是默认 organic 城市的质量提示，不是所有国度的硬规则。

例如：

- 规则化帝国、棋盘城、防御城、机械文明、地下设施，可以允许较方正边界。
- 自然村镇、海岸城、山城、森林城，应更倾向有机边界。

因此，方正度检查默认输出 warning / retry suggestion，只有当世界配置明确要求 organic 且连续生成结果极端方正时，才触发 retry。

可检查：

- 外边界直角数量是否过高
- 长直水平/垂直边占比是否过高
- 边界 bbox 填充率是否接近矩形
- 边界凹凸变化是否过低

该检查只用于发现明显方块城市，不作为精确美学评估。

### 层级比例检查

层级比例也不应是严格美学评分。`buffer / transition` 的重点是承载风险、过渡和低干预语义，不要求所有城市都有同样面积比例。

建议只检查明显异常：

- core 不存在或过大
- urban 可用面积不足
- transition / preserve 被挤压到接近 0，且该国度/城市类型没有声明允许极高密度或硬边界城市
- core、urban、transition 互相完全割裂

不要引入大量精确百分比参数。默认阈值应隐藏在内部策略中。

## 自动重试策略

每座城市最多进行少量重试，避免世界生成卡死。

```text
attempt 1: 正常边界生成
attempt 2: 降低方正度、增加边界平滑和地形吸附
attempt 3: 降低目标规模、放宽局部留白
fallback: 使用安全边界模板
fail_safe: 小型保守城市画布
```

重试只调整内部策略，不暴露大量玩家参数。

## fallback 策略

### fallback_boundary

用于 AI/热力边界失败时的保守方案。fallback 也必须尊重国度设定，而不是默认陆地保守城：

- 以中心点附近所属国度范围内的可解析区域为核心
- 使用椭圆、软多边形或设定允许的规则形状
- 不跨国度、不重叠已有城市
- 水体/坡地只根据城市设定决定是否避让
- 生成较小但可继续 C2/C3/C8 的 `allowed_polygon`
- buffer / transition 可由风险区域自然承担，不强制固定比例

### fail_safe_city_canvas

极端情况下生成最小安全城市画布：

- 小型 core
- 一圈 urban
- 外缘 transition / preserve
- 明确禁止进入复杂 C3/C6 路线
- 后续 C8 只生成少量结构节点

fail_safe 的目标不是好看，而是保证世界生成不中断。

## 建议产物

### C1_BoundaryPlan.json

```json
{
  "step": "C1_BOUNDARY_PLAN",
  "city_id": "city_3120_-3200",
  "status": "pass",
  "attempt": 1,
  "boundary_source": "terrain_heatmap",
  "center": { "x": 3120, "z": -3200 },
  "target_chunk_count": 120,
  "allowed_polygon": [],
  "claimed_chunks_compat": [],
  "heat_layers": {
    "core_heat": "C1_core_heat.png",
    "urban_heat": "C1_urban_heat.png",
    "transition_heat": "C1_transition_heat.png",
    "preserve_heat": "C1_preserve_heat.png"
  },
  "validation": {
    "status": "pass",
    "actions": [],
    "blocking_errors": [],
    "auto_fixes": [],
    "fallback_used": false
  }
}
```

### C1_boundary_preview.png

必须可视化：

- 原始地形底图
- 城市中心
- allowed polygon
- chunk snap 后的兼容 claimed chunks
- core / urban / transition 热力等高线
- rejected / preserved 区域

## 与 C3 AI 草图的关系

C1 输出“画布”，C3 输出“构图”。

```text
C1: 这座城市大致允许在哪里长，哪里安全，哪里应保留
C2: 把画布和地形画清楚
C3: AI 在画布里做总体城市设计草图
```

C3 不应再被旧 chunk 方框锁死，但也不能完全无边界自由发挥。C1 的新边界是 C3 的安全舞台。

## 与旧 claimedChunks 的兼容

迁移期可以继续生成 `claimedChunks`：

- 作为 C2 绘图兼容
- 作为旧 C3/C5/C6 fallback 输入
- 作为国境和城市占用登记

但正式语义应逐步转向：

- `allowed_polygon`
- `boundary_mask`
- `heat_layers`
- `claimed_chunks_compat`

`claimedChunks` 不再作为唯一城市边界真值。

## 开局配置建议

玩家/世界配置只暴露少量高层选项：

```json
{
  "city_boundary": {
    "style": "organic",
    "density": "medium",
    "waterfront_preference": "allow",
    "fallback_policy": "safe"
  }
}
```

不暴露：

- polygon 数量
- 方正度阈值
- 每层百分比
- 边界平滑半径
- 碎片合并面积
- 具体 heat map 权重

这些应作为内部策略，避免项目再次陷入参数过多。

## 迁移步骤

### 第一阶段：只新增产物

- 保留当前 `expandCity`
- 新增 C1 边界计划文档与样例 JSON
- 允许保存 `C1_BoundaryPlan.json` 和 `C1_boundary_preview.png`
- 旧 `claimedChunks` 不变

### 第二阶段：双轨生成

- 运行旧 `expandCity`
- 同时运行新 C1 boundary planner
- 在 C2 预览图中同时显示旧 claimed chunks 与新 allowed polygon
- 比较方正度、可建面积、层级比例和水体冲突

### 第三阶段：C2/C3 切换到新画布

- C2 以新 boundary plan 作为主要画布
- C3 AI 草图以新 allowed polygon 和 heat layers 为输入
- 旧 claimed chunks 只作兼容和 fallback

### 第四阶段：旧扩张降级

- `expandCity` 从主真值降为 fallback
- C1 boundary planner 成为默认边界生成方式
- 文档和测试入口同步更新

## 验收标准

- 新边界预览明显减少 chunk 方格扩张感
- 边界能根据国度设定选择顺应、利用或避让水体、海岸、坡地和开阔平地
- core / urban / transition 不再出现明显竖条化或外层消失
- validator 能自动发现跨国度、城市重叠、边界不可解析等硬问题，并把水体、坡地、过方、transition 偏低等作为设定敏感的软提示
- 失败时能自动 retry / auto_fix / fallback，不需要人工确认
- 后续 C3 AI 草图能在更自然的 C1 画布内工作

## 当前建议结论

应先重构 C1 边界，再推进 C3 AI 草图。

如果 C1 仍输出方正 chunk 框，C3 再聪明也只能在错误画布里设计；如果 C1 输出自然、安全、可校验的城市画布，C3 才能真正发挥图像模型的构图能力。


