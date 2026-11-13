# 文献状态与附件归档

在插件根目录执行，`$data` 必须是研究数据根（含 workspace.json），不是插件目录：

```powershell
$data = 'D:/codex/workplace/reference/.literature-evaluation'
py -3.11 scripts/build_paper_status_overview.py --workspace-root $data --paper-id <paper_id> --refresh
py -3.11 scripts/build_paper_status_overview.py --workspace-root $data --refresh
py -3.11 scripts/build_paper_status_overview.py --workspace-root $data --rebuild-only
py -3.11 scripts/build_paper_status_overview.py --workspace-root $data --import-history <baseline.md> --identity-map <identity-map.json>
# 预览核对身份后添加 --apply；重复执行不增加行数
py -3.11 scripts/build_paper_status_overview.py --workspace-root $data --import-history <baseline.md> --identity-map <identity-map.json> --apply
py -3.11 scripts/prepare_si_bundle.py --workspace-root $data --sources <source_cross_reference.json> --output "$data/work/<paper_id>/handoff/Support_Information.pdf"
py -3.11 scripts/zotero_bridge.py normalize-titles --parent-key <parent> --spec <migration.json> --report <migration-report.json>
# 已授权改名才添加 --yes；真实删除/覆盖/批量清理另行授权
py -3.11 scripts/zotero_bridge.py verify-archive --parent-key <parent> --spec <archive-spec.json> --workspace-root $data --report <archive-report.json>
```

新论文：`--record record.json` 写持久 intake；record 至少含 paper_id，建议含规范 DOI、完整 title、week（未归周 null）、outputs.A/B/C 的数据根相对路径。周工作流继续保留原 manifest。归周后同 paper_id 合并一行；多个真实周评用 status_current 明确当前版本。identity-map 为简称到 `{paper_id,doi,title,week}` 的显式映射；缺映射保留待认领身份，不猜年份。历史 Markdown 七列表原文保存在研究区，不进入公开测试或插件包。

私有配置 `knowledge/paper_status_config.json`：

```json
{"research_git_root":"<research Git root>","remote_url":"<confirmed remote>","remote_branch":"<confirmed branch>","zotero":{"library_prefix":"users/0","collection_key":"<target>"},"web":{"source_url":"<confirmed author publication list>","charset":"gb18030"}}
```

复用 workspace.json 的 data-root 与 research_git_root；显式配置覆盖平台目标。GitHub 用临时 bare repository 实时 fetch 目标分支，比对 C 字节，支持提交 SHA 不同但内容相同；目标/访问失败标 UNKNOWN，保留上次结果。不推送。网页适配当前 ASP 作者清单，确认 DOI 后仅比较评论正文，忽略格式；摘要/书目尚未逐字段比对时保持 PRESENT_UNVERIFIED。完整枚举才能判定此清单未发布，不能代表全站。不同实际发布时间条目才报告重复。manual_edit_notes 保留人工润色说明。其他网站需提供适配器或经核对的报告，不猜发布状态。

每篇平台 observations 在 manifest 或 intake 的 platform_status；网页/Zotero 原始回查报告在 knowledge/status_reports。`knowledge/paper_status_overview.md/.csv` 七列重建产物含待处理摘要，默认私有。平台 UNKNOWN 表示本次待核验，last_observation 保存上次结论与日期。本地文件只有通过内容绑定 QC 才显示已验证；其他可读文件作为草稿报告。阅读历史不由状态汇总写入。

SI 来源沿用 sources 数组的 source_id/source_type/local_path/required。可用 `si_kind: READING|VIDEO|DATA` 和 publisher_order；无 publisher_order 沿用固定记录顺序。DOC/DOCX 复用 LibreOffice，转换报告必须有 passed、pdf_sha256、all_pages_visual_reviewed，并由 conversion_qc_report 引用；缺 QC 保留可恢复 si_conversion_pending 与 pending_zotero_actions，不误报成功。成功后只保留最终 PDF、来源与 si_bundle_manifest.json。后者记录原指纹、转换 QC、页区间、书签、合并 SHA/字节/页数、媒体稳定编号。新 SI 必须重新执行 source-change 流程。

新归档规格 naming_version=2；学术 contract_version 保持 1.5.0。沿用 paper_id、workflow_id、source_fingerprints、collection_key，增加 library_prefix。attachments 每行沿用 role/key/mime/local_path/local（sha256,size_bytes）。阅读 SI 一行携带多个 source_ids 和 si_bundle_manifest（数据根相对路径）；required_si_source_ids 必须全部覆盖。VIDEO/DATA 使用真实 MIME 与 si_number。没有 naming_version 的旧规格按旧命名契约验证。

attach-role A/B 必须提供 --qc-report，内容绑定到最终 PDF；A 使用新 translation report 的 pdf_binding，B 使用现有 export_b_pdf 的 pdf_binding。B 完整 DOCX 在本地保留。迁移 preview 要求每行明确附件 key、local_path 和 sha256，并校验 Zotero MD5；旧 Word 保留，先导出验证 PDF。normalize-titles 使用版本条件 PATCH 保留附件身份，--report 保存旧名称、附件键、旧/新版本与部分进度；重试重新预览，冲突不覆盖。回滚按报告逐键核对当前版本后恢复旧标题；不恢复/删除研究原始来源。

Windows 验收：先运行 `scripts/run_contract_tests.py --discover --allow-skips`，再运行 `--mandatory-simsun tests.test_v150_release_hardening`；构建/包验证沿用 local-plugin-updates.md。独立构建安装后必须开新任务检查四个入口的实际加载路径，再刷新测试 intake 和 SI fixture。当前聊天不能代替新任务加载验收。保留此前已验证 marketplace 路径，恢复时重新注册旧路径并安装。开发包与正式发布分开报告；不创建新 tag 即不宣称正式发布。
