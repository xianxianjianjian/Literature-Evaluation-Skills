# State Contract

当周唯一工作流事实来源是：

```text
<data-root>/weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml
```

不得再维护第二份全局 `status.yaml`。每个状态变化必须写回该 manifest，恢复流程必须先读取它和现有产物。

Translation stage additionally records its requested scope:

```yaml
stages:
  translation:
    scope: FULL_MIRROR  # FULL_MIRROR | MAIN_ONLY | ABSTRACT_ONLY
```

New weekly manifests default to `FULL_MIRROR`. Older manifests remain readable with a null/missing scope, but scope must be made explicit before Translation can become `COMPLETE`.

## 允许状态

```text
NOT_STARTED
IN_PROGRESS
WAITING_USER
BLOCKED
PROVISIONAL
COMPLETE
```

禁止增加 `STALE`。需要重新更新时使用：

```yaml
needs_update: true
update_reason:
  - "新增 Supplement，需要重新核验 Results"
```

更新完成后设置 `needs_update: false` 并清空 `update_reason`。

## 状态语义

- `NOT_STARTED`：尚未开始。
- `IN_PROGRESS`：正在执行且存在可恢复进度。
- `WAITING_USER`：只用于需要用户学术决策的 Gate。
- `BLOCKED`：缺失依赖使当前学术工作无法继续得到可辩护结果。
- `PROVISIONAL`：已有可用学术结果，但仍存在会影响当前任务范围完整性的明确来源、SI、版本、证据或产物缺口。
- `COMPLETE`：该阶段自身的学术/产物完成条件和 QC 已满足。

`COMPLETE` 不等于永远无需更新；Source Change Check 可在保持历史完成记录的同时设置 `needs_update: true`。

## 学术完成与归档完成分离

V1 的阶段状态首先描述**学术工作和对应产物本身**，不再把某一种外部归档传输方式混入阶段状态。

因此：

- Search 的选题、筛选、论文确认和 source/package handoff 已完成时，Search 可以 `COMPLETE`；
- A 已生成且 Translation QC 通过时，Translation/A 可以 `COMPLETE`；
- B/C 和 Deep Reading QC 已完成时，Deep Reading/B/C 可以 `COMPLETE`；
- Zotero 暂时不可写、自动 attachment 尚未验证或需要之后人工挂接，**本身不应把上述学术阶段降为 `PROVISIONAL`**。

Zotero 等归档待办通过：

```yaml
pending_zotero_actions:
  - action: attach
    source_id: SRC-M1
    expected_attachment_name: "[ORIGINAL] Main Article"
```

单独记录。只有当缺失 Zotero 中的文件意味着**源证据本身也不可用**时，才根据真实证据缺口影响学术阶段状态。

### Academic completion

学术工作流可判定完成的最低条件是：适用阶段与 A/B/C 的学术/QC 条件通过、没有 consequential blocker、没有 unresolved `needs_update`，并完成要求的周记录/知识记录。

`pending_zotero_actions` 可以与学术阶段 `COMPLETE` 共存。

### Archive completion

归档完成是比学术完成更严格的额外闭环。若用户要求“完整 Zotero 归档”，还需确认所需 Main/SI/A/B parent/attachment 实际存在并验证，且相应 `pending_zotero_actions` 已清空。

不得因为学术工作已完成就声称“Zotero 归档已完成”；两者必须分别报告。

## 固定用户 Gate

完整每周流程只有两个固定人工 Gate：用户确定主题、用户确定最终论文。其余机械步骤原则上不重复询问，除非涉及新的权限、风险或真正异常。
