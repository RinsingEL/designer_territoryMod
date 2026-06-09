# Tools 文档入口

`docs/tools/` 维护为 Geomantia 开发、调试、扫描和资产策展服务的配套工具文档。工具不等同于运行时主系统，因此不放入 `docs/systems/`。

## 当前工具

| 工具 | 说明 |
| --- | --- |
| `code_process_viewer/` | 代码过程浏览与 Jigsaw 求解器回放工作台。 |
| `TerraSense/` | 结构扫描、结构策展、C3.5 catalog 生成和 runtime jigsaw 真值相关工具。 |

## 组织规则

工具内部仍按四层组织：

- `10_product/`：工具方案和功能设计。
- `20_contracts/`：工具协议、导出格式、输入输出契约。
- `30_code_guide/`：工具代码入口和实现仓库映射。
- `40_tests/`：测试入口、验收口径和影响面。

