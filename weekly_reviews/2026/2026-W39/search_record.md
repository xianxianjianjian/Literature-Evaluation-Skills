# Search Record

- Week: 2026-W39
- Search date: 2026-09-17
- Status: COMPLETE
- Search type: 面向每周译评的定向检索；不是系统综述，也不声称穷尽。
- Confirmed topic: REM 睡眠连续性对情绪记忆内容与心理生理情感反应的差异性作用。

## Search Question Profile

| Field | Decision |
| --- | --- |
| Population/context | 健康成人，优先青年；临床、儿童和动物研究只作边界证据 |
| Focal construct | 情绪记忆内容、情感反应/习惯化、REM 连续性与碎片化 |
| Relation/mechanism | REM 操纵或睡眠阶段指标是否对记忆与情感反应产生可分离影响 |
| Preferred methods | 被试内操纵、整夜 PSG/高密度 EEG、ECG/EDA、延迟记忆测验 |
| Preferred study type | 2025–2026 同行评议原始研究；Version of Record 优先 |
| Transfer need | 为后续“记忆准确性与情绪反应分开建模”的实验设计提供可复用范式 |
| Known exclusions | 综述、会议摘要、错误人群、错误结局、仅预印本不作为焦点 |

## Search routes

| Route | Source | Query / logic | Filters | Hits | Retained/notes |
| --- | --- | --- | --- | ---: | --- |
| Q1 | Europe PMC | `(TITLE_ABS:"emotional memory" OR TITLE_ABS:"emotional memories" OR TITLE_ABS:"emotional processing") AND TITLE_ABS:sleep` | 2025-01-01 to 2026-09-17 | 91 | 宽检索；保留记忆与情感反应相关原始研究 |
| Q2 | Europe PMC | `(TITLE_ABS:REM OR TITLE_ABS:"rapid eye movement") AND TITLE_ABS:emotional AND (TITLE_ABS:memory OR TITLE_ABS:habituation OR TITLE_ABS:reactivity)` | 2025-01-01 to 2026-09-17 | 51 | 强化 REM、习惯化与反应分离 |
| Q3 | Europe PMC | `(TITLE_ABS:spindle* OR TITLE_ABS:"slow oscillation" OR TITLE_ABS:theta) AND TITLE_ABS:emotional AND TITLE_ABS:sleep` | 2025-01-01 to 2026-09-17 | 42 | 补充 NREM/REM 微结构与方法边界 |
| J1 | SLEEP / Oxford Academic + PubMed/PMC | 题名、DOI、期次、全文与 SI 核验 | 2024–2026 | — | 核验 Viselli 与 Chappel-Farley 的 Version of Record |
| C1 | PubMed/PMC、Crossref/出版社页面 | DOI、版本、修订/撤稿状态、全文/SI、数据/代码/预注册声明 | Round 2 | — | 对主选与强备选作来源和完整性检查 |
| Z1 | Zotero Local API | DOI 与精确题名查重 | 当前文库 | 0 | Viselli 无既有父条目，可作为新论文进入流程 |

Web of Science、Scopus 与 PsycINFO 的授权检索在当前环境不可用，未声称搜索这些数据库。增加同义词、SLEEP 期刊定向检索和阶段微结构检索后，未出现能同时超过主选论文的“实验操纵 + 健康青年 + PSG/EEG + 记忆/情感反应双结局”候选，排序已稳定，停止继续扩展。

## Round 1 screening

| ID | Record | Year | Decision | Reason |
| --- | --- | ---: | --- | --- |
| R1-01 | Viselli et al., *Experimentally induced REM sleep fragmentation…* `10.1093/sleep/zsaf409` | 2026 | INCLUDE | REM 实验操纵；记忆与心理生理反应双结局；健康青年 |
| R1-02 | Azza et al., *Sleep to remember, sleep to protect…* `10.1038/s41398-026-03910-0` | 2026 | INCLUDE | NREM spindle 与 REM theta；模拟创伤与多日侵入记忆 |
| R1-03 | Reinhold et al., *Past stories, future worries…* `10.1016/j.brat.2026.104978` | 2026 | INCLUDE | 直接比较未来相关性、记忆与情绪反应，但缺少 PSG 操纵 |
| R1-04 | Chappel-Farley et al., *Individual differences in medial temporal lobe…* `10.1093/sleep/zsaf117` | 2025 | INCLUDE | SLEEP 正式论文；情绪记忆、网络与 SO–spindle coupling |
| R1-05 | Greco et al., *Disarming emotional memories using TMR during REM sleep* `10.1162/imag.a.924` | 2025 | MAYBE | REM TMR 因果价值高；范式与当前碎片化问题不同 |
| R1-06 | Morehouse et al., *Vagal heart rate variability during REM sleep…* `10.3389/fnbeh.2025.1513655` | 2025 | MAYBE | 自主神经与负性记忆偏向相关；观察性机制边界 |
| R1-07 | Cross et al., *Effects of aperiodic neural activity…* `10.1016/j.neuropsychologia.2025.109270` | 2025 | MAYBE | 睡眠 EEG 新指标；并非直接 REM 操纵 |
| R1-08 | Colin et al., *Sodium Oxybate Alters Sleep Architecture…* `10.1111/jsr.70386` | 2026 | MAYBE | 睡眠结构药理操纵与情绪选择性；机制专一性较弱 |
| R1-09 | Tsang et al., *Temporal proximity to sleep determines emotional memory interference* `10.1101/lm.054156.125` | 2026 | MAYBE | 时间接近性与干扰；缺少目标 REM 生理操纵 |
| R1-10 | Rodheim et al., *Does sleep change the emotional bias in memory in older adults?* `10.1016/j.neuropsychologia.2025.109237` | 2025 | EXCLUDE | `EX-02` 老年样本，不适合作为本周健康青年焦点 |
| R1-11 | Zeng et al., *Impaired emotional memory dissipation in insomnia disorder* `10.1017/S0033291725101566` | 2025 | EXCLUDE | `EX-02` 临床失眠样本，适合作边界而非焦点 |
| R1-12 | Rusin et al., *Sleep and emotional memory of preschool children adopted from foster care…* `10.1093/jpepsy/jsag039` | 2026 | EXCLUDE | `EX-02` 儿童与寄养经历人群 |
| R1-13 | Kurdziel et al., *Top-down instruction outweighs emotional salience…* `10.3389/fnbeh.2025.1643449` | 2025 | EXCLUDE | `EX-04` 主要问题是选择性巩固，不直接区分情感反应习惯化 |
| R1-14 | Patriota et al., *Theta phase-locked memory reactivation during REM sleep…* `10.64898/2026.06.05.730360` | 2026 | EXCLUDE | `EX-05` 预印本；保留为前沿线索，不作为焦点 Version of Record |
| R1-15 | Zhang et al., *Dissociable reactivation during NREM and REM sleep…* `10.64898/2026.08.04.742295` | 2026 | EXCLUDE | `EX-05` 预印本；题目高度相关但尚无同行评议正式版 |
| R1-16 | Rao et al., *Sleep, emotional regulation, and limbic-cortical dynamics…* `10.1016/bs.pbr.2026.07.002` | 2026 | EXCLUDE | `EX-06` 综述，不是焦点原始研究 |
| R1-17 | Yasser et al., *Sleep and memory consolidation: Neural and cognitive perspectives* `10.1016/bs.pbr.2026.07.001` | 2026 | EXCLUDE | `EX-06` 综述 |
| R1-18 | Saito et al., *Amygdalo-cortical dialogue underlies memory enhancement by emotional association* `10.1016/j.neuron.2025.01.001` | 2025 | EXCLUDE | `EX-03` 非睡眠范式 |
| R1-19 | Leitner et al., *Isolated REM Sleep Behavior Disorder…* `10.3390/clockssleep7010009` | 2025 | EXCLUDE | `EX-02` 临床 RBD 人群 |
| R1-20 | Rodrigues et al., *Multi-scale sleep dynamics in memory consolidation…* `10.1016/j.sleep.2026.108998` | 2026 | EXCLUDE | `EX-06` 综述 |

## Round 2 Quality Gate and weighted ranking

评分维度按固定权重：主题相关性 25、证据质量 20、期刊/来源 15、方法迁移 15、当前研究迁移 10、新颖性 10、全文/SI 5。每项 0–5 分后按权重归一。

| Rank | Candidate | Gate | Relevance | Design | Source | Method | Transfer | Novelty | Full/SI | Total |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Viselli et al. 2026 | AMBER | 5.0 | 3.5 | 5.0 | 4.5 | 4.5 | 5.0 | 5.0 | **91.5** |
| 2 | Chappel-Farley et al. 2025 | AMBER | 4.5 | 3.5 | 5.0 | 4.5 | 4.0 | 4.5 | 5.0 | **87.0** |
| 3 | Azza et al. 2026 | AMBER | 4.5 | 3.0 | 4.0 | 4.5 | 4.0 | 4.5 | 5.0 | **82.0** |
| 4 | Reinhold et al. 2026 | AMBER | 3.5 | 4.0 | 4.0 | 3.0 | 3.5 | 4.0 | 4.5 | **74.0** |

### Primary — Viselli et al. (2026)

- Literature role: CURRENT / Focal Paper.
- Main strength: 反平衡被试内交叉设计，用腕部振动在 REM 期诱发皮层觉醒；64 通道 PSG/EEG，并在睡前、次晨和 48 小时测量 old/new 识别、主观反应、EDA 与心率减速。
- Main result profile at Search stage: 操纵增加 REM→N1 转换；未观察到情绪图片识别改变，但阻断了心率减速的正常习惯化，且效应延续至 48 小时。
- Main caveats: 最终样本 n=17；REM 碎片化同时减少 REM 时长和比例并增加 N1，因此无法完全分离“碎片化”与“REM 丢失”；关键阳性结局是心率习惯化；未发现预注册、公开代码或公开原始数据。
- Method transfer: `REUSABLE_WITH_MODIFICATION`。被试内多夜设计、REM 在线刺激、记忆与生理情感反应的并列结局可直接借鉴；需扩大样本并控制 REM 总量变化。
- Source/integrity: DOI、题名、作者、期次与 Version of Record 一致；Main PDF 和 SI 可用。当前检查未发现明显 correction、retraction 或 Expression of Concern；这只是当前来源状态核验，不证明研究无误。

### Strong Alternative 1 — Chappel-Farley et al. (2025)

- Strength: 情绪记忆、内侧颞叶网络、整夜 PSG 与 SO–spindle coupling 同篇结合，方法迁移价值高。
- Caveats: 健康老年样本；睡眠微结构约 n=18 子样本；主要是个体差异关联，无法提供 REM 操纵证据。
- Method transfer: `REUSABLE_WITH_MODIFICATION`。
- Why below Primary: 它更适合研究网络结构与 NREM 微结构，但对本周“内容记忆与情感反应分离”的直接度较低，且没有 REM 因果操纵。

### Strong Alternative 2 — Azza et al. (2026)

- Strength: 被试内创伤/中性夜、64 通道 hdEEG、NREM spindle 与 REM theta、六日侵入记忆日记。
- Caveats: n=22 且全为女性；关键睡眠指标与结局主要是相关关系；侵入记忆只在创伤条件测量。
- Method transfer: `REUSABLE_WITH_MODIFICATION`。
- Why below Primary: 它更全面覆盖 NREM/REM 振荡，但无法像 Viselli 那样直接检验 REM 连续性操纵，也没有同等清楚地把识别记忆与自主神经习惯化并列为主要结局。

### Alternative — Reinhold et al. (2026)

- Strength: 研究问题直接比较睡眠前后负性记忆的情绪反应及未来相关性。
- Caveat: 睡眠/清醒时段设计缺少 PSG/EEG，对具体睡眠阶段机制的可迁移性较弱。
- Method transfer: `REUSABLE_WITH_MODIFICATION`。

## Final decision

- Selected focal paper: Viselli et al. (2026), DOI `10.1093/sleep/zsaf409`.
- Selection authority: 用户明确委托系统选择一篇尚未处理的新论文，因此本次选择记录即满足论文 Gate。
- Why #1 outranks #2: Viselli 的被试内 REM 操纵和记忆/情感反应双结局与本周问题完全同构；Chappel-Farley 的优势在网络与 NREM coupling，但其老年样本、小微结构子样本和观察性关系降低了对当前因果问题的直接性。
- Source package: Version of Record Main PDF 与 SI DOCX 已取得并验证；来源包可进入 Translation 和 Deep Reading。
