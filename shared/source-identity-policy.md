# Source Identity Policy

每篇进入正式流程的论文都必须进行身份与版本审计。至少记录：Title、Authors、Journal、DOI、Year、Online Date、Volume、Issue、Article number/pages、Publication Status、Version、Correction、Retraction、Expression of Concern 和 Supplement Status。

日期使用 ISO 8601；未知字段使用 `null`，不得猜测。

## 版本优先级

```text
Version of Record
>
Accepted Manuscript
>
Preprint
```

优先级用于选择默认分析版本，不代表低优先级版本没有研究价值。不同版本必须分别记录身份和来源，不得静默覆盖。发现 Correction、Retraction、Expression of Concern 或新增 Supplement 时，应保留原记录并通过工作流的 `needs_update` 与 `update_reason` 路由更新。

## Source Manifest

Main Article、每个 Supplement、Correction 和其他正式来源分别使用 `SRC-Mn`、`SRC-Sn` 或明确类型登记。清单应包含版本、获取时间、校验信息（如可得）、可用性和缺口。资料不可用时标记缺失或待核验，不得自行复原。
