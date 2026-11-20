# 文献评译插件（Literature Evaluation）

面向科研文献的模块化 Skill 工作流，覆盖 **文献检索 → 全文翻译 → 系统精读 → 每周评译提交** 全流程，强调证据可追溯、过程可审计、结果可复现。

> 当前版本（Software version: **v1.6.0**）：版本号以 [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) 为唯一来源。研究产物的人工验收仍在进行中，见 [Issue #15](https://github.com/xianxianjianjian/Literature-Evaluation-Skills/issues/15)。
>
> 持续验证：
> - Python 3.11 / 3.12 CI
> - Windows 宋体（SimSun）生产门禁
> - 全流程回归测试

## 项目简介

本项目不是简单的“论文摘要生成器”，而是一套强调**证据可追溯**的文献研究流程：

- 每条结论都能追溯到原文出处（Source Anchor）。
- 严格区分“原文直接内容 / 作者解释 / 评译者分析 / 外部依据”。
- 正文（Main）与补充材料（Supporting Information, SI）统一处理。
- 翻译、方法、结果、讨论各有明确的质量规则与独立校验器。
- 学术完成与 Zotero 归档完成分开判定，归档不可用时不阻塞学术工作。

## 四个 Skill 的分工

```text
weekly-literature-evaluation（总控）
        |
        |-- literature-search（文献检索）
        |-- paper-translation（论文翻译）
        `-- paper-deep-reading（深度精读）
```

| Skill | 职责 |
| --- | --- |
| `weekly-literature-evaluation` | 工作流路由、两个固定人工确认环节（选题、选定论文）、状态管理与断点续作 |
| `literature-search` | 选题规划、期刊映射、检索与两轮筛选、完整性核查、来源包交接 |
| `paper-translation` | 来源核验、术语库查询、全文翻译与 A 镜像 PDF 生成 |
| `paper-deep-reading` | 研究审计、方法与结果重建、批判性评价，产出 B 与 C |

## 快速开始

安装插件包后，调用对应的 Skill 入口即可：

- `literature-evaluation:weekly-literature-evaluation`
- `literature-evaluation:literature-search`
- `literature-evaluation:paper-translation`
- `literature-evaluation:paper-deep-reading`

本地构建、校验与安装推荐使用一体化脚本：

```powershell
py -3.11 scripts/deploy_local_plugin.py --deployments-dir <部署目录> --create-archive
```

详细说明见：

- [本地插件更新与部署](docs/local-plugin-updates.md)
- [架构说明](docs/architecture.md)
- [工作流规范](docs/workflow-spec.md)

研究数据（阅读历史、术语库、周评译等）保存在独立的数据根目录（`.literature-evaluation`）中，不随插件包分发；插件仓库只保留空白工作区模板与脱敏测试夹具。

## 交付物（A / B / C）

| 交付物 | 内容 |
| --- | --- |
| **A** | 中文全文精确镜像 PDF：保持原文版式，中文文字层可选中、复制与检索 |
| **B** | 完整的 DOCX 研究笔记，以及经独立渲染与视觉核查的 PDF 阅读副本 |
| **C** | 800–1000 字的中文周评译，正文事实以 Main 可见内容为准，并附私有来源映射 |

## 质量与校验

- **FULL_MIRROR / EXACT_TEXT_FRAME**：默认逐页一一对应、宋体嵌入、字号不低于原文 95%，校验器独立于生成器。
- **Main / SI 来源包管理**：缺失必要 SI 时明确标记，不以省略方式“通过”。
- **SHA-256 内容绑定**：B 的 DOCX → 渲染 PDF → 视觉核查 → Zotero 附件全链条绑定。
- **Zotero 附件命名 v2**：`Main Article / Support Information / A-Translation / B-DeepReading`，旧命名 v1 继续可读。
- **跨论文心理学术语库**：按领域、子领域与语境匹配，记录使用次数与修订历史。
- **段落角色排版**：中文正文两端对齐、首行缩进 2 字符；英文与参考文献遵循 APA 风格；精确镜像下不破坏原文几何。

历史版本的兼容规则见 [历史兼容说明](docs/legacy-compatibility.md)。

## 版本历史

### v1.6.0

- 研究记录（`knowledge/`、`weekly_reviews/`）迁出到独立的研究 Git 仓库，插件仓库只保留空白模板与脱敏夹具。
- 新增插件图标，并强制 `plugin.json`、`README.md`、`docs/architecture.md` 三处版本号一致。
- 精简四个 `SKILL.md` 中重复的状态与 SI 说明，历史兼容规则集中到 [`docs/legacy-compatibility.md`](docs/legacy-compatibility.md)。
- `scripts/` 包化，拆分千行级脚本，所有命令行入口保持兼容。
- 新增 `scripts/deploy_local_plugin.py`，一键完成构建、校验、缓存安装与 `workspace.json` 更新。
- 详见 [v1.6.0 发布说明](docs/releases/v1.6.0.md)。

### v1.5.1

- 记录私有的论文平台状态证据，生成七列文献总览。
- 合并阅读型 SI，核验来源与页码覆盖，媒体附件稳定编号。
- 统一 Zotero 附件显示名称，同时保留旧契约的读取能力。
- 详见 [v1.5.1 发布说明](docs/releases/v1.5.1.md)。

### v1.5.0（软件发布；人工验收仍有已知待办）

- A 使用可选中、可检索的中文 PDF 文字层，并拒绝残留的英文旧文字层。
- 经校验的 B 渲染结果转为 PDF 用于 Zotero 归档。
- C 采用 800–1000 字提交规范，事实以 Main 可见内容为准，局限以作者承认为准。
- 规范 Zotero 附件显示标题，保留原始文件名与数据型 SI。
- 心理学术语按语境跨论文复用，记录使用与修订历史。
- 中文正文排版与英文、参考文献的 APA 风格分开处理，不削弱精确镜像几何约束。

### 更早版本

- **v1.4.2**：强化翻译镜像校验，改进 CI 与 Windows 字体测试，补充工作流文档与归档规则。
- **v1.3.0**：引入证据加固的精确镜像工作流。
- **v1.1.0**：引入插件打包架构。

## 相关文档

- [文献状态刷新、历史导入与 SI 合并](docs/paper-status-and-si.md)（新归档采用 `naming_version=2`，旧命名契约继续读取）
- [研究产物人工验收跟踪（Issue #15）](https://github.com/xianxianjianjian/Literature-Evaluation-Skills/issues/15)
- 更多规范文档见 [`docs/`](docs/) 目录。
