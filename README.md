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

当前开发分支进入 **Phase 3 — Paper Translation**。

Phase 1 已建立共享协议、Knowledge Schema、状态与基础脚本。Phase 2 已完成 `literature-search` 的规则层，并使用 2026-W34 的真实主题完成 Topic → Search → Screening → Paper Selection 验收；焦点论文已确认为 Mullins et al. (2025), DOI `10.1111/jsr.14281`。由于当前 ChatGPT 会话不能访问用户本机 Zotero Desktop，Search 的 Zotero handoff 按规则保持 `PROVISIONAL`，没有伪装写入成功。

Phase 3 当前已实现 `paper-translation` 的规则层：

- Context-sensitive terminology + TE1–TE7 evidence-source types；
- Abstract 两遍翻译 + alignment + 唯一 Canonical Abstract；
- Page/Section/Paragraph Translation Units 与 translation ledger；
- Main + Supporting Information 全覆盖与 Source Gap 标记；
- Figure/Table 数据锁定和 SI 处理；
- `Strict Mirror → Adaptive Mirror → Readable Extension` 镜像排版；
- Coverage / Semantic / Numeric / Layout 四层 Translation QC；
- Zotero unavailable 时的 `PROVISIONAL` / pending handoff 规则。

当前真实 Mullins 2025 验收已完成出版身份、Wiley Version of Record、PMID/PMCID 和 Supporting Figure S1 核验。网页通道能够读取出版社/PMC 正文信息，但 Wiley PDF 二进制下载在当前环境返回 403；在取得真实 Main PDF 之前，不得伪造页面对应的 A 镜像 PDF。

Deep Reading 的完整实现仍属于 Phase 4。

## V1 / V2 边界

V1 按阶段完成 Search、Translation、Deep Reading 与总控集成。系统综述/PRISMA、Meta-analysis、批量候选下载、多 Agent、Web dashboard、自动影响因子数据库和自动重跑原始统计属于 V2 或明确排除项，不应混入当前阶段。

## 基础验证

```bash
python -m compileall scripts
python scripts/validate_deliverables.py --repo-root .
python scripts/workflow_state.py --help
```
