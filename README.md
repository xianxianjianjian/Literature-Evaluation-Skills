# Literature Evaluation Skills

一套面向长期使用的每周学术文献检索、专业翻译与系统精读 Skills 系统。项目把可复用业务协议、长期知识状态和每周工作流状态保存在 Git 中，把论文原文、补充材料及大体积研究产物交给 Zotero 管理。

## 四 Skill 架构

```text
weekly-literature-evaluation
        |
        |-- literature-search
        |-- paper-translation
        `-- paper-deep-reading
```

- `weekly-literature-evaluation`：薄总控，只负责意图路由、状态、断点恢复、用户决策 Gate 和跨 Skill handoff。
- `literature-search`：规划主题、检索与筛选文献、确认最终论文并准备 Zotero/Source handoff。
- `paper-translation`：术语核验、Canonical Abstract、全文与补充材料翻译，以及 A 的制作。
- `paper-deep-reading`：证据审计、理论/方法/结果/讨论重建、批判性评译，以及 B/C 的制作。

三个专业 Skill 必须可以独立运行；总控不得承担实际学术分析。

## 交付物 A / B / C

- **A**：中文全文翻译镜像 PDF。
- **B**：完整文献研究笔记 DOCX。
- **C**：每周评译提交稿。

## Git 与 Zotero 的边界

```text
Zotero: Main / SI / A / B
Git:    Skills / shared policies / knowledge / search decisions / C / workflow state
```

Git 不长期重复保存 A/B。Zotero 暂时不可用时，待挂接产物可暂存于 `work/<paper_id>/handoff/`，并在当周 `workflow_manifest.yaml` 的 `pending_zotero_actions` 中登记。

## 当前开发阶段

`phase-6-v1-hardening` 已封为 **V1 rule-layer / structural Release Candidate**：规则、状态、helper、合成验收、CI 与仓库 hygiene 已通过审核，但真实论文 Production validation 仍保持 OPEN。

当前隔离开发分支为 **Phase 7 — Zotero Write Adapter**。Phase 7 不改学术规则，只缩小 Zotero 生产集成缺口：

- bibliographic parent create：使用官方 Zotero Connector `/connector/saveItems`；
- create 前先查重，写后必须通过只读 Local API 做 DOI/标题身份回查；
- 没有 `--yes` 时 `create` 只预览，不执行写入；
- local-file attach（Main/SI/A/B → 已有 parent）仍未实现，继续明确记录为 pending/provisional；
- 不会因为 Connector 在线或 HTTP 201 就把整个 Zotero 档案标记 COMPLETE。

详见 [`docs/zotero-write-adapter.md`](docs/zotero-write-adapter.md)。

## 已完成的 V1 hardening

- `workflow_state.py`：V1 manifest、`paper_id`、`needs_update`、A/B/C、blockers、pending Zotero、source-check date、两个固定 Gate；
- `history_manager.py`：Selection 同周去重/跨周允许；`reading_history.csv` 仅允许真实 `Deep Reading = COMPLETE`；
- `terminology_registry.py`：`lookup / add / update / context / status / export`，上下文术语身份与历史保留；
- `validate_deliverables.py`：19 个 specialist references、A/B/C 结构、Canonical Abstract、comment 字数和 full-workflow closure；
- `mirror_pdf.py`：`Strict Mirror → Adaptive Mirror → Readable Extension` 与 render-first QA；
- GitHub Actions：Python 3.11 / 3.12 smoke tests；
- synthetic T01–T04、specialist-only、Resume、Zotero downgrade、new-SI update；
- real Mullins 2025 blocked/provisional trace 的 CI 防回退保护。

## Branch 关系

Phase 分支是**累积式里程碑**，不是互相独立的实现：

```text
main
  ↓
phase-1-foundation
  ↓
phase-2-search
  ↓
phase-3-translation
  ↓
phase-4-deep-reading
  ↓
phase-5-orchestration
  ↓
phase-6-v1-hardening        ← sealed rule-layer RC
  ↓
phase-7-zotero-write-adapter ← isolated integration work
```

`main` 仍保持初始提交，等待明确的 release 决策。不要逐个重新 merge Phase 1–5；最终只合入被接受的最新累积线。

## 自动验证状态

Draft PR #1 (`phase-6-v1-hardening → main`) 是 Phase 6 RC 的审核/CI 容器，不代表已授权合并。

Phase 6 exact-head `V1 Smoke Tests` 已在 Python 3.11 和 3.12 实际通过：

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

Phase 7 使用独立 PR/CI 验证 Zotero parent-create adapter；mock 测试不能代替未来在用户本地 Zotero Desktop 上的 live write verification。

## 真实验收状态

真实 Mullins et al. (2025), DOI `10.1111/jsr.14281` 端到端测试已主动暂停，但测试现场保留在 `weekly_reviews/2026/2026-W34/`。

已完成 Topic → Search → Screening → Paper Selection。当前环境无法取得用于逐页镜像的 Main PDF，因此 manifest 仍准确保持：

```text
Search = PROVISIONAL
Translation = BLOCKED
A = BLOCKED
Deep Reading = NOT_STARTED
```

未来取得 Main PDF 后，应从该 manifest 继续，不重复已经满足的用户 Gate。

## 当前尚未关闭的 Production gates

- 真实 T01–T04 学术验收；
- A 的真实 render → inspect → iterate → re-render；
- B 的真实 evidence/source-anchor closure；
- C 的真实 Canonical Abstract/comment/reviewer 验收；
- Zotero local-file attachment adapter 及 Main/SI/A/B post-write verification；
- Phase 7 parent-create adapter 的真实本地 Zotero live verification。

## V1 / V2 边界

系统综述/PRISMA、Meta-analysis、批量候选下载、多 Agent、Web dashboard、自动影响因子数据库、citation graph 和自动重跑原始统计不属于当前 V1。

## 基础验证

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
python scripts/workflow_state.py --help
python scripts/zotero_bridge.py --help
```
