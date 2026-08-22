# Zotero Policy

Zotero 是本项目**首选的长期研究档案中心**，但不是 V1 学术工作流能够运行和完成的前置依赖。普通 Search 候选不应全部塞入 Zotero；只有用户最终确认精读的论文才进入正式归档流程。

## 推荐附件名称

```text
[ORIGINAL] Main Article
[SUPPLEMENT] <descriptive name>
[A] 中文全文翻译镜像版
[B] 文献研究笔记·完整精读版
```

长期目标仍是由 Zotero 管理 Main、SI、A 和 B；Git 保存 Skills、knowledge、Search 历史、C 和工作流状态，不长期重复保存 A/B。

## V1 核心原则：归档不能卡死学术工作

只要 Main/SI 等源证据本身已经可用，Zotero 不可访问、自动写入失败、Local API 尚未完成本机验证或用户选择手动挂接，都**不得单独阻止**：

- Search 学术阶段完成；
- Translation/A 完成；
- Deep Reading/B/C 完成；
- completed reading 写入 `<data-root>/knowledge/reading_history.csv`。

这些情况必须改为单独记录归档待办：

```text
pending_zotero_actions
```

并在可用的本地运行时暂存到：

```text
<data-root>/work/<paper_id>/handoff/
```

阶段 `PROVISIONAL/BLOCKED` 应由真正影响学术完整性的来源、SI、版本、证据或产物问题触发，而不是仅因为 Zotero 自动化不可用。

## Academic completion 与 Archive completion

### Academic completion

A/B/C 本身及其 QC、证据链、来源身份和必需知识记录通过即可形成学术完成状态。A/B 的 `zotero_attachment_key` 可以暂时为 `null`，但必须有真实文件/工作产物和明确的 pending archive record。

### Archive completion

若用户要求“完整 Zotero 归档”，则额外要求：

- 所需 parent 可观察且身份匹配；
- Main/SI/A/B 中适用的 attachment 实际存在；
- attachment key 已验证；
- 版本关系没有静默混淆；
- 相应 `pending_zotero_actions` 已清除。

不得因为学术工作已经完成就声称 Zotero 归档完成。

## Parent 与附件规则

- 先通过 DOI 等正式身份字段匹配 parent，防止明显重复。
- 不同版本不得静默覆盖；版本关系写入 source manifest。
- 每个已验证附件记录 parent item key、attachment key、来源类型与校验状态。
- Zotero 写入必须验证真实返回结果；请求已发送、HTTP 2xx、Connector/Local API 在线都不等于归档成功。
- 同名附件不得静默覆盖。完全相同的 title + filename + MD5 可幂等复用；同名但不同文件必须停为冲突。
- 手动在 Zotero 中完成 parent/attachment 并随后验证，也属于 V1 可接受的操作路径；V1 不强制所有归档动作必须自动化。

## 当前自动化能力：可选增强，不是 release blocker

仓库保留 Zotero 自动化 helper 作为可选集成和后续优化基础。

### Parent create

现有 `<plugin-root>/scripts/zotero_bridge.py create` 使用 Zotero Connector `/connector/saveItems`，执行前查重，写后要求身份回查。该路径可继续使用，但其 group-library/selected-target 统一问题属于后续优化，不阻止 V1 核心 Skill 发布。

### Zotero 10+ Local API attachment

`<plugin-root>/scripts/zotero_bridge.py attach` 和 Local API helper 已实现 Zotero 10+ existing-parent durable attachment 的协议/mock/CI 版本，包括本机授权、Server-ID、full upload、MD5/parent/filename 回查、幂等与冲突保护。

但真实用户桌面端 live validation 仍属于后续集成验收。V1 运行时可以：

1. 自动写入并验证（环境支持时）；
2. 自动写入失败后转 pending；
3. 由用户/操作方手动挂接后再验证；
4. 暂时保留 handoff 文件，不影响学术流程完成。

## 完成语义

不得折叠以下层级：

```text
academic artifact COMPLETE
≠ Zotero reachable
≠ write authorization granted
≠ item/attachment created
≠ attachment identity verified
≠ full Zotero archive COMPLETE
```

`ATTACHED_AND_VERIFIED` 或 `ALREADY_ATTACHED_AND_VERIFIED` 才能提供可用于 archive-complete 判定的已验证 attachment key。

如果写入过程中 child 已创建但文件上传未完成，应保留恢复线索并继续作为 pending archive action；不得假装归档成功，但也不得因此抹掉已经通过 QC 的 A/B 学术完成状态。

## 恢复与后续优化

恢复会话时优先处理真正影响学术证据链的 blocker。Zotero pending actions 可以在学术工作完成后单独批量清理。

以下属于后续可优化项而不是 V1 release blocker：

- parent create 全面迁移到 Local API；
- user/group library 统一路由；
- 真实 Zotero Desktop live write acceptance；
- collection 自动定位；
- 更完善的归档 reconciliation/repair 工具。
