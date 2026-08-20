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

当前为 **Phase 1 — Repository Foundation**，只提供：

- 共享证据、身份、Zotero、状态和数据格式协议；
- 长期知识库 Schema；
- 工作流状态与基础数据管理 CLI；
- 四个 Skill 的职责和路由骨架。

当前脚本中的 PDF 重排、Zotero 写入以及完整学术流程均为受控接口或占位框架，不代表相应生产能力已经实现。

## V1 / V2 边界

V1 将按阶段完成 Search、Translation、Deep Reading 与总控集成。V2 才考虑在真实使用反馈支持下扩展更复杂的自动化；系统综述、PRISMA、Meta-analysis、多 Agent、Web dashboard 和自动重跑原始统计不属于 Phase 1。

## 基础验证

```bash
python -m compileall scripts
python scripts/validate_deliverables.py --repo-root .
python scripts/workflow_state.py --help
```
