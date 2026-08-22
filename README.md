# Literature Evaluation Plugin

一套面向长期科研使用的**文献检索 → 全文评译 → 系统精读 → 每周评译提交**工作流。

V1 的核心目标不是生成普通摘要，而是形成可核验、可追溯、可恢复的研究档案：重要结论回到原文位置，作者解释与评译者分析分离，Main/SI 一体审计，Translation/Methods/Results/Discussion 都有明确完成与 QC 规则。

当前插件版本：`1.1.0`。本次升级只改变安装、运行路径、工作区与打包方式，不修改 V1 已冻结的学术逻辑、两个 Gate、证据合同或 A/B/C 范围。

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

三个专业 Skill 可以绕过总控独立运行。

安装后四个可发现入口为：

- `literature-evaluation:weekly-literature-evaluation`
- `literature-evaluation:literature-search`
- `literature-evaluation:paper-translation`
- `literature-evaluation:paper-deep-reading`

## 构建本地 Plugin bundle

仓库根目录本身是 `literature-evaluation` 插件源码。构建脚本生成本地 marketplace 安装包，不在 Git 中维护第二份 Skill 源码。

最方便的仓库内生成方式是使用已经被 `.gitignore` 排除的 `dist/`：

```bash
python scripts/build_plugin_bundle.py \
  --output dist/literature-evaluation-local \
  --archive dist/literature-evaluation-local.zip
```

也可以把 `--output` 指向插件源码树之外的绝对路径。如果输出位于插件源码树内，只允许放在 `<plugin-root>/dist/` 下，不能写进 `skills/`、`shared/`、`scripts/`、`assets/` 等源码目录。ZIP 必须位于 bundle 输出目录之外；上例中的 sibling ZIP 是合法布局。

将生成的 marketplace 加入 Codex：

```bash
codex plugin marketplace add /absolute/path/to/literature-evaluation-local
```

如果使用上面的 `dist/` 示例，请把 `<bundle-root>` 解析为 `dist/literature-evaluation-local` 的绝对路径。然后重启支持 Plugins 的 Codex/ChatGPT 客户端，在 Plugins Directory 中选择 `literature-evaluation-local` marketplace 并安装 `literature-evaluation`。不同客户端版本可能提供额外的安装子命令；以当前客户端 `codex plugin --help` 和 OpenAI Plugin 文档为准，不把未验证的快捷命令作为唯一安装路径。

当前机器如果已经通过 Skill installer 分别安装过同名的四个独立 Skill，不要自动删除。应先确认插件版四个 namespaced Skill 均能发现和运行，再单独移除旧副本，避免重复发现或路由冲突。

## 插件资源与用户数据分离

插件安装目录只保存只读资源：

```text
<plugin-root>/
|-- .codex-plugin/
|-- skills/
|-- shared/
|-- scripts/
`-- assets/workspace-template/
```

用户自己的研究数据写入独立 data root：

```text
<data-root>/
|-- workspace.json
|-- knowledge/
|-- weekly_reviews/
`-- work/
```

默认 data root 是研究项目中的 `.literature-evaluation/`。

### 数据根解析顺序

固定为：

1. 显式 `--workspace-root <path>`；
2. 环境变量 `LITERATURE_EVALUATION_HOME`；
3. 从当前目录向父目录查找已经初始化的 `.literature-evaluation/workspace.json`；
4. 若尚未初始化且位于 Git 项目中，使用 Git 项目根下的 `.literature-evaluation/`；
5. 最后才使用当前目录下的 `.literature-evaluation/`。

这样即使从同一研究项目的不同子目录启动 Codex，也不会轻易生成多份互相分叉的 `research_profile`、`reading_history` 或 workflow manifest。

## 初始化与旧数据迁移

首次写入前初始化：

```bash
python <plugin-root>/scripts/init_workspace.py
```

显式指定数据根：

```bash
python <plugin-root>/scripts/init_workspace.py \
  --workspace-root <data-root>
```

从旧版仓库根迁移时先预演：

```bash
python <plugin-root>/scripts/init_workspace.py \
  --workspace-root <data-root> \
  --migrate-from <legacy-root> \
  --dry-run
```

确认后去掉 `--dry-run`。初始化幂等且不覆盖已有用户文件；迁移遇到同名不同内容时停止。迁移源和目标必须是两个互不包含的目录树。

仓库根现有 `knowledge/` 与 `weekly_reviews/` 继续作为 V1 历史/真实验收样例保留，但插件运行时不得继续把它们当默认写入目标。

`<data-root>/knowledge/submission_profile.yaml` 当前采用 JSON-compatible YAML 表示，以保持标准库实现；不要把它改成任意 YAML 语法，除非后续版本正式加入 YAML parser。

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
2. 在有本地运行环境时把待归档文件放到 `<data-root>/work/<paper_id>/handoff/`；
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
<data-root>/weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml
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

不使用 `STALE`；来源更新使用 `needs_update` + `update_reason`。`WAITING_USER` 在普通完整流程里只用于两个固定 Gate。

## Git / knowledge

长期维护：

- `<data-root>/knowledge/research_profile.md`
- `<data-root>/knowledge/submission_profile.yaml`
- `<data-root>/knowledge/journal_registry.csv`
- `<data-root>/knowledge/terminology_registry.csv`
- `<data-root>/knowledge/terminology_evidence.jsonl`
- `<data-root>/knowledge/reading_history.csv`
- `<data-root>/knowledge/selection_log.csv`

`research_profile.md` 不能因一篇论文自动改方向；任何长期研究方向变更都需要用户明确确认。

术语身份至少考虑：

```text
English Term + Discipline + Subfield + Context
```

同一个英文词可以在不同研究语境拥有不同中文译法。`HIGH / MEDIUM / LOW` 是置信度；`TE1–TE7` 是中文术语依据来源类型，两者不得混用。

## 自动验证

仓库在 Python 3.11 / 3.12 执行：

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_plugin_package.py --plugin-root .
python scripts/validate_deliverables.py --repo-root .
```

已安装插件与独立数据目录分别验证：

```bash
python <plugin-root>/scripts/validate_plugin_package.py \
  --plugin-root <plugin-root>

python <plugin-root>/scripts/validate_deliverables.py \
  --plugin-root <plugin-root> \
  --workspace-root <data-root>
```

`validate_plugin_package.py` 检查插件名、版本、Skill 路径、Research 类别、短描述、四个 Skill frontmatter、最终 `literature-evaluation:<skill>` namespaced 名称、四个 `agents/openai.yaml` 以及必要共享资源；它是仓库内 structural validation，不能替代实际客户端中的 Plugin discovery/install 验收。

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

这些工作不阻塞 V1 学术工作流正常使用。

## 真实验收记录

Mullins et al. (2025) 的首次真实流程测试保留在根级 `weekly_reviews/2026/2026-W34/`。该记录属于 V1 历史样例；因为 Main PDF 当时无法取得而保持真实 blocker，没有为了让测试变绿伪造完成。新插件 workspace 模板不会复制该样例。

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

## Release 与分支策略

V1 核心于 2026-08-21 合并到 `main`；`v1.0.0` tag 固定核心发布点。插件化升级在具体 topic branch 开发，不恢复旧 Phase 编号。

长期分支仍以 `main` 为稳定主线。功能分支在验证和合并后可删除，历史由 Git commits/tags 保留。

详见 [`docs/branch-strategy.md`](docs/branch-strategy.md) 和 [`docs/releases/v1.0.0.md`](docs/releases/v1.0.0.md)。
