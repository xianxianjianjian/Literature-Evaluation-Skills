# Literature Evaluation Skills V1

一套面向长期科研使用的**文献检索 → 全文评译 → 系统精读 → 每周评译提交**工作流。

V1 的核心目标不是生成普通摘要，而是形成可核验、可追溯、可恢复的研究档案：重要结论回到原文位置，作者解释与评译者分析分离，Main/SI 一体审计，Translation/Methods/Results/Discussion 都有明确完成与 QC 规则。

## 四 Skill 架构

```text
weekly-literature-evaluation
        |
        |-- literature-search
        |-- paper-translation
        `-- paper-deep-reading
```

- **`weekly-literature-evaluation`**：薄总控。负责意图路由、两个用户 Gate、状态、断点恢复和跨 Skill handoff，不承担实际学术判断。
- **`literature-search`**：主题规划、Journal Mapping、检索策略、两轮筛选、Quality Gate、7D 排名、Integrity Check、最终论文确认与 source handoff。
- **`paper-translation`**：术语核验、唯一 Canonical Abstract、Main/SI 全文翻译、表图/数字完整性和 A 镜像 PDF。
- **`paper-deep-reading`**：Full Research Audit、Introduction/Methods/Results/Discussion 重建、统计路线、假设闭环、批判性评译，以及 B/C。

三个专业 Skill 可以独立运行。

## 交付物

- **A**：中文全文翻译镜像版 PDF。
- **B**：完整文献研究笔记 DOCX。
- **C**：每周评译提交稿。

C 中的评论正文默认至少 500 个有效中文字符；原文摘要与中文摘要不计入这 500 字。

## 最快开始方式

### 完整每周流程

向总控提出本周文献评译需求。标准流程只有两个固定人工 Gate：

```text
研究背景/历史
→ 3–5 个主题候选
→ Gate 1：确认本周主题
→ 正式检索与筛选
→ Primary + Alternatives
→ Gate 2：确认最终论文
→ Source/Main/SI intake
→ Translation + A
→ Deep Reading + B
→ C
→ knowledge/history 更新
→ 可选 Zotero 归档清理
```

Gate 通过后，后续普通翻译、精读、A/B/C 与安全归档操作不应反复询问。

### 只运行一个专业 Skill

可以直接提供论文/主题并运行：

- Search-only；
- Translation-only；
- Deep-Reading-only；
- Resume；
- Update existing paper/source。

直接进入 Translation 或 Deep Reading 时仍必须做 Minimal Intake，不能跳过论文身份和来源核验。

## 核心证据合同

重要内容区分：

- `【原文直接内容】`
- `【作者解释】`
- `【评译者分析】`
- `【外部依据 EXT-xxx】`

证据类型与 Source Anchor 是两个维度。重要结论尽量定位到 Section/Subsection/Page/Table/Figure/SI。

系统不得：

- 把论文引用过的文献自动当成已独立核验的外部依据；
- 用“常见做法”补原文没报告的方法参数；
- 用总体 N 替代未知的模型 N；
- 把相关、横断面中介、功能连接写成已证明的因果机制；
- 静默修正作者原始统计值或省略重要非显著结果。

## Academic completion 与 Archive completion

V1 明确分成两个完成维度。

### Academic workflow COMPLETE

当 Search、Translation/A、Deep Reading/B/C 的学术与 QC 条件通过，来源身份足以支持任务范围，历史/周记录完成，且没有 consequential blocker / `needs_update` 时，学术工作流可以完成。

**Zotero 自动写入不是这一层的前置条件。**

### Zotero archive COMPLETE

Zotero 是首选长期档案：

```text
Zotero: Main / SI / A / B
Git:    Skills / shared policies / knowledge / Search decisions / C / workflow state
```

如果 Zotero 暂时不可写：

1. 继续所有安全的学术工作；
2. 在有本地运行环境时把待归档文件放到 `work/<paper_id>/handoff/`；
3. 在 manifest 记录 `pending_zotero_actions`；
4. 可以之后手动挂接 Zotero，再做身份验证；
5. 不得在未验证时声称“已经保存到 Zotero”。

因此允许：

```text
Academic workflow: COMPLETE
Zotero archive: PENDING
```

详见 [`docs/v1-scope-freeze.md`](docs/v1-scope-freeze.md) 和 [`shared/zotero-policy.md`](shared/zotero-policy.md)。

## 工作流状态

唯一周状态文件：

```text
weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml
```

只允许：

```text
NOT_STARTED
IN_PROGRESS
WAITING_USER
BLOCKED
PROVISIONAL
COMPLETE
```

不使用 `STALE`；来源更新使用 `needs_update` + `update_reason`。

`WAITING_USER` 在普通完整流程里只用于两个固定 Gate。

## Git / knowledge

长期维护：

- `knowledge/research_profile.md`
- `knowledge/submission_profile.yaml`
- `knowledge/journal_registry.csv`
- `knowledge/terminology_registry.csv`
- `knowledge/terminology_evidence.jsonl`
- `knowledge/reading_history.csv`
- `knowledge/selection_log.csv`

`research_profile.md` 不能因一篇论文自动改方向；任何长期研究方向变更都需要用户明确确认。

## 术语规则

术语身份至少考虑：

```text
English Term + Discipline + Subfield + Context
```

同一个英文词可以在不同研究语境拥有不同中文译法。`HIGH / MEDIUM / LOW` 是置信度；`TE1–TE7` 是中文术语依据来源类型，两者不得混用。

## 自动验证

仓库使用 GitHub Actions 在 Python 3.11 / 3.12 运行：

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

完成级别可分别检查：

```bash
# 学术流程完成；允许 Zotero pending
python scripts/validate_deliverables.py \
  --repo-root . \
  --manifest <workflow_manifest.yaml> \
  --require-academic-complete

# 更严格的 Zotero archive closure
python scripts/validate_deliverables.py \
  --repo-root . \
  --manifest <workflow_manifest.yaml> \
  --require-archive-complete
```

旧参数 `--require-workflow-complete` 保留为严格 archive-complete 的兼容别名。

## Zotero 自动化状态

仓库保留已开发的 Connector / Zotero 10+ Local API helper，但它们属于**可选归档增强**：

- parent create 已有 Connector 实现；
- existing-parent local-file attachment 已有 Local API 协议/mock/CI 实现；
- 真实用户桌面端 live validation、group-library 统一路由和 parent-create Local API 迁移均列为后续优化。

这些工作不再阻塞 V1 发布和正常使用。

## 真实验收记录

Mullins et al. (2025) 的首次真实流程测试保留在 `weekly_reviews/2026/2026-W34/`。该测试因为 Main PDF 当时无法取得而保持真实 blocker，没有为了让测试“变绿”伪造完成。

它是一个断点恢复样例，不是 V1 是否可发布的单一前置条件。

## V1 不做什么

以下明确属于后续版本：

- 系统综述 / PRISMA；
- Meta-analysis；
- 批量候选下载；
- citation graph；
- 多 Agent 并行；
- Web dashboard；
- 自动影响因子数据库；
- 自动重跑论文原始统计/实验代码；
- publisher-grade 一键 PDF 重排。

## 分支策略

早期 `phase-1` 到 `phase-8` 是累计开发里程碑，不是八套不同 Skill。现在停止继续新增编号 Phase。

正式收束工作只在：

```text
v1-release-candidate
```

进行。完成最终 CI / diff / hygiene 审核并获得明确发布决定后，再把该累计 RC 合入 `main`。

详见 [`docs/branch-strategy.md`](docs/branch-strategy.md)。
