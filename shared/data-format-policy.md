# Data Format Policy

所有持久化结构化数据遵守以下约定：

- 文本编码：UTF-8；
- 日期和时间：ISO 8601；
- 布尔值：`true` / `false`；
- 缺失值：结构化 YAML/JSON 使用 `null`，CSV 使用空字段；
- 每个可演进的结构化文件包含 `schema_version`，或由其固定 Schema 文档明确版本；
- 字段名、枚举值和标识符大小写稳定，不使用本地化同义值。

## YAML 子集

Phase 1 的 Python 工具仅依赖标准库。机器维护的 `.yaml` 文件采用 JSON-compatible YAML 1.2 子集：UTF-8 JSON 对象写入 `.yaml` 文件。这样保留 YAML 业务格式和可读性，同时避免未声明的第三方解析依赖。

工具不得用字符串替换方式修改结构化文件；必须解析、验证后原子写回。未知字段应在合理情况下保留，格式错误必须显式报错。

## CSV

CSV 使用 UTF-8、首行固定 Header 和 RFC 4180 兼容引用规则。脚本写入前验证 Header，避免列错位。DOI 比较时使用标准化值，但保留原始 DOI 字段以便显示。

## JSONL

JSONL 每行一个完整 JSON object，不允许跨行对象。空的 `terminology_evidence.jsonl` 是合法初始状态；后续每条记录必须包含其 Schema 版本和稳定 Evidence ID。
