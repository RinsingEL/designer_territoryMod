# T3 单大陆扩张入口契约

## 接口

- 路径：`POST /t3_run_continent`
- 请求体：

```json
{
  "continent_id": 1
}
```

## 成功响应

当 T3 为目标大陆导出至少一个有效主权 chunk 时返回 `200`。

```json
{
  "continent_id": 1,
  "exported_count": 2,
  "claimed_total": 128,
  "wild_total": 24,
  "territories": [
    {
      "territory_id": "han",
      "territory_instance_id": "han@c1",
      "continent_id": 1,
      "claimed_chunks": 80,
      "wild_chunks": 12
    }
  ]
}
```

## 零面积失败响应

当 T3 导出了 territory 结果，但 `claimed_total + wild_total == 0` 时，入口必须返回 `409`，不得返回假成功。

```json
{
  "continent_id": 1,
  "exported_count": 2,
  "claimed_total": 0,
  "wild_total": 0,
  "territories": [
    {
      "territory_id": "han",
      "territory_instance_id": "han@c1",
      "continent_id": 1,
      "claimed_chunks": 0,
      "wild_chunks": 0
    }
  ],
  "error": "T3 produced zero claimed chunks for continent 1",
  "hint": "Likely causes: missing/invalid W3-W4 scan cache, missing cluster map, or territory region_id does not match current W3 continent ids."
}
```

如果目标实例此前已经存在非零 canonical T3 产物，则新的零面积结果不得覆盖旧产物；实现会把本次零面积结果写到 `territory/<territory_instance_id>/T3_failed/<timestamp>/` 诊断目录，并可在失败响应里附带 `preserved_existing_t3` 提示。

## 历史 T3 导入入口

- 路径：`POST /territory/t3_import`
- 用途：把旧基础 id 的非零 T3 结果显式导入到当前实例 id，例如 `r15_test_01 -> r15_test_01@c15`

请求体：

```json
{
  "source_territory_id": "r15_test_01",
  "target_territory_id": "r15_test_01@c15",
  "dry_run": false
}
```

成功响应核心字段：

```json
{
  "step": "T3_IMPORT",
  "ok": true,
  "dry_run": false,
  "message": "imported",
  "source_territory_id": "r15_test_01",
  "target_territory_id": "r15_test_01@c15",
  "claimed_chunks": 2342,
  "wild_chunks": 4,
  "canonical_written": true,
  "runtime_restored": true
}
```

约束：

- `source_territory_id` 必须存在且非零。
- `target_territory_id` 必须能在当前运行态解析到 territory config。
- `dry_run=true` 只做校验与摘要回传，不改磁盘、不改内存。

## 下游约束

- `wild_total` 计入有效国度面积，因为运行时主权判定接受 claimed 与 wild chunks。
- `/territory_status` 启动后会尝试把当前实例 id 的 T3 结果从磁盘恢复到内存；如果此前已经通过 `/territory/t3_import` 写入 canonical T3，重启后应可直接恢复。
- 调用 `/city_survival_c1_generate` 前，应先确认 `/territory_status` 中目标国度 `total_area > 0`，避免使用空主权结果继续生成城市。
