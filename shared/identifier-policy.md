# Identifier Policy

本协议冻结跨 Skill 使用的标识符命名空间。标识符一经用于持久化记录，不得改变含义或在另一类对象中复用。

| Namespace | Meaning | Example |
| --- | --- | --- |
| `EXT-xxx` | 外部依据 | `EXT-001` |
| `EX-xx` | Search 排除理由 | `EX-01` |
| `AUD-xxx` | 文献审计问题 | `AUD-001` |
| `CLM-xxx` | 核心 Claim | `CLM-001` |
| `TRI-xxx` | Translation Issue | `TRI-001` |
| `TERM-xxxx` | 专业术语 | `TERM-0001` |
| `TERMEV-xxxx` | 术语依据 | `TERMEV-0001` |
| `AN-xxx` | Result Analysis | `AN-001` |
| `SRC-Mn` | Main Article | `SRC-M1` |
| `SRC-Sn` | Supplement | `SRC-S1` |
| `Hn` | Hypothesis | `H1` |

序号在各自命名空间内递增；不得通过改变位数创建同义标识。

## 术语依据等级 TE1–TE7

`TE1` 表示最直接、最权威且与当前语境最匹配的中文术语依据；`TE7` 表示仅可作为弱线索、必须继续核验的依据。每条术语记录应保留 Evidence Level 和 `TERMEV-xxxx` 依据标识，不能让脚本或模型仅凭记忆自动决定最佳译名。

## 作者解释 Evidence Distance ED0–ED3

- `ED0`：解释几乎等同于直接观察或预先定义的分析输出。
- `ED1`：由直接数据支持，但包含一步有限解释。
- `ED2`：需要多步推断或依赖未直接测量的过程。
- `ED3`：高度推测、跨层级外推或需要重要外部假设。

Evidence Distance 描述解释距离，不等价于研究质量评分。

## paper_id

优先使用 DOI。标准化时：

1. 转为小写；
2. 移除 `https://doi.org/`、`http://doi.org/` 和 `doi:` 前缀；
3. 将文件系统不安全字符替换为连字符；
4. 保留足以回溯原 DOI 的可识别信息。

没有 DOI 时使用：

```text
FirstAuthor-Year-ShortTitle-hash
```

其中 `hash` 来自稳定的书目信息组合。不得把本地文件路径、Zotero 附件路径或临时下载名作为论文唯一身份。
