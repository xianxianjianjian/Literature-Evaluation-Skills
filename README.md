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

- `weekly-literature-evaluation`：薄总控，只负责意图路由、状态、断点恢复、用户决策 Gate 和子 Skill 调度。
- `literature-search`：规划主题、检索与筛选文献、确认最终论文并准备 Zotero 入库。
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
Git:    Skills / knowledge / search history / C / workflow state
```

Git 不长期重复保存 A/B。Zotero 暂时不可用时，待挂接产物可暂存于 `work/<paper_id>/handoff/`，并在当周 `workflow_manifest.yaml` 的 `pending_zotero_actions` 中登记。

## 当前开发阶段

当前开发分支进入 **Phase 4 — Paper Deep Reading**。

Phase 1 已建立共享协议、Knowledge Schema、状态与基础脚本。Phase 2 已完成 `literature-search` 规则层，并用真实周主题完成 Topic → Search → Screening → Paper Selection 验收。Phase 3 已完成 `paper-translation` 规则层，包括术语证据、Canonical Abstract、Translation Units、Main+SI、Figure/Table、镜像排版与四层 QC。

真实 Mullins 2025 端到端测试当前暂停：焦点论文身份和来源已核验，但当前环境无法取得用于逐页镜像的 Main PDF 二进制，因此测试状态保留为 `Translation = BLOCKED`。该真实测试记录不被删除，也不妨碍继续完成 V1 Skill 规则层；未来取得 Main PDF 后可从 manifest 直接恢复。

Phase 4 当前已实现 `paper-deep-reading` 的规则层：

- Search Intake / Translation Intake / Full Research Audit 三层审计；
- Publication Identity、Source Package、Paper Structure Inventory 与 A0–A3；
- Introduction 论证链、Research Gap、RQ/Aim/Hypothesis 与 Hypothesis Matrix；
- Study Architecture、Sample Ledger、Measurement Chain、被试/研究者双流程；
- Acquisition 与 Preprocessing 分离、Reproducibility Gap Table；
- Analysis Question Tree、Result Matrix、非显著结果、校正与统计一致性复核；
- Author Discussion 与 Evaluator Critique 分离、ED0–ED3；
- Innovation / Limitations / Redesign / Transfer Value；
- Dynamic Coverage 与 Source→Notebook closure；
- B/C 交付与最终 Evidence/Methods/Results/Discussion QC。

下一步为 Phase 5：完成 `weekly-literature-evaluation` 薄总控、跨 Skill handoff/resume/state 路由和 V1 全局完成条件。真实 T01–T04 端到端验收将在规则层全部封板后统一恢复。

## V1 / V2 边界

V1 按阶段完成 Search、Translation、Deep Reading 与总控集成。系统综述/PRISMA、Meta-analysis、批量候选下载、多 Agent、Web dashboard、自动影响因子数据库和自动重跑原始统计属于 V2 或明确排除项，不应混入当前阶段。

## 基础验证

```bash
python -m compileall scripts
python scripts/validate_deliverables.py --repo-root .
python scripts/workflow_state.py --help
```
