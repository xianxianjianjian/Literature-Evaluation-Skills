# Literature Evaluation Skills

一套面向长期使用的每周学术文献检索、专业翻译与系统精读 Skills 系统。项目把可复用的业务协议、长期知识状态和每周工作流状态保存在 Git 中，把论文原文、补充材料及大体积研究产物交给 Zotero 管理。

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

当前开发分支为 **Phase 5 — V1 Orchestration / Rule-Layer Completion**。

### Phase 1 — Foundation

已建立：

- Evidence / Identifier / Source Identity / Zotero / State / Data Format shared contracts；
- Research Profile、Submission Profile、Journal/Terminology/Reading/Selection knowledge schemas；
- workflow/history/terminology/validation/Zotero/mirror-PDF 基础脚本接口；
- 四个 Skill 的职责边界。

### Phase 2 — Literature Search

已完成：

- Topic Planning + Topic Gate；
- Journal Mapping；
- Search Question Profile、Concept Blocks、Database Routing、Recency Roles；
- Round 1 / Round 2 screening；
- EX-01–EX-13；
- GREEN / AMBER / RED Quality Gate；
- 25/20/15/15/10/10/5 七维评分；
- Method Transfer Checklist；
- Retraction/Correction/Version/SI/Data/Code/Preregistration Integrity Check；
- Primary + Strong Alternatives + Paper Gate；
- selected-paper/source/Zotero handoff。

### Phase 3 — Paper Translation

已完成：

- Context-sensitive terminology；
- TE1–TE7 evidence-source types 与 HIGH/MEDIUM/LOW confidence 分离；
- Abstract 两遍翻译 + Alignment + 唯一 Canonical Abstract；
- Page/Section/Paragraph Translation Units 与 ledger；
- Main + SI coverage 与 Source Gap；
- Figure/Table 数据锁定；
- `Strict Mirror → Adaptive Mirror → Readable Extension`；
- Coverage / Semantic / Numeric / Layout QC；
- A 与 Zotero/PROVISIONAL handoff 规则。

### Phase 4 — Paper Deep Reading

已完成：

- Search Intake / Translation Intake / Full Research Audit；
- Publication Identity、Source Package、Paper Structure Inventory、A0–A3；
- Introduction argument chain、Research Gap、RQ/Aim/Hypothesis、Hypothesis Matrix；
- Study Architecture、Sample Ledger、Measurement Chain；
- Participant / Researcher 双流程；
- Acquisition / Preprocessing 分离与 Reproducibility Gap；
- Analysis Question Tree、Result Matrix、非显著结果、Correction、统计一致性复核；
- Figure/Table visual audit；
- Author Discussion / Evaluator Critique 分离与 ED0–ED3；
- Innovation / three-layer Limitations / Redesign / Transfer Value；
- Dynamic Coverage + Source→Notebook closure；
- B/C 与最终 QC。

### Phase 5 — Weekly Orchestration

已完成规则层：

- `FULL_WEEKLY / SEARCH_ONLY / TRANSLATION_ONLY / DEEP_READING_ONLY / RESUME / UPDATE_EXISTING` 路由；
- 两个固定人工 Gate；
- Paper Gate 后普通后续工作的授权边界；
- dependency-aware handoff；
- `BLOCKED / PROVISIONAL / COMPLETE` 传播规则；
- source change + `needs_update` 更新链；
- artifact identity/reuse；
- Zotero outage downgrade；
- A/B/C、knowledge、archive 的 V1 全局完成条件。

## 真实验收状态

规则层继续开发期间，真实 Mullins et al. (2025), DOI `10.1111/jsr.14281` 端到端测试已主动暂停。

该验收已经完成 Topic → Search → Screening → Paper Selection，并保留在 `weekly_reviews/2026/2026-W34/`。当前环境无法取得用于逐页镜像的 Main PDF 二进制，因此真实 manifest 仍准确保留 `Translation = BLOCKED` 和 `A = BLOCKED`；没有为了开发进度伪造完成状态。

未来取得 Main PDF 后，应直接从该 manifest 恢复 Translation，而不是重新执行已经完成的 Topic/Paper Gates。

## 当前含义

**四个 Skill 的 V1 规则层现已全部写齐。**

这不等于整个系统已经通过生产验收。后续仍需要：

- 对脚本接口做 Phase 5 集成补强；
- 恢复并完成真实 A/B/C 测试；
- 执行 T01–T04 与 Search-only / Translation-only / Deep-Reading-only / Resume / Zotero downgrade / new-SI update 验收；
- 根据测试结果修复规则或实现缺口；
- 最终决定分支合并与 main 封板。

## V1 / V2 边界

系统综述/PRISMA、Meta-analysis、批量候选下载、多 Agent、Web dashboard、自动影响因子数据库、citation graph 和自动重跑原始统计不属于当前 V1。

## 基础验证

```bash
python -m compileall scripts
python scripts/validate_deliverables.py --repo-root .
python scripts/workflow_state.py --help
```
