# Evidence Policy

本协议定义焦点论文、作者解释、评译者判断和外部依据之间的证据边界。所有 Skill 都必须保留这些边界，原文没有的信息不得猜测。

## 【原文直接内容】

包括焦点论文直接报告的 Methods、实验参数、数据、统计结果、事实和结果。该名称取代旧称“原文直接结果”，因为 Methods 等内容同样属于直接内容。

直接内容必须忠实保留数字、方向、显著性、不确定性和限定条件。相关不得改写为因果；总体 N 不得代替未知的模型实际 N；不显著结果不得因看似不重要而删除；原论文内部错误或不一致不得被系统静默修正。

## 【作者解释】

包括作者在 Discussion 等位置提出的机制、原因、意义和推测。作者解释不等于数据已经直接证明。中介分析不得自动写成机制已证明，functional connectivity 不得自动解释为方向性连接。

作者解释可使用 `ED0`–`ED3` 标记其 Evidence Distance，具体定义见 [identifier-policy.md](identifier-policy.md)。

## 【评译者分析】

包括独立的方法学、统计学、理论或可重复性判断。必须明确标注为评译者判断，不得伪装为作者原结论，也不得偷偷替原论文改正分析或结果。

## 【外部依据 EXT-xxx】

用于中文术语核验、方法学解释、外部文献比较和独立评价。每条外部依据使用 `EXT-001` 形式的标识，并记录可追溯来源。外部依据不得与焦点论文自己的结果混写或冒充原始证据。

## Source Anchor

重要结论应尽可能绑定精确 Source Anchor：

- Section；
- Subsection；
- Page；
- Table；
- Figure；
- Supplementary Table；
- Supplementary Figure。

Supporting Information 是主体证据的一部分，不能只审阅 Main Article。示例：

```text
【原文直接内容｜Methods 2.5，p.4；Table 2】
【作者解释｜Discussion，p.12；ED2】
【评译者分析｜基于 CLM-003 与 AUD-002】
【外部依据 EXT-004｜用于术语核验】
```

Source Anchor 缺失时应显式记录缺口，不得制造页码、表号或补充材料内容。
