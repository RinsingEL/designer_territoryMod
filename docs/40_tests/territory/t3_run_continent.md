# T3 单大陆扩张入口验收

## 必验项

| 编号 | 项目 | 验收方式 | 通过标准 |
| --- | --- | --- | --- |
| T3-1 | 正常面积汇总 | 调用 `/t3_run_continent` 或单元测试响应构造 | 返回 `200`，包含 `continent_id / exported_count / claimed_total / wild_total / territories` |
| T3-2 | 零面积门禁 | 构造 `claimed_total + wild_total == 0` 的 T3 结果 | 返回 `409`，不得返回 `200` |
| T3-3 | 调试信息 | 检查零面积响应体 | 包含 `error`、`hint`、`exported_count` 和每个 territory 的 0 面积摘要 |
| T3-4 | C1 前置条件 | 调用 `/city_survival_c1_generate` 前检查 `/territory_status` | 只有目标国度 `total_area > 0` 时才继续城市生成 |

## 自动验证

在实现仓库运行：

```powershell
.\gradlew.bat test --tests "*Territory*"
.\gradlew.bat compileJava compileTestJava
```

## 手动回归

当前缺少有效 W3/W4 上下文、缺少 cluster map，或 territory `region_id` 与当前 W3 continent 不匹配时，调用 `/t3_run_continent` 应返回 `409`，并提示优先检查扫描缓存和大陆匹配关系。
