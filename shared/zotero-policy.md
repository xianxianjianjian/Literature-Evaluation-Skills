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
- Zotero 写入必须验证真实返回结果，不得把请求已发送伪装成写入成功。

## Zotero 不可用时

Zotero 暂时失败不得阻塞已经完成的学术产出。待挂接文件可暂存于：

```text
work/<paper_id>/handoff/
```

当周 `workflow_manifest.yaml` 的 `pending_zotero_actions` 必须记录待执行动作、目标 parent、文件、期望附件名和失败原因。恢复后逐项验证并清除；禁止 silent failure。
