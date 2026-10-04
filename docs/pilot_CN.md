# 小规模、可追溯的评测试运行

[English](pilot.md) · [完整协议](evaluation_CN.md) · [任务目录](../evaluation/cases.json)

当前仓库有十个合成任务和维护者编写的参考结果，没有独立模型的效果测量。
下面用于准备一个规模明确的实验；准备命令不调用模型，也不能证明技能提升。

## 运行前确定比较问题

同一输入下比较不加载技能与加载所提供技能的两个条件，固定实际模型版本、生成
设置和工具权限。先选择三个任务：

| 任务 | 核心问题 | 字面检查之外的证据 |
|---|---|---|
| `rescue-errors` | 修复是否保留数量和未知引用键？ | 实际编译、未解决引用与公式审查 |
| `polish-scope` | 润色是否保留范围和否定主张？ | 独立语义审查及准确原文摘录 |
| `pdf-table` | 重建是否保留单元格和不确定性？ | 原始/候选页面对照及审查意见 |

每个任务重复两次，共 **12 次运行、6 组配对**。这是流程试运行，不能据此推断广泛
质量提升。预先确定执行者、审查者、审查时如何隐藏条件、公布哪些结果，以及
费用上限。不知道的 token/费用保持 `null`，不要从日志长度推算。

## 准备隔离目录

```sh
als benchmark prepare --case rescue-errors --case polish-scope --case pdf-table --trials 2 --seed 17 --output evaluation-runs/pilot-01
```

输出应为 `prepared-not-run`，运行数为 12。协调者读取
`evaluation-runs/pilot-01/batch.json` 的随机顺序。每个新 Agent 会话只能访问一个
准备好的任务目录。基线不能发现全局技能、仓库参考文件、候选答案或评分标准。
记录任何上下文污染；随机顺序本身不能防止泄漏。

## 用实际配置执行

使用[配置命令运行器](evaluation_CN.md)，或遵守协议的独立手工会话。记录真实
Agent、模型、版本、设置、轮次和会话身份，保留原始日志与工具证据。命令运行器
使用你实际配置的规格文件：

```sh
als benchmark run --task evaluation-runs/pilot-01/tasks/rescue-errors-01-baseline --spec path/to/actual-baseline-spec.json
```

分别执行全部 12 个任务。每个任务包括技能条件都需要独立 session ID；不能在
多个会话中原样复用同一规格。运行器可能调用收费服务；准备和报告不会。
模型与审查者身份不能用示例值代填。服务凭据放在任务文件和留存产物之外。

## 提交结束后再审查

将评分表导出到 Agent 工作区之外：

```sh
als benchmark review-template --task evaluation-runs/pilot-01/tasks/rescue-errors-01-baseline --output work/rescue-baseline-rubric.json
```

协调者用不透露条件的候选编号提供输入、提交结果和必要证据，隐藏条件/模型标签
及预期答案。填写所有标准的审查者身份、分数、理由、实际 `file:line` 与该行准确
摘录。未审查前评分表保持空白。Agent 会话结束后，按[完整协议](evaluation_CN.md)
将已完成评分放到对应任务的 `human-review.json`。

## 保留失败，分别汇报证据

```sh
als benchmark report --batch evaluation-runs/pilot-01 --output work/pilot-report-01
```

阅读 `work/pilot-report-01/report.json` 和 `report.md`。报告全部 12 个计划运行，
包括超时、无提交、污染、未审查和无法配对的任务。区分字面检查、实际编译/提取
与人工质量判断，配对汇总不能替代失败分析。涉及编译时需使用实际选择的引擎；
缺少本地工具保持未验证。

公开前核对身份、日志与审查证据，移除敏感信息，说明合成任务范围、样本数与缺失
数据。把失败写入 [failure-log.md](../evaluation/failure-log.md)。流程可复现后，
再扩展至全部技能和获得授权的真实案例。
