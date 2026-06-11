# C阶段 AI 总规链路契约草案

## 状态

本文件是 C 阶段 AI-first 总规路线的目标契约草案，尚未表示实现仓代码已经完成。实现时应优先保证旧 C1-C9 入口继续可用，并把本契约作为新入口和新产物的对齐依据。

## 核心产物

| 产物 | 阶段 | 作用 |
| --- | --- | --- |
| `C1_design_base.png` | C1 | AI 设计底图，包含地形、网格、主权、已有城市和图例 |
| `C1_design_base.legend.json` | C1 | 底图坐标、颜色、比例尺与约束说明 |
| `C2_ai_masterplan_preview.png` | C2 | AI 总规预览，给人审阅 |
| `C2_boundary_mask.png` | C2 | 城市边界 mask |
| `C2_district_mask.png` | C2 | 功能区 mask |
| `C2_road_mask.png` | C2 | 道路骨架 mask |
| `CityDesignPlan.json` | C3/C4 | 解析、校验、修复后的城市总规真值 |
| `group/<groupId>/group_intent.json` | C5-C7 | C8 可消费的 group 意图和约束 |

## CityDesignPlan.json

```json
{
  "step": "C_STAGE_AI_MASTERPLAN",
  "city_id": "city_3120_-3200",
  "territory_id": "r15_test_01@c15",
  "coordinate_space": {
    "type": "world_block",
    "origin_x": 3008,
    "origin_z": -3360,
    "width_blocks": 256,
    "height_blocks": 192,
    "preview_size": 512
  },
  "source": {
    "base_map": "C1_design_base.png",
    "base_legend": "C1_design_base.legend.json",
    "masterplan_preview": "C2_ai_masterplan_preview.png",
    "boundary_mask": "C2_boundary_mask.png",
    "district_mask": "C2_district_mask.png",
    "road_mask": "C2_road_mask.png"
  },
  "boundary_polygon": [],
  "districts": [],
  "roads": [],
  "preserve_areas": [],
  "entry_bands": [],
  "fallback_sources": [],
  "validation": {
    "status": "pass",
    "blocking_errors": [],
    "warnings": [],
    "auto_fixes": []
  }
}
```

## District

```json
{
  "district_id": "district_core_01",
  "semantic_type": "core",
  "polygon": [],
  "source_mask_color": "#E53935",
  "confidence": 0.86,
  "area_blocks": 4200,
  "entry_band_ids": ["entry_main_north"],
  "validation": {
    "inside_boundary": true,
    "water_overlap_ratio": 0.0,
    "roughness_risk": "low",
    "too_small": false,
    "too_thin": false
  }
}
```

`semantic_type` 第一批固定为：

- `core`
- `urban`
- `transition`
- `preserve`
- `waterfront`
- `industrial`
- `market`
- `defense`
- `civic`

实现可以先支持子集，但不得把未知颜色静默当作可建区。

## Road

```json
{
  "road_id": "road_spine_01",
  "road_type": "primary",
  "polyline": [],
  "width_hint_blocks": 7,
  "connects": ["entry_main_north", "district_core_01"],
  "validation": {
    "connected": true,
    "inside_boundary_ratio": 0.97,
    "blocked_segments": []
  }
}
```

`road_type` 第一批固定为：

- `primary`
- `secondary`
- `service`
- `bridge`
- `stair`
- `waterfront_path`

## group_intent.json

```json
{
  "group_id": "g_market_01",
  "source_district_ids": ["district_market_01"],
  "allowed_polygon": [],
  "avoid_polygons": [],
  "road_interfaces": [],
  "intent": {
    "theme": "市场",
    "density": "medium",
    "growth_mode": "jigsaw_growth",
    "style_tags": ["organic", "waterfront"],
    "max_nodes": 8,
    "branch_budget": 2
  },
  "validation": {
    "status": "pass",
    "warnings": []
  }
}
```

## 新入口建议

第一批 MCP / HTTP 入口建议：

| 入口 | 职责 |
| --- | --- |
| `city_ai_design_base_generate` | 生成 C1 设计底图包 |
| `city_ai_masterplan_import` | 导入 AI 总规图与 mask |
| `city_ai_masterplan_parse` | 解析 mask 为 CityDesignPlan |
| `city_ai_masterplan_validate` | 校验并自动修复 CityDesignPlan |
| `city_group_intent_generate` | 从 CityDesignPlan 生成 group intent |

这些入口命名是草案。实现前可按现有 `CityController` 风格调整，但必须保留“生成底图、导入图像、解析、校验、生成 group intent”五段能力。

## 兼容规则

- 旧 C1/C3/C6/C7 产物在迁移期继续可读。
- 当 `CityDesignPlan.json` 缺失或失败时，允许回退旧选簇/扩张路线。
- 当 AI mask 可读但局部缺失时，程序可用旧选簇补齐 group，不得直接扩大到国境外。
- C8/C9 只消费已校验的 group intent、placement node 和执行队列，不直接消费未经解析的 AI 图片。
