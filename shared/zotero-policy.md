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
- Zotero 写入必须验证真实返回结果；请求已发送、HTTP 2xx、Connector/Local API 在线都不等于归档成功。
- 同名附件不得静默覆盖。完全相同的 title + filename + MD5 可幂等复用；断点留下的空 attachment child 可继续上传；同名但不同文件必须停为冲突。

## V1 写入能力边界

### Zotero 10+ Local API

Zotero 10+ 的 Local API v3 支持本地写入与完整文件上传。V1 的 durable existing-parent attachment 路径使用该能力，而不是依赖短生命周期 Connector session。

写入安全合同：

1. 先从 Local API discovery 响应取得 `Zotero-Server-ID`；
2. 写入通过 `/api/local/authorize` 请求 Zotero Desktop 本机授权；
3. Local API key 只保存在当前进程内，不打印、不写入 Git、manifest、日志或配置文件；
4. 临时授权 key 按单次写入处理；用户在 Zotero 中选择长期允许时，进程内可复用对应授权；
5. 写入和写后验证绑定同一 `Zotero-Server-ID`，数据库身份变化必须停止而不是继续写；
6. attachment 只有在 parent、filename 与 MD5 均回查一致后才可记为已验证。

`scripts/zotero_bridge.py attach` 的默认行为是预览；只有显式 `--yes` 才会请求本机授权并执行写入。

### Bibliographic parent create

Phase 7 已验证的 parent-create 路径继续保留：`scripts/zotero_bridge.py create` 使用官方 Connector `/connector/saveItems`，执行前查重并解析保存目标，执行后通过 Local API 按 DOI/标题回查。只有唯一匹配时才记录 `CREATED_AND_VERIFIED` 和 parent item key。

### Durable local-file attach

Phase 8 为 Zotero 10+ 实现 existing-parent attachment：

```text
existing parent
→ create/reuse attachment child
→ request full-upload authorization
→ upload file bytes
→ register uploadKey
→ server-bound read-after-write verification
→ ATTACHED_AND_VERIFIED
```

支持 Main/SI/A/B 后续独立挂接，因此不要求 parent 与附件处于同一 Connector session。

默认 library prefix 是 `users/0`。只有明确知道目标 group library 且拥有相应编辑/文件权限时，才使用 `groups/<numeric-group-id>`。

当前 helper 自设单文件 256 MiB 安全上限；这是项目侧限制，不应表述为 Zotero 的官方最大文件大小。

## 完成语义

不得折叠以下层级：

```text
Local API/Connector reachable
≠ write authorization granted
≠ item/attachment child created
≠ file bytes registered
≠ attachment identity verified
≠ full Zotero archive COMPLETE
```

`ATTACHED_AND_VERIFIED` 或 `ALREADY_ATTACHED_AND_VERIFIED` 才能提供可用于 manifest/source record 的已验证 attachment key。

如果写入过程中 child 已创建但文件上传未完成，返回 `ATTACHMENT_FILE_UPLOAD_INCOMPLETE` 并保留 child key 作为恢复线索；不得标记 COMPLETE。

## Zotero 不可用或当前运行时不满足写入条件时

待挂接文件可暂存于：

```text
work/<paper_id>/handoff/
```

当周 `workflow_manifest.yaml.pending_zotero_actions` 必须记录待执行动作、目标 parent、文件、期望附件名和失败原因。恢复后逐项验证并清除，禁止 silent failure。

如果运行的是不具备 Zotero 10+ Local API 写能力的环境，或用户拒绝本机授权，attachments 保持 pending/PROVISIONAL；不得自动退回到未验证的写接口。

父条目创建成功不等于论文档案完整：Main/SI/A/B 的 attachment key 仍需分别验证。