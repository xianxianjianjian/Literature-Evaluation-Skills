# Data Format Policy

所有持久化结构化数据遵守以下约定：

- 文本编码：UTF-8；
- 日期和时间：ISO 8601；
- 布尔值：`true` / `false`；
- 缺失值：结构化 YAML/JSON 使用 `null`，CSV 使用空字段；
- 每个可演进的结构化文件包含 `schema_version`，或由其固定 Schema 文档明确版本；
- 字段名、枚举值和标识符大小写稳定，不使用本地化同义值。

## YAML 子集

V1 的 Python helper 默认仅依赖标准库。机器维护的 `.yaml` 文件采用 JSON-compatible YAML 1.2 子集：UTF-8 JSON 对象写入 `.yaml` 文件。这样保留 YAML 业务格式和可读性，同时避免未声明的第三方解析依赖。

工具不得用字符串替换方式修改结构化文件；必须解析、验证后原子写回。未知字段应在合理情况下保留，格式错误必须显式报错。

## CSV

CSV 使用 UTF-8、首行固定 Header 和 RFC 4180 兼容引用规则。脚本写入前验证 Header，避免列错位。DOI 比较时使用标准化值，但保留原始 DOI 字段以便显示。

## JSONL

JSONL 每行一个完整 JSON object，不允许跨行对象。空的 `terminology_evidence.jsonl` 是合法初始状态；后续每条记录必须包含其 Schema 版本和稳定 Evidence ID。

## Source-text reproduction and public Git

结构化字段要求保留“原文 Abstract”或其他原文片段时，必须同时遵守来源权限边界：

- 用户直接提供/上传的原文、Zotero 中用户已拥有的附件、或明确允许相应再利用的开放/授权来源，可以作为精确原文字段的来源；
- 仅从网页搜索结果、出版社预览页或其他受复制限制的网页获得的文本，不得为了填满 Git 字段而自动大段复制；
- 当目标 Git 仓库是公开仓库时，尤其不能把“可以在线阅读”自动等同于“可以公开再发布全文或摘要”；
- 若 C 要求精确 Original Abstract，但当前只有不适合再发布的网页来源，则保持该字段待补/明确标注来源缺口，并将相关交付状态保持 `PROVISIONAL`，直到获得可合法用于该字段的源文本；
- “Original Abstract”字段不得用模型改写文本冒充原文。可另行生成摘要，但必须与原文栏位区分。

以上规则不改变 C 的字段要求，只规定原文字段的可接受来源与公开归档边界。
