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

当前开发分支为 **Phase 6 — V1 Hardening / Release Preparation**。

Phase 1–5 已累计完成四个 Skill 的 V1 规则层：Foundation → Literature Search → Paper Translation → Paper Deep Reading → Weekly Orchestration。Phase 6 不再扩展新的学术功能，重点是检查并补齐：

- Skill rules ↔ shared contracts；
- Skill rules ↔ knowledge schemas；
- Skill rules ↔ workflow manifest；
- Skill rules ↔ helper scripts；
- deterministic tests / regression protection；
- release 前的 capability boundary 与 branch hygiene。

当前已完成的 hardening 包括：

- `workflow_state.py` 升级为 V1 manifest helper，支持 `paper_id`、全阶段 `needs_update`、A/B/C 状态、`blocking_issues`、`pending_zotero_actions`、source-check date，以及两个固定 `WAITING_USER` Gate 的语义校验；
- `validate_deliverables.py` 升级为 V1 结构验证器，检查 19 个 specialist references、A PDF、B DOCX Base Schema、C 必填字段/评论字数/Canonical Abstract 一致性及关键 manifest 完成关系；
- `mirror_pdf.py` 升级为 V1 确定性 layout/QC helper，并明确 `Strict Mirror → Adaptive Mirror → Readable Extension` 与 render-first QA；
- 增加 `tests/test_core.py` 和 GitHub Actions `V1 Smoke Tests`；
- 增加 `docs/v1-hardening-audit.md` 与 `docs/branch-strategy.md`。

## Branch 关系

本仓库的 Phase 分支是**累积式里程碑**，不是互相独立的五套实现：

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
phase-6-v1-hardening
```

因此最终通过验收后，通常只需要把最新的已接受累积分支合入 `main`，无需逐个再次合并 Phase 1→5。详见 [`docs/branch-strategy.md`](docs/branch-strategy.md)。

## 真实验收状态

真实 Mullins et al. (2025), DOI `10.1111/jsr.14281` 端到端测试已主动暂停，但测试现场保留在 `weekly_reviews/2026/2026-W34/`。

该验收已经完成 Topic → Search → Screening → Paper Selection。当前环境无法取得用于逐页镜像的 Main PDF 二进制，因此 manifest 仍准确保留 `Translation = BLOCKED` 和 `A = BLOCKED`；没有为了开发进度伪造完成状态。

未来取得 Main PDF 后，应直接从该 manifest 恢复，不重新执行已经通过的 Topic/Paper Gates。

## 当前尚未关闭的 V1 集成点

- Zotero Desktop Local API 只读；`create / attach` 仍需要经过可验证的 Connector/plugin write route，不能假装成功。
- `mirror_pdf.py` 是确定性布局/QC辅助器，不是出版社级全自动重排引擎；真正 A 仍必须 render → inspect → iterate → re-render。
- 自动测试已加入仓库，但 GitHub Actions 的实际运行状态需在 release 前确认。
- T01–T04、Search-only、Translation-only、Deep-Reading-only、Resume、Zotero downgrade、new-SI update 等真实验收仍待统一执行。

## V1 / V2 边界

系统综述/PRISMA、Meta-analysis、批量候选下载、多 Agent、Web dashboard、自动影响因子数据库、citation graph 和自动重跑原始统计不属于当前 V1。

## 基础验证

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
python scripts/workflow_state.py --help
```
