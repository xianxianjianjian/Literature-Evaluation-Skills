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

Git 不长期重复保存 A/B。Zotero 暂时不可用时，待挂接产物可暂存于 `work/<paper_id>/handoff/`，并在当周 `workflow_manifest.yaml.pending_zotero_actions` 中登记。

## 当前开发阶段

`phase-6-v1-hardening` 已封为 **V1 rule-layer / structural Release Candidate**：规则、状态、helper、合成验收、CI 与仓库 hygiene 已通过审核，但真实论文 Production validation 仍保持 OPEN。

`phase-7-zotero-write-adapter` 已封为 parent-create 集成基线：使用官方 Connector `/connector/saveItems` 建立 bibliographic parent，写前查重/目标解析，写后通过 Local API DOI/标题回查。

当前隔离开发分支为 **Phase 8 — Zotero Local Attachments**。Phase 8 使用 Zotero 10+ Local API v3 的本机授权与 full-upload 能力补齐 durable existing-parent attachment：

- Main/SI/A/B 可以在 parent 创建很久之后独立挂接，不依赖短生命周期 Connector session；
- `attach` 默认只预览，`--yes` 才请求 Zotero Desktop 本机写入授权；
- Local API key 只驻留当前进程，不打印、不持久化；
- 写入与验证绑定同一 `Zotero-Server-ID`；
- attachment 只有 parent + filename + MD5 回查一致才成功；
- 已有相同附件幂等复用，断点留下的空 child 可继续上传，同名不同文件停止为冲突；
- CI 使用 synthetic files/mocks，不修改真实 Zotero library。

详见 [`docs/zotero-local-attachments.md`](docs/zotero-local-attachments.md)；Phase 7 的设计背景保留在 [`docs/zotero-write-adapter.md`](docs/zotero-write-adapter.md)。

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
phase-6-v1-hardening          ← sealed rule-layer RC
  ↓
phase-7-zotero-write-adapter ← parent-create baseline
  ↓
phase-8-zotero-local-attachments ← durable attachment integration
```

`main` 仍保持初始提交，等待明确 release 决策。不要逐个重新 merge Phase 1–7；最终只合入被接受的最新累积线。

## 自动验证状态

Draft PR #1 (`phase-6-v1-hardening → main`) 是 Phase 6 RC 的审核/CI 容器，不代表已授权合并。Draft PR #2 审核 Phase 7 parent-create adapter；Draft PR #3 审核 Phase 8 durable attachment adapter。

Phase 8 exact-head smoke tests 已在 Python 3.11 和 3.12 通过：

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

自动测试只验证 deterministic contracts；不能替代用户本机 Zotero Desktop 授权/真实文件写入测试。

## Zotero 10+ durable attachment

预览：

```bash
python scripts/zotero_bridge.py attach \
  --parent-key <ZOTERO_PARENT_KEY> \
  --file <LOCAL_FILE> \
  --name "[ORIGINAL] Main Article"
```

真实写入：

```bash
python scripts/zotero_bridge.py attach \
  --parent-key <ZOTERO_PARENT_KEY> \
  --file <LOCAL_FILE> \
  --name "[ORIGINAL] Main Article" \
  --yes
```

默认目标是 `users/0`。Group library 只有在目标明确且可写时才使用 `--library-prefix groups/<id>`。项目 helper 当前自设单文件 256 MiB 安全上限。

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
- Phase 7 parent-create adapter 的真实本地 Zotero live verification；
- Phase 8 existing-parent Main/SI/A/B local attachment 的真实 Zotero 10+ live authorization/write/post-write verification；
- Mullins 测试所需 Main PDF source blocker。

因此当前结论是：**Zotero durable attachment 的代码/协议/mock 验证已实现；Production live validation 仍 OPEN。**

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
