# Zotero Policy

一个正式书目 parent item 等于一篇论文的长期研究档案中心。普通 Search 候选不应全部塞入 Zotero；只有用户最终确认精读的论文才正式入库。

## 推荐附件名称

```text
[ORIGINAL] Main Article
[SUPPLEMENT] <descriptive name>
[A] 中文全文翻译镜像版
[B] 文献研究笔记·完整精读版
```

Main、SI、A 和 B 由 Zotero 长期管理。Git 保存 Skills、knowledge、Search 历史、C 和工作流状态，不长期重复保存 A/B。

## Parent 与附件规则

- 先通过 DOI 等正式身份字段匹配 parent，防止明显重复。
- 不同版本不得静默覆盖；版本关系写入 source manifest。
- 每个附件记录其 parent item key、attachment key、来源类型与校验状态。
- Zotero 写入必须验证真实返回结果，不得把请求已发送、HTTP 2xx 或 Connector 在线伪装成归档成功。

## V1 写入能力边界

Zotero Desktop Local API `/api/` 只读。V1 可使用 Zotero Connector server 执行经过明确验证的写接口，但必须逐操作声明能力：

- **bibliographic parent create**：`scripts/zotero_bridge.py create` 使用官方 `/connector/saveItems` 路由；执行前检查重复，执行后必须通过 Local API DOI/标题身份回查。只有唯一匹配成功时才可记录 `CREATED_AND_VERIFIED` 和 parent item key；
- **local-file attach**：当前仍为 `LOCAL_FILE_ATTACH_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED`。不得猜测未验证的 Connector/plugin 参数，不得把 Main/SI/A/B 标记为已挂接。

`create` 是显式写操作。普通 Paper Gate 已授权当周所选论文的正常入库时，可以执行；独立调用时必须有等价的明确写入授权。脚本本身还要求 `--yes`，没有该参数时只输出预览，不写 Zotero。

父条目创建成功不等于论文档案完整：Main/SI/A/B 的 attachment key 仍需分别验证。

## Zotero 不可用或附件写入尚不可用时

Zotero 暂时失败不得阻塞已经可以安全完成的学术工作。待挂接文件可暂存于：

```text
work/<paper_id>/handoff/
```

当周 `workflow_manifest.yaml` 的 `pending_zotero_actions` 必须记录待执行动作、目标 parent、文件、期望附件名和失败原因。恢复后逐项验证并清除；禁止 silent failure。

如果 parent 已成功创建但 attachment route 仍不可用，应保留真实 parent key，同时只把未完成的附件动作留在 `pending_zotero_actions`。相关归档阶段保持 `PROVISIONAL`，直到要求的附件可观察并验证。
