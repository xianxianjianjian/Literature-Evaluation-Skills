# 2026-W36 归档记录

## Zotero

- 父条目：`89TU6WAS`
- 所属分类：`SLEEPY`（集合键 `CXGQF4XF`；已由写入响应验证）
- DOI：`10.1038/s42003-025-07868-5`
- 父条目状态：已创建并通过本地 API 按 DOI 唯一查回。
- 附件状态：待上传；API 查回 `numChildren = 0`，因此不得标记为已归档。
- 待上传附件：
  - `[ORIGINAL] Main Article` → `sources/SRC-M1_Version-of-Record.pdf`
  - `[SUPPLEMENT] Supplementary Materials` → `sources/SRC-S1_Supplementary-Materials.pdf`
  - `[A] 中文全文翻译·结构镜像版` → `handoff/[A] 中文全文翻译·结构镜像版_Yuksel_2025.pdf`
  - `[B] 文献研究笔记·完整精读版` → `handoff/[B] 文献研究笔记·完整精读版_Yuksel_2025.docx`
- 自动附件阻塞：当前 Zotero 9.0.6 未暴露文献插件要求的 Zotero 10+ 本地附件写入身份；Connector 接受父条目写入，但没有持久化 localhost 附件 URL。网页端状态绑定连续超时，未执行无法验证的上传。

## Git / GitHub

- 运行时数据目录本身不是 Git 工作树；项目树内找到并确认记录仓库：`Literature-Evaluation-Skills`。
- 远程：`https://github.com/xianxianjianjian/Literature-Evaluation-Skills.git`；分支：`main`。
- W36 首次同步提交：`38e3509`，已于 2026-09-06 推送到 `origin/main`。
- Git 仅保存 knowledge、主题/检索决策、C、流程与归档状态；原文、A、B 按仓库规则不提交。

## 流程纠正

- 现有 A 为 `STRUCTURAL_MIRROR_READABLE_EXTENSION`，并非默认要求的 `EXACT_TEXT_FRAME`。
- 未找到用户明确选择 `STRUCTURAL_MIRROR` 的记录，因此 Translation 与 A 已改为 `PROVISIONAL / needs_update`；现有文件保留作可用版本与溯源，不冒充精确镜像版。
