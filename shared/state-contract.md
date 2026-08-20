# State Contract

当周唯一工作流事实来源是：

```text
weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml
```

不得再维护第二份全局 `status.yaml`。每个状态变化必须写回该 manifest，恢复流程必须先读取它和现有产物。

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

更新完成后设置 `needs_update: false` 并清空 `update_reason`。`PROVISIONAL` 表示当前产物可使用但证据包或挂接尚不完整；不得把它声称为完整研究档案。

## 状态语义

- `NOT_STARTED`：尚未开始。
- `IN_PROGRESS`：正在执行且存在可恢复进度。
- `WAITING_USER`：只用于需要用户学术决策的 Gate。
- `BLOCKED`：外部依赖或不可恢复错误阻止当前阶段继续。
- `PROVISIONAL`：已有可用结果，但存在明确资料或系统缺口。
- `COMPLETE`：该阶段的完成条件和验证均已满足。

`COMPLETE` 不等于永远无需更新；Source Change Check 可在保持历史完成记录的同时设置 `needs_update: true`。

## 固定用户 Gate

完整每周流程只有两个固定人工 Gate：用户确定主题、用户确定最终论文。其余机械步骤原则上不重复询问，除非涉及新的权限、风险或真正异常。
