# Search Record

- Week: 2026-W36
- Search status: COMPLETE
- Search completed: 2026-09-05 20:49 +08:00
- Confirmed topic: NREM 慢振荡—纺锤波耦合与 REM 指标如何共同预测情绪记忆的隔夜巩固
- Review type: targeted weekly search；不是系统综述或 PRISMA 流程

## Search Question Profile

- Population: 健康成人；优先年轻成人；临床样本、儿童/青少年和老年样本仅作边界线索，不竞争焦点论文。
- Exposure/intervention: 正常睡眠、日间小睡、睡眠期 TMR、睡眠期刺激或药理操纵。
- Sleep measures: PSG/EEG 睡眠分期；NREM 慢振荡、纺锤波及其耦合；REM 时长、比例、连续性或 theta；可辅以 fMRI、心率或瞳孔。
- Outcomes: 隔夜情绪记忆准确性/误差、细节保持、负性偏向、侵入性记忆或记忆相关情感反应。
- Preferred architecture: 睡前编码—客观睡眠记录—睡后测验；优先随机、被试内、TMR/刺激或阶段序列分析。
- Time: 重点 2024-01-01 至 2026-09-05；2021-2023 仅保留直接机制或方法锚点；更早文献仅承担理论奠基角色。
- Focal-use requirements: 同行评议的原始人类研究、可确认 DOI/版本、主文全文可合法获得；SI 可得性计入完整度。

## Journal map

Checked 2026-09-05. Core journals: `Sleep`, `Journal of Sleep Research`, `Neurobiology of Learning and Memory`, `Learning & Memory`, `Sleep Medicine Reviews`（仅背景综述）。Recommended journals: `Communications Biology`, `Translational Psychiatry`, `eNeuro`/`Journal of Neuroscience`, `NeuroImage`/`Imaging Neuroscience`。映射用于定向补检，不作为排除其他可靠期刊的白名单。

## Concept blocks

- B1 Emotion/memory: `emotional memory`, `negative memory`, `affective memory`, `intrusive memories`, `analogue trauma`.
- B2 Sleep stage: `sleep`, `NREM`, `slow wave sleep`, `REM`, `sleep cycle`.
- B3 Microstructure: `slow oscillation`, `spindle`, `SO-spindle coupling`, `theta`, `phase coupling`.
- B4 Method: `EEG`, `polysomnography`, `fMRI`, `targeted memory reactivation`, `tACS`.
- B5 Population: `healthy adults`, `young adults`, `good sleepers`.

## Search routes and yield

### PubMed / NCBI E-utilities

Searched 2026-09-05, latest route check 20:49 +08:00.

| Route | Exact query | Hits | Use |
| --- | --- | ---: | --- |
| P1 | `((emotional memory[Title/Abstract]) OR (emotional memories[Title/Abstract])) AND sleep[Title/Abstract] AND (spindle*[Title/Abstract] OR slow oscillation*[Title/Abstract] OR slow wave*[Title/Abstract]) AND (2024/01/01[Date - Publication] : 2026/12/31[Date - Publication])` | 15 | NREM 微结构主检索 |
| P2 | `((emotional memory[Title/Abstract]) OR (emotional memories[Title/Abstract])) AND sleep[Title/Abstract] AND (REM[Title/Abstract] OR NREM[Title/Abstract]) AND (EEG[Title/Abstract] OR polysomnography[Title/Abstract]) AND (2024/01/01[Date - Publication] : 2026/12/31[Date - Publication])` | 13 | 睡眠阶段 + 客观记录 |
| P3 | `((emotional memory[Title/Abstract]) OR (emotional memories[Title/Abstract])) AND sleep[Title/Abstract] AND (EEG[Title/Abstract] OR polysomnography[Title/Abstract] OR fMRI[Title/Abstract]) AND (2021/01/01[Date - Publication] : 2026/12/31[Date - Publication])` | 25 | 近五年方法与奠基补检 |
| P4 | `((emotional memory[Title/Abstract]) OR (emotional memories[Title/Abstract])) AND sleep[Title/Abstract] AND (healthy adults[Title/Abstract] OR young adults[Title/Abstract]) AND (2024/01/01[Date - Publication] : 2026/12/31[Date - Publication])` | 7 | 健康成人精确补检 |

### Europe PMC

- Query: `"emotional memory" AND sleep AND (spindle OR "slow oscillation" OR REM) AND FIRST_PDATE:[2024-01-01 TO 2026-12-31]`
- Hits: 198；检查前 50 条及全文状态。
- Incremental yield: 发现 1 篇初始 PubMed 题名检索易漏的合格研究：Azza et al. (2026)，其主要结局写作 `intrusive memories`；同时发现 1 篇 2026 REM-theta 相位锁定 TMR 预印本，按 `EX-10` 不进入焦点竞争。

### Crossref

- Query route: bibliographic query `emotional memory sleep spindle REM NREM`；过滤 2024-01-01 至 2026-12-31、journal article。
- Reported hits: 148,095；该自由文本路由噪声很高，检查排序前 30 条。
- Use: DOI、Version of Record、许可与 update relation 回查。未增加新的合格焦点研究；发现的 Sleep Medicine 相关记录属于 World Sleep 2025 摘要集，按 `EX-07` 处理。

### Journal/publisher and citation backfill

- 定向检查上述 core/recommended 期刊的出版社页面、PubMed related records、PMC 全文参考文献与文章补充材料。
- 增补直接机制/反证论文：Rodheim et al. (2023)、Denis et al. (2022)、Ng et al. (2025 meta-analysis)。
- 出版社页与 PMC 用于核对主文、SI、数据/代码声明和版本，不以搜索结果摘要替代全文判断。

### Sources not available

- 当前环境无法获得 Web of Science、Scopus、PsycINFO 的授权检索界面与可审计命中数。
- Google Scholar 未提供稳定、可复现的结果计数路由，因此未把其结果数写入记录。
- 影响：可能漏掉尚未被 PubMed/Europe PMC 收录的社会科学或会议记录；已用 Crossref、期刊定向检索及引用回溯降低该风险。

## Recency and saturation

- Current research: 2024-2026 原始研究。
- Recent support: 2021-2023 的直接情绪记忆—睡眠微结构研究。
- Foundational: 更早的 NREM 系统巩固、NREM–REM 序列与 REM 情感加工理论。
- Saturation decision: PubMed 四条互补式检索去重后，加上 Europe PMC、Crossref、出版社与引用回溯，共形成 30 条可审计的广筛记录。第二数据库只新增 1 篇合格原始研究；Crossref 排序前 30 条未新增合格焦点研究，新增信号主要为综述、临床/老年样本、方法论文、会议摘要或预印本。继续扩展已主要重复这些类别，足以进入周评的精筛与论文确认。

## Round 1 — broad screening (n = 30)

`INCLUDE` 进入精筛；`MAYBE` 保留为边界/背景；`EXCLUDE` 使用固定排除码。

| # | PMID | Year | Short title | Decision | Reason |
| ---: | --- | ---: | --- | --- | --- |
| 1 | 42267755 | 2026 | Sodium oxybate alters sleep architecture and emotional selectivity | INCLUDE | 健康成人、双盲交叉、PSG + fMRI/瞳孔；但行为记忆近天花板 |
| 2 | 41905254 | 2026 | Stress and sleep: EEG to circuitry | EXCLUDE | EX-06：综述 |
| 3 | 41783613 | 2025 | Sleep and fear extinction in adolescents: protocol | EXCLUDE | EX-05：方案；且为青少年临床背景 |
| 4 | 41755328 | 2026 | Automated phasic/tonic REM detection | EXCLUDE | EX-01：方法检测，无情绪记忆结局 |
| 5 | 41432255 | 2026 | REM fragmentation and emotional habituation | MAYBE | REM 因果操纵有价值，但核心结局为情绪反应习惯化而非记忆巩固 |
| 6 | 41207483 | 2026 | REM/SWS spectra and internalizing symptoms | EXCLUDE | EX-04：结局侧重症状/一般记忆缺陷，不是情绪记忆巩固 |
| 7 | 41127676 | 2025 | Instruction, emotional salience and sleep physiology | INCLUDE | 健康青年、睡眠 EEG 与记忆；需核查小 EEG 样本和统计一致性 |
| 8 | 41089190 | 2025 | Disarming emotional memories with REM TMR | INCLUDE | 健康成人、REM TMR + fMRI/心率；偏情感消退而非记忆准确性 |
| 9 | 40937197 | 2025 | Dreams of remote emotional memory | EXCLUDE | EX-04：梦内容为主，非隔夜巩固结局 |
| 10 | 40888367 | 2025 | Emotional memory dissipation in insomnia | EXCLUDE | EX-02：失眠障碍样本 |
| 11 | 40442306 | 2025 | MTL networks and emotional memory in older adults | EXCLUDE | EX-02：老年样本 |
| 12 | 40136846 | 2025 | iRBD and overnight emotional habituation | EXCLUDE | EX-02：临床神经退行性风险样本 |
| 13 | 40129180 | 2025 | NREM oscillations, anxiety and negative affect | INCLUDE | 健康青年小睡 PSG；情绪/焦虑变化明确，记忆关联为阴性 |
| 14 | 39738288 | 2024 | Physical activity and overnight memory in older adults | EXCLUDE | EX-02：老年样本；且非情绪记忆主问题 |
| 15 | 39695124 | 2024 | Sleep TMR after imagery rescripting | INCLUDE | 睡眠 TMR 与情绪记忆调节；更贴近后备 TOPIC-03 |
| 16 | 38328085 | 2024 | REM hypoxemia and MTL in older adults | EXCLUDE | EX-02：老年/低氧背景；预印本版本 |
| 17 | 37614274 | 2023 | Sleep patterns and memory retention | EXCLUDE | EX-06：系统综述 |
| 18 | 37485816 | 2024 | Sleep and intellectual abilities | EXCLUDE | EX-01：无情绪记忆焦点 |
| 19 | 36584677 | 2023 | Updating unwanted emotions during sleep | MAYBE | 因果 TMR 重要但超出优先两年，且更贴近 TOPIC-03 |
| 20 | 35578403 | 2023 | Sleep continuity disruption and emotion regulation | EXCLUDE | EX-04：情绪加工/调节结局，无记忆巩固主结局 |
| 21 | 35331867 | 2022 | SWS emotional cueing and next-day OFC/amygdala | MAYBE | fMRI/TMR 方法锚点；超出近期窗口 |
| 22 | 35253902 | 2022 | Sleep and valenced story/image memory | MAYBE | 行为锚点；无睡眠微结构 |
| 23 | 34153105 | 2021 | Short-term preservation and long-term affect depotentiation | MAYBE | 行为 + 提取 EEG 理论锚点；无睡眠 PSG |
| 24 | 33511691 | 2022 | SO-spindle coupling after stress | INCLUDE | 直接耦合反证/边界；较旧但健康成人 PSG |
| 25 | 33166026 | 2021 | Wi-Fi exposure and sleep-dependent memory | EXCLUDE | EX-01：无情绪记忆焦点 |
| 26 | 41702880 | 2026 | Spindles/theta predict fewer analogue-trauma intrusions | INCLUDE | 健康成人被试内高密度 EEG；NREM spindle + REM theta |
| 27 | 40123003 | 2025 | SWS and REM jointly contribute to emotional memory | INCLUDE | 健康成人 TMR、57 通道 EEG、跨阶段指标与开放数据 |
| 28 | 39397004 | 2024 | Temporal dynamics of negative emotional-memory reprocessing | INCLUDE | 整夜 PSG、睡眠周期、SO-spindle coupling、tACS |
| 29 | 38769012 | 2024 | NREM TMR enhances neutral but not negative components | INCLUDE | 健康成人 PSG/TMR；关键阴性结果界定边界 |
| 30 | 40066370 | 2025 | REM vagal HRV and negative-memory bias | MAYBE | REM 生理与记忆偏向相关，但缺少核心耦合指标 |

## Round 2 — detailed screening (n = 9)

Ratings are 0–5. Total uses the fixed weights: relevance 25, evidence 20, journal/source 15, method transfer 15, current-research transfer 10, novelty 10, full text/SI 5.

| Rank | Paper | Gate | Rel. | Evidence | Journal | Method | Transfer | Novelty | Full/SI | Total |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Yuksel et al., 2025, Commun Biol | AMBER | 4.8 | 4.1 | 4.5 | 4.7 | 4.8 | 4.8 | 5.0 | 92.2 |
| 2 | Tabarak et al., 2024, Transl Psychiatry | AMBER | 5.0 | 3.2 | 4.4 | 4.6 | 4.7 | 5.0 | 4.5 | 88.7 |
| 3 | Azza et al., 2026, Transl Psychiatry | AMBER | 4.7 | 3.2 | 4.4 | 4.7 | 4.5 | 4.9 | 5.0 | 87.4 |
| 4 | Colin et al., 2026, J Sleep Res | AMBER | 4.2 | 3.7 | 4.5 | 4.9 | 4.5 | 5.0 | 4.0 | 87.0 |
| 5 | Denis & Payne, 2024, eNeuro | GREEN | 4.4 | 4.0 | 4.2 | 4.5 | 4.5 | 4.4 | 5.0 | 86.9 |
| 6 | Bai et al., 2024, Transl Psychiatry | AMBER | 4.1 | 3.9 | 4.4 | 4.6 | 4.3 | 4.6 | 4.8 | 85.7 |
| 7 | Arpaci et al., 2025, J Sleep Res | AMBER | 4.1 | 3.8 | 4.3 | 4.5 | 4.1 | 4.4 | 5.0 | 84.1 |
| 8 | Greco et al., 2025, Imaging Neurosci | AMBER | 3.9 | 3.3 | 4.2 | 4.8 | 4.5 | 4.8 | 5.0 | 83.3 |
| 9 | Kurdziel et al., 2025, Front Behav Neurosci | RED | 4.0 | 2.0 | 3.2 | 3.0 | 3.8 | 4.0 | 5.0 | 67.2 |

### Screening judgments behind the scores

- Yuksel: n=123 usable participants across five nap/wake groups；57-channel EEG；item-level TMR and mixed models；公开 SI、行为/EEG 数据和代码。关键限制是组间设计、未完成 neutral-REM group、REM 组入组依赖获得足够稳定 REM，以及若干跨阶段结果属于交互/相关分析。
- Tabarak: Experiment 1 n=40 整夜 PSG、约五个睡眠周期；Experiment 2 n=21 被试内 tACS/sham。与 SO-spindle coupling 最直接，但用大量睡眠特征的小样本 LOOCV 分类把“条件可分类”解释为“记忆再加工”较间接；第二实验功效计算采用 alpha=.10；部分相关未校正。
- Azza: 22 名健康女性，随机条件顺序的被试内创伤/中性影片，三晚 64-channel hdEEG；NREM spindle 与 REM theta 同时进入情绪记忆框架。主要结果为单侧、相关性 cluster tests；平均睡眠指标并未因创伤条件显著改变；侵入性记忆只在创伤条件记录，不能把相关写成因果保护机制。
- Colin: 19 名健康青年男性、双盲随机交叉 sodium oxybate/placebo、PSG + 次日 fMRI/瞳孔。药理操纵和多模态价值高，但行为识别约 96% 天花板、无记忆差异，有限 EEG 导联不能分析 SO-spindle coupling。
- Denis & Payne: TMR 组 n=31、无 TMR 对照 n=32，整夜 PSG；spindle response 预测 neutral cueing benefit，negative component 和内源 coupling/REM theta 多为阴性。设计与报告可用，因此 Gate 为 GREEN；但它是关键反证而非最能回答 NREM–REM 协同的主论文。
- Bai: imagery rescripting + sleep TMR 的因果设计有价值，但问题更接近后备 TOPIC-03，且不能完整覆盖 NREM coupling 与 REM 指标。
- Arpaci: n=42 健康非临床青年、2-hour nap PSG；NREM oscillation 与焦虑/负性情绪变化相关，但记忆组差异及睡眠—记忆关联为阴性，未直接分析 SO-spindle coupling。
- Greco: REM TMR、fMRI 与心率给出情感消退网络证据；最终 n=18（10-day follow-up n=15），且更偏“情感色彩”而非记忆准确性。
- Kurdziel: in-lab 行为样本 n=53，但可用睡眠 EEG 仅 n=15；全文报告 `r=.150, p=.041` 的相关组合与该样本量下普通双变量相关不相容，且有多重探索相关。该核心报告缺口使其 Gate 为 RED，不用于主结论。

## Final recommendation set

### Three-candidate expanded comparison

#### Journal source notes

- **Communications Biology**（Yuksel et al., 2025）是 Nature Portfolio 旗下的全开放获取综合生物学期刊，覆盖基础与生物医学科学，由专业编辑与学术编委共同处理稿件；强调对具体生物学分支具有新见解且证据技术上可靠的研究。期刊实行同行评议，并对2019年以来的研究论文采用透明同行评议。官方2025 Journal Impact Factor 为5.8、5-year JIF为6.3。它不是 `Nature` 或 `Nature Communications`，不能把 Nature Portfolio 品牌直接当作单篇论文质量保证。对本次候选而言，优势是论文附有 reporting summary、补充数据、审稿意见/回复以及开放数据和代码。
- **Translational Psychiatry**（Tabarak et al., 2024；Azza et al., 2026）同属 Nature Portfolio，是全开放获取的转化精神病学期刊，定位在神经科学机制与精神障碍诊断、预防、治疗之间的连接，接收机制性人类研究、临床研究、神经影像及具有明确精神医学转化意义的相关工作。官方2025 Journal Impact Factor 为7.5、5-year JIF为7.8，并被 PubMed/MEDLINE、PubMed Central、Scopus 和 Web of Science 收录。该定位解释了两篇论文为何强调焦虑/PTSD或潜在干预，但“具有转化意义”不等于已经证明临床疗效：Tabarak与Azza均为健康成人实验，外推到患者仍需独立证据。
- **对本周选择的意义**：两本均为正规同行评议、可确认 Version of Record 的开放获取期刊，来源层面没有决定性短板。Tabarak与Azza来自同一本期刊，因此二者不能靠期刊声誉排序；真正区分三篇的仍是样本、设计、统计和结局与 TOPIC-01 的匹配程度。

#### Full titles

1. **Yuksel, Nall, & Denis (2025)**
   - Original: *Both slow wave and rapid eye movement sleep contribute to emotional memory consolidation*
   - Chinese: **慢波睡眠与快速眼动睡眠均参与情绪记忆巩固**
   - Question actually tested: 在 SWS 或 REM 中重新呈现与图片—位置记忆绑定的声音线索，会怎样改变空间位置记忆；SWS 与 REM 的睡眠量是否共同解释 TMR 获益？
2. **Tabarak et al. (2024)**
   - Original: *Temporal dynamics of negative emotional memory reprocessing during sleep*
   - Chinese: **睡眠中负性情绪记忆再加工的时间动态**
   - Question actually tested: 负性与中性材料编码后的睡眠 EEG/EOG 特征能否定位“再加工”最强的睡眠周期；第二周期 SO–spindle coupling 是否关联并可能支持次日及两年后的识别？
3. **Azza et al. (2026)**
   - Original: *Sleep to remember, sleep to protect: increased sleep spindle and theta activity predict fewer intrusive memories after analogue trauma*
   - Chinese: **睡眠以记忆、睡眠以保护：增强的睡眠纺锤波与 θ 活动预测模拟创伤后更少的侵入性记忆**
   - Question actually tested: 同一健康个体在模拟创伤夜相对中性夜出现的 NREM spindle、SWA 与 REM theta 变化，是否预测未来六天的侵入性记忆和一周后的负性情感？

#### Design and evidence comparison

| Dimension | Yuksel et al. (2025) | Tabarak et al. (2024) | Azza et al. (2026) |
| --- | --- | --- | --- |
| Core construct | 阶段定向 TMR；SWS–REM 互补 | 睡眠周期时窗；SO–spindle coupling | NREM spindle 与 REM theta 的个体内变化 |
| Population | 123 名健康青年，21.6±2.7 岁，63.9% 女性 | 实验1 n=40，22.05±1.41 岁、8 女性；实验2 n=21，19.27±1.09 岁、10 女性 | 22 名健康女性，23.14±2.46 岁 |
| Architecture | 五组组间设计：E-SWS n=24、E-REM n=25、N-SWS n=31、E-Nap n=22、E-Wake n=20 | 两个平衡交叉实验；实验1 负性夜/中性夜，实验2 active/sham tACS 夜 | 三晚实验室设计：适应夜 + 随机顺序的创伤影片夜/中性影片夜，测试夜间隔至少一周 |
| Sleep opportunity | 2-hour daytime nap | 整夜睡眠；约五个睡眠周期 | 整夜睡眠 |
| Memory material | 50 个带声音的情绪或中性图片—网格位置配对 | 负性/中性图片；80 个旧图 + 60 个新 foil 的识别 | 12 分钟模拟创伤/中性影片；不是标准图片识别任务 |
| Manipulation | 睡眠期向一半项目重放声音；阶段为 SWS 或 REM | 实验1无睡眠操纵；实验2在第二周期 N2/SWS 施加 60-Hz cross-hemispheric tACS 或 sham | 操纵睡前影片类型，不直接操纵睡眠振荡 |
| Recording | 57-channel EEG，400 Hz；睡眠分期与 cue-evoked time–frequency | 6-channel PSG EEG + 2 EOG；周期级 95 个 NREM、132 个 REM 特征 | 64-channel hdEEG + EOG/EMG/ECG，500 Hz；AASM 人工分期 |
| Key sleep metrics | %SWS、%REM、SWS×REM product；cue-evoked delta/theta、spindle-band、alpha/beta | SO、spindle、SO–spindle coupling count/power、theta、SWA、EOG；分类器特征权重 | NREM SWA 0.5–4 Hz、spindle 12–16 Hz count/envelope；REM theta 4.25–8 Hz；头皮 cluster |
| Primary behavioral outcome | 图片空间位置误差变化 `%ΔError`；cueing benefit = 非提示项目变化 − 提示项目变化 | 次日与两年后负性/中性图片识别 d′；实验2比较 tACS/sham | 六日侵入性记忆总数；一周后提示诱发侵入和 PANAS 负性情感 |
| Strongest result | E-SWS 中 cueing benefit 与 SWS×REM product 强相关，rs=.66, p=.0004；情绪 SWS TMR 相对中性有更大获益，组×再激活 β=.39, p=.002 | 第二周期 SO–spindle count 与次日负性记忆相关，n=38, r=.46, Bonferroni-adjusted p<.008；tACS 降低 coupling，并相对 sham 降低负性识别 | 创伤夜相对中性夜增加的 REM theta 与更少侵入相关，ρ=−.62, q=.038；spindle count 与更少侵入相关，ρ=−.590, q=.025 |
| Important counter-result | REM cueing 反而增加位置误差（22% vs 11%）；SWS 组内 TMR 主效应不显著；spindle power 不预测 cueing benefit | REM 分类特征虽可区分条件，但 REM-specific spindle 未与记忆表现相关，REM 机制未被解释 | 创伤夜与中性夜的平均 SWA、spindle、REM theta 均无显著差异；SWA 不预测侵入或负性情感 |
| Correction/model | item-level LMM；FDR 与 Bonferroni；部分 REM 相关未通过校正 | ANOVA/MMRM、相关 Bonferroni α=.008、LOOCV + permutation；另有未校正相关 | cluster permutation；每个行为结局四项相关用 Storey FDR；相关均为单侧 |
| Source transparency | SI、Supplementary Data、Reporting Summary、peer review、OSF 数据与代码 | SI 可得；数据/代码仅可向作者申请 | SI 可得；行为数据与 MATLAB 代码公开，EEG/ECG 需申请 |
| Best use in this week | 回答 NREM–REM 是否共同参与；审查阶段互补与“记忆弱化”解释 | 回答 coupling 是否集中于特定睡眠周期；重点做方法/统计审计 | 回答 NREM spindle 与 REM theta 是否共同关联适应性情绪结局；强调生态性与构念边界 |

#### Comparison by the selected TOPIC-01

- **对“NREM–REM 共同作用”的匹配：Yuksel > Azza > Tabarak。** Yuksel 明确构造 `SWS×REM product` 并把 SWS/REM TMR 放进同一框架；Azza 同时测量 NREM spindle 与 REM theta，但没有正式检验二者交互或序列；Tabarak 检查同一睡眠周期的 NREM/REM 特征，但可解释的行为关系主要落在 NREM coupling。
- **对“SO–spindle coupling”的匹配：Tabarak > Yuksel > Azza。** Tabarak 直接检测 coupling count/power 并在第二周期做 tACS；Yuksel 只报告 cue-evoked spindle-band power，没有 SO–spindle coupling；Azza 只分析 SWA 与 spindle 的独立指标，没有耦合。
- **对“情绪记忆”的经典操作化：Tabarak > Yuksel > Azza。** Tabarak 使用负性/中性图片识别 d′；Yuksel 测量情绪图片的空间位置误差，可能混入“情绪核心内容保留、情境细节减弱”的 trade-off；Azza 测量侵入性记忆和负性情感，更接近创伤模拟与心理健康结局，但不是一般识别记忆。
- **对因果推断的支持：Yuksel ≈ Tabarak > Azza。** Yuksel 有项目内 cued/uncued TMR 对照，但睡眠阶段主要是组间；Tabarak 有 active/sham tACS 被试内操纵，但刺激不只改变 coupling；Azza 的影片条件顺序随机，关键睡眠—结局关系仍是相关。
- **样本与统计稳定性：Yuksel > Tabarak > Azza。** Yuksel 总样本最大，但每组仅 20–31 人且筛除 62/185；Tabarak 两实验分别 n=40、n=21，分类维度远多于样本；Azza n=22，只按先验中大效应做单侧检验。
- **全文翻译与 A/B/C 成品潜力：Yuksel > Tabarak > Azza。** Yuksel 结果结构最适合形成“阶段差异—跨阶段协同—时频响应—边界解释”的完整叙事；Tabarak 最适合做严厉的方法审计；Azza 最适合形成“记忆准确性与情绪适应结局不可混同”的专题评论。

#### Decision implications

- 若本周最想回答 **“SWS 与 REM 是否协同，而非二选一”**，选 Yuksel。
- 若最想回答 **“第二睡眠周期的 SO–spindle coupling 是否是关键机制/干预靶点”**，选 Tabarak，同时接受深读将花较多篇幅审计分类与 tACS 推断。
- 若最想回答 **“NREM spindle 与 REM theta 是否预测更少创伤样侵入和负性情感”**，选 Azza，同时把结论限定为小样本相关证据。

### Primary — Yuksel et al. (2025)

- Citation: Yuksel, C., Nall, W. A., & Denis, D. *Both slow wave and rapid eye movement sleep contribute to emotional memory consolidation*. Communications Biology, 8, 485.
- DOI: https://doi.org/10.1038/s42003-025-07868-5
- PMID/PMCID: 40123003 / PMC11930935
- Role: CURRENT_RESEARCH；本周首选焦点论文。
- Why worth reading: 在当前候选中，它用最大的健康成人样本、睡眠阶段定向 TMR、57-channel EEG 和 SWS×REM 跨阶段指标，最直接检验“不是 NREM 或 REM 二选一，而是阶段互补/序列作用”的核心命题。主要结果同时包含 REM cueing 的反直觉损害、SWS 情绪/中性差异及 SWS×REM product 关系，适合深读统计解释和构念边界。
- Main caveat: 不是把每名参与者随机接受 SWS 与 REM 的完整被试内比较；没有 neutral-REM group；跨阶段指标主要是相关/交互，不能直接证明序列机制。
- Sources: Version of Record、PMC 主文、SI PDF、Supplementary Data、Reporting Summary 与 transparent peer review 均可得；OSF 提供行为和 EEG time-frequency 数据及复现代码。
- Method transfer: `REUSABLE_WITH_MODIFICATION`。可复用项目级 cueing benefit、睡眠期时频反应和 mixed model；若迁移，应采用完整 factorial/被试内设计、预先定义跨阶段指标，并避免按是否出现稳定 REM 造成选择偏差。
- Current-research transfer: 可直接转化为“情绪价性 × TMR 阶段 × NREM/REM 序列指标”的实验和分析框架。
- Integrity summary: DOI、题名、期刊与 Version of Record 一致；Crossref 未列出 update/correction relation，PMC 标记 `is-retracted=no`；当前检查未发现明显撤稿、Expression of Concern 或版本冲突。此结论限于已检查的 Crossref、PubMed/PMC 与出版社来源。

### Strong Alternative 1 — Tabarak et al. (2024)

- Citation: Tabarak, S., et al. *Temporal dynamics of negative emotional memory reprocessing during sleep*. Translational Psychiatry, 14, 434.
- DOI: https://doi.org/10.1038/s41398-024-03146-w
- PMID/PMCID: 39397004 / PMC11471876
- Role: CURRENT_RESEARCH；最贴近“第二睡眠周期 SO-spindle coupling”字面问题的机制候选。
- Main strength: 整夜分周期 PSG 与第二睡眠周期 tACS/sham 实验把时窗、coupling 和记忆行为放在同一论文中。
- Main caveat: 小样本高维分类、LOOCV 缺乏独立验证、分类目标与“记忆再加工”并不等价；tACS 同时改变慢振荡，不能把效应唯一归因于 coupling；部分推断依赖未校正结果。
- Sources: Version of Record、PMC 主文和 SI DOCX 可得；数据与代码仅可向作者合理申请，未发现公开仓库或预注册。
- Method transfer: `REUSABLE_WITH_MODIFICATION`。睡眠周期切片和刺激时窗可借鉴；不建议直接复用“小样本高维分类 = replay”的解释链。
- Integrity summary: DOI/版本一致；Crossref 未列 update/correction relation，PMC 未标记撤稿；当前来源未发现明显更正、撤稿或 Expression of Concern。方法学风险已反映为 AMBER，而不是诚信定性。

### Strong Alternative 2 — Azza et al. (2026)

- Citation: Azza, Y., Kammerer, M. K., Ngo-Dehning, H.-V., et al. *Sleep to remember, sleep to protect: increased sleep spindle and theta activity predict fewer intrusive memories after analogue trauma*. Translational Psychiatry, 16, 147.
- DOI: https://doi.org/10.1038/s41398-026-03910-0
- PMID/PMCID: 41702880 / PMC12987997
- Role: CURRENT_RESEARCH；最新的 NREM spindle + REM theta 同篇证据。
- Main strength: 随机条件顺序、被试内创伤/中性夜、64-channel hdEEG，并用六日侵入记忆日记与一周负性情感结局提高生态性。
- Main caveat: n=22 且全为女性；主要分析为单侧相关，创伤夜相对中性夜的平均振荡变化并不显著；侵入记忆只在创伤条件测量，不能据此证明“振荡增强导致保护”。
- Sources: Version of Record、PMC 主文、SI 与图件可得；行为数据和 MATLAB 代码公开在 GitHub，EEG/ECG 需申请。
- Method transfer: `REUSABLE_WITH_MODIFICATION`。可复用被试内对照夜、hdEEG cluster permutation 与多日侵入日记；应增加双侧/稳健性分析、性别多样样本和直接记忆测验。
- Integrity summary: DOI/版本一致；Crossref 未列 update/correction relation；PMC/出版社当前未显示撤稿或 Expression of Concern。未发现预注册声明，透明度限制已记录。

## Why Primary ranks above the strongest alternative

Yuksel 高于 Tabarak，不是因为它更贴近所有关键词，而是因为它对本周核心中的“NREM–REM 共同贡献”给出更直接的阶段操纵、较大的总样本、项目级对照、开放数据/代码与更完整的补充材料。Tabarak 对 SO-spindle coupling 更精确，但其关键证据链包含小样本高维分类、间接 replay 解释和机制不专一的 tACS；这会把深读的重心从“检验阶段协同”推向“审计一条脆弱的机制主张”。因此 Yuksel 更适合作为本周综合成品的主轴，Tabarak 最适合作为机制性强、风险也更高的对照论文。

## Foundational and boundary sources

- Walker & van der Helm (2009), *Overnight therapy? The role of sleep in emotional brain processing* — REM 情感去强化理论锚点。
- Rasch & Born (2013), *About sleep's role in memory* — NREM 系统巩固与睡眠阶段框架。
- Klinzing, Niethard, & Born (2019), *Mechanisms of systems memory consolidation during sleep* — SO–spindle–ripple 机制框架。
- Rodheim et al. (2023), DOI `10.1101/lm.053685.122` — 情绪记忆与 SO-spindle coupling 的直接近期研究，但年轻成人分组仅 n=10/12，作为支持而非主证据。
- Denis et al. (2022), DOI `10.1111/ejn.15132` — 应激后 coupling 与情绪记忆呈负关联的反证/边界。
- Ng et al. (2025), DOI `10.7554/eLife.101992` — 一般睡眠依赖记忆中 coupling 效应的 Bayesian meta-analysis；作为 BACKGROUND_REVIEW，不替代情绪记忆原始研究。
- Denis & Payne (2024), DOI `10.1523/ENEURO.0285-23.2024` — NREM TMR 对 neutral 而非 negative component 有益，是解释选择性和阴性结果的重要边界。

## Preprint and abstract watchlist

- Patriota et al. (2026), bioRxiv DOI `10.64898/2026.06.05.730360`: REM theta phase-locked TMR 可能降低记忆情感色彩；尚未发现同行评议 Version of Record，按 `EX-10` 保留为 TOPIC-03 后续线索。
- World Sleep 2025 / Sleep Medicine supplement records `10.1016/j.sleep.2025.107441`, `10.1016/j.sleep.2025.107070`: 仅会议摘要，按 `EX-07`，不竞争本周焦点论文。

## Search addendum — SLEEP journal-focused rerun

- User-requested rerun: 2026-09-05.
- Access confirmed before rerun: 可访问 Oxford Academic 的 `SLEEP` 期刊站、PubMed、Europe PMC、Crossref，并读取开放全文与公开 SI；无可确认的机构订阅权限，不能绕过付费墙；Web of Science、Scopus、PsycINFO 授权检索不可用。
- Journal identity: `SLEEP` 是 Sleep Research Society 与 Australasian Sleep Association 的官方同行评议期刊，由 Oxford University Press 出版，覆盖基础、转化和临床睡眠/昼夜节律科学。官方2025 JIF 7.0、5-year JIF 6.6。

### Exact PubMed journal-field routes

| Route | Exact query | Hits |
| --- | --- | ---: |
| S1 | `Sleep[Journal] AND (("emotional memory"[Title/Abstract]) OR ("emotional memories"[Title/Abstract]) OR ("affective memory"[Title/Abstract])) AND (2024/01/01[Date - Publication] : 2026/12/31[Date - Publication])` | 3 |
| S2 | `Sleep[Journal] AND (emotion*[Title/Abstract] OR affective[Title/Abstract] OR fear[Title/Abstract]) AND (memory[Title/Abstract] OR consolidation[Title/Abstract] OR habituation[Title/Abstract]) AND (2024/01/01[Date - Publication] : 2026/12/31[Date - Publication])` | 7 |
| S3 | `Sleep[Journal] AND (emotion*[Title/Abstract] OR affective[Title/Abstract]) AND (EEG[Title/Abstract] OR polysomnography[Title/Abstract] OR fMRI[Title/Abstract] OR REM[Title/Abstract] OR NREM[Title/Abstract]) AND (memory[Title/Abstract] OR learning[Title/Abstract]) AND (2021/01/01[Date - Publication] : 2026/12/31[Date - Publication])` | 14 |

Oxford Academic title/subject searches and issue checks were then used to distinguish full articles from the journal's annual conference supplements.

### Eligible or near-eligible SLEEP articles

#### SLEEP-01 — Chappel-Farley et al. (2025)

- Title: *Individual differences in medial temporal lobe functional network architecture predict the capacity for sleep-related consolidation of emotional memories in older adults*.
- Chinese: **内侧颞叶功能网络结构的个体差异预测老年人睡眠相关情绪记忆巩固能力**。
- DOI: `10.1093/sleep/zsaf117`; PMID 40442306.
- Design: 36名健康老年人（72.9±5.6岁），整夜PSG、睡前/睡后情绪记忆辨别、3T结构像与静息态fMRI；SO、SO–spindle coupling 仅在约n=18子样本中分析。
- Result profile: hippocampal/amygdala network centrality 与更好的负性记忆保持相关；这些网络指标也与SO功率和SO–spindle coupling相关；没有观察到REM时长与情绪记忆保持的显著关系。
- Value: 是本轮 `SLEEP` 中最直接覆盖“情绪记忆 + SO–spindle coupling + fMRI”的正式论文。
- Caveat: 年龄限制明显；睡眠微结构子样本很小；rsfMRI与睡眠夜并非同步采集；coupling主要与网络指标关联，而不是对NREM–REM协同的直接检验。
- Gate/score: AMBER, 87.1/100. `REUSABLE_WITH_MODIFICATION`.
- Source: Version of Record、全文、SI可得；分析代码公开，数据依申请；Crossref未列update/correction relation。

#### SLEEP-02 — Viselli et al. (2026)

- Title: *Experimentally induced REM sleep fragmentation affects psychophysiological habituation to emotional stimuli*.
- Chinese: **实验诱发的REM睡眠碎片化影响对情绪刺激的心理生理习惯化**。
- DOI: `10.1093/sleep/zsaf409`; PMID 41432255.
- Design: 17名健康青年（23.18±3.94岁，14名女性），两条件反平衡被试内设计；64-channel PSG；用腕部振动在REM诱发皮层觉醒；比较睡前、次晨和48小时的old/new情绪记忆、主观反应、皮电与心率减速。
- Result profile: REM碎片化成功增加REM→N1转换，未明显改变TST、睡眠效率或WASO；没有影响情绪图片识别，却阻断心率减速的正常习惯化，效应持续至48小时，并与刺激诱发的顶枕alpha增强相关。
- Value: 本轮最新、最接近因果的健康青年REM实验，清楚区分“记忆内容保持”和“生理情感反应消退”。
- Caveat: n=17；未测SO–spindle coupling；关键阳性结局是心率习惯化而非记忆准确性；刺激同时降低REM总量，碎片化与REM丢失未完全分离；数据仅可申请、未发现预注册/公开代码。
- Gate/score: AMBER, 86.5/100. `REUSABLE_WITH_MODIFICATION`.
- Source: Version of Record、全文、SI可得；CC BY；Crossref未列update/correction relation。

#### SLEEP-03 — Alkalame et al. (2024)

- Title: *The relationship between REM sleep prior to analog trauma and intrusive memories*.
- Chinese: **模拟创伤前REM睡眠与侵入性记忆的关系**。
- DOI: `10.1093/sleep/zsae203`; PMID/PMCID 39235362/PMC11632187.
- Design: 27名健康成人，四晚正常或昼夜节律错位睡眠；第5天观看创伤影片，随后三天记录侵入性记忆。
- Result profile: 更高的创伤前REM比例与REM效率预测更少侵入；每增加约4%平均REM，侵入数约减少27%，每增加约4% REM效率，侵入数约减少21%；N3不相关。
- Value: 多晚PSG与健康成人创伤模拟设计较强。
- Caveat: 睡眠发生在创伤编码之前，回答的是易感性/编码准备状态，而不是编码后的睡眠巩固，故不应替代TOPIC-01焦点论文。
- Gate/score: AMBER, 78.3/100. Role limited to `BOUNDARY_EVIDENCE`.
- Source: Version of Record、PMC全文、SI可得；数据依申请；Crossref未列update/correction relation。

### Other SLEEP records screened

- Chappel-Farley et al. (2025) is the only recent full SLEEP article combining emotional memory, SO–spindle coupling and fMRI, but it uses healthy older adults and does not establish an REM mechanism.
- 2024 abstract `The Temporal Dynamics of Emotional Memory and Reactivity in Patients with Insomnia Disorder` reports a healthy-control SWS×REM result but is `Supplement_1` abstract-only (`EX-07`) and the full later article centers insomnia (`EX-02`).
- `Testing affect regulation theories of dreaming` (2026) was excluded for wrong outcome (`EX-04`).
- `The role of emotion in sleep: a quantitative analysis using EEG data` (2026) was excluded for wrong memory outcome (`EX-04`).
- Fear-memory-triggered sleep disruption and the 2023 ML297 paper were animal studies (`EX-02`).
- The remaining journal-field hits concerned sleep loss networks, pediatric sleep, insomnia connectomics, trauma-exposed/PTSD samples, or older non-emotional/general memory and did not satisfy the focal combination.

### Effect on the recommendation

- No SLEEP paper found in this rerun supersedes Yuksel et al. (2025) as the best single answer to the NREM–REM joint-contribution question.
- If journal priority is elevated above population age fit, **Chappel-Farley et al. (2025)** becomes the best SLEEP-specific alternative because it directly measures emotional memory, SO–spindle coupling and fMRI network architecture.
- If healthy-young experimental causality and outcome separation are prioritized, **Viselli et al. (2026)** becomes the best SLEEP-specific alternative, but it addresses REM continuity rather than NREM–REM coupling.
- Revised comparison set for the paper gate: Yuksel (overall Primary); Tabarak (coupling/cycle alternative); Chappel-Farley (SLEEP, coupling+fMRI alternative); Viselli (SLEEP, REM causal-boundary alternative). Azza remains a current supporting paper rather than a top-three recommendation after the journal-focused rerun.

## Paper confirmation gate

- Recommended focal paper: Yuksel et al. (2025), DOI `10.1038/s42003-025-07868-5`.
- Strong alternatives after SLEEP-focused rerun: Tabarak et al. (2024), DOI `10.1038/s41398-024-03146-w`; Chappel-Farley et al. (2025), DOI `10.1093/sleep/zsaf117`; Viselli et al. (2026), DOI `10.1093/sleep/zsaf409`. Azza et al. (2026) remains supporting current research.
- User confirmation: CONFIRMED on 2026-09-05 — selected **Yuksel et al. (2025)**, DOI `10.1038/s42003-025-07868-5`.
- Search status: COMPLETE. The confirmed paper is handed off to Translation and Deep Reading; Tabarak, Chappel-Farley and Viselli remain explicit alternatives rather than co-focal papers.
