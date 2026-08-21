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
- `paper-deep-reading`：证据审计、分章节精读、批判性评译，以及 B/C 的制作。

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

当前开发分支进入 **Phase 2 — Literature Search**。

Phase 1 已建立：

- 共享证据、身份、Zotero、状态和数据格式协议；
- 长期知识库 Schema；
- 工作流状态与基础数据管理 CLI；
- 四个 Skill 的职责边界和总控路由骨架。

Phase 2 当前已实现 `literature-search` 的规则层：

- 主题规划与用户 Topic Gate；
- Journal Mapping；
- Search Question Profile、Concept Blocks、Database Routing 与时间角色；
- 两轮筛选、固定排除码、Quality Gate、七维评分和 Method Transfer Checklist；
- Retraction/Correction/Version/SI/Data/Code/Preregistration 等 Integrity Check；
- Primary + Strong Alternatives 推荐逻辑；
- 用户 Paper Gate 后的 selected-paper/source-manifest/Zotero handoff 规则。

下一步是用真实周主题执行一次完整的 Topic → Search → Screening → Paper Selection → Zotero/PROVISIONAL handoff 验收。Translation 和 Deep Reading 的完整实现仍属于后续 Phase 3/4。

当前 PDF 重排和 Zotero 写入接口仍有明确的能力边界；未实现的操作不得伪装成功。

## V1 / V2 边界

V1 按阶段完成 Search、Translation、Deep Reading 与总控集成。系统综述/PRISMA、Meta-analysis、批量候选下载、多 Agent、Web dashboard、自动影响因子数据库和自动重跑原始统计属于 V2 或明确排除项，不应混入当前阶段。

## 基础验证

```bash
python -m compileall scripts
python scripts/validate_deliverables.py --repo-root .
python scripts/workflow_state.py --help
```
