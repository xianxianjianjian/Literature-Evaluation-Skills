# 2026-W36 归档记录

## Zotero

- 当前父条目：`BHX9LWRZ`（旧父条目 `89TU6WAS` 已由用户删除）
- 所属分类：`SLEEPY`（集合键 `CXGQF4XF`；已由写入响应验证）
- DOI：`10.1038/s42003-025-07868-5`
- 父条目状态：2026-09-06 通过 Zotero Connector 的 PDF-first `saveStandaloneAttachment` 路径导入 Main PDF，Zotero 自动识别并生成父条目；本地 API 按 DOI 唯一查回，题名、年份与 SLEEPY 集合均核验通过。
- 当前原文附件：`NQSZH9AA`；已作为 Zotero 存储型 PDF 挂到父条目。Zotero 存储副本 SHA-256 `A88A59EB07264BE72661C9DD49314CE059AA3F60F1A4D88864058F8FD2711FE5` 与 `SRC-M1` 完全一致。
- 当前 A 附件：`C3YDZ6JF`；标题为 `[A] 中文全文翻译·精确镜像版 v1.4.0`，已作为 Zotero 存储型 PDF 挂到同一父条目。Zotero 存储副本 SHA-256 `A878CB0CB0DF262A44C569311860761352E42BA7AC797CACBAB5B9A479CB65EE`、MD5 `21D5EBBFB12D77A8F15564D001E01818`、长度 `3224624` 字节均与本地 A 完全一致。
- 附件状态：Main、A 已完成；SI、B 尚待上传，因此完整 Zotero 归档仍未闭合。
- 待上传附件：
  - `[SUPPLEMENT] Supplementary Materials` → `sources/SRC-S1_Supplementary-Materials.pdf`
  - `[B] 文献研究笔记·完整精读版` → `handoff/[B] 文献研究笔记·完整精读版_Yuksel_2025.docx`
- 2026-09-06 重新入库时 Zotero Desktop Local API 与 Connector 均可用。旧父条目已删除，SRC-M1 由 Connector 作为独立 PDF 导入，自动识别生成新父条目 `BHX9LWRZ` 和 Main 子附件 `NQSZH9AA`；1.4.0 `ingest-pdf` 复核状态为 `VERIFIED`。
- 2026-09-06 Zotero 已升级至 10.0.1；用户允许 `Literature Evaluation Skills` 本地写入后，1.4.0 `attach` 将 A 挂到父条目 `BHX9LWRZ`，生成附件 `C3YDZ6JF`，随后返回 `ALREADY_ATTACHED_AND_VERIFIED`。Zotero 上传接口将文件名空格规范化为字面 `+`，不影响附件标题或文件内容，双哈希核验一致。
- 用户确认的后续规则：新焦点论文优先将 Main PDF 导入目标分类并由 Zotero 自动识别父条目；不得把元数据-only 父条目作为常规完成路径。

## Git / GitHub

- 运行时数据目录本身不是 Git 工作树；项目树内找到并确认记录仓库：`Literature-Evaluation-Skills`。
- 远程：`https://github.com/xianxianjianjian/Literature-Evaluation-Skills.git`；分支：`main`。
- W36 首次同步提交：`38e3509`，已于 2026-09-06 推送到 `origin/main`。
- Git 仅保存 knowledge、主题/检索决策、C、流程与归档状态；原文、A、B 按仓库规则不提交。

## A 文件 v1.4.0 重建

- 2026-09-06 已用 literature-evaluation v1.4.0 重建 A：`FULL_MIRROR / EXACT_TEXT_FRAME`，主文 10 页与科学补充材料 11 页保持 1:1 页序。
- 语言权威为出版社 JATS（主文）及出版社可选文本补充 PDF；几何权威为 VOR PDF 与出版社补充 PDF。
- 独立验证通过 27/27 项：数值/统计量、图注清单、术语证据、页面几何、宋体嵌入、95% 字号下限、文本框归属与非文本像素均通过；21 页视觉检查通过。
- 旧结构镜像 A 保留作溯源，不覆盖；Git 仓库仍只记录状态，不提交 PDF 本体。新版 A 已作为附件 `C3YDZ6JF` 挂到当前父条目。
- v1.4 独立 B 验收发现当前 DOCX 不符合固定中文 0–10 标题结构，且缺少 `b_visual_qa.json` 与可核验的独立 office-render 来源，因此 Deep Reading/B 同步改为 `PROVISIONAL / needs_update`。既有完成历史通过 `HISTCOR-0001` 标记纠正。
- 术语纠错：原 `cluster-based permutation test` / TERM-0013 已弃用并解除 TERMEV-0005 关联；按原文方法改为 `FDR-corrected time-frequency cluster identification` / TERM-0016。
