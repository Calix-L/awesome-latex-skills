# 用真实证据评测技能

[完整英文协议](evaluation.md) · [十个自制任务](../evaluation/cases.json)

评测分别记录运行结果、有限的字面检查、真实编译、人工审查、耗时和实际费用。
案例与测试夹具用于验证工具行为；它们不是模型对照实验，也不能证明技能提升了质量。

## 从两个任务开始

```sh
als benchmark prepare --case polish-scope --trials 1 --output evaluation-runs/pilot-01
```

这会准备同一个案例的 baseline 与 with-skill 两个任务。两边的 `TASK.md` 与
`inputs/` 相同，`submission/` 初始为空；只有 with-skill 获得指定技能的完整
`context/`。评分规则与参考答案不会复制进去。重复 `--case` 可以选择多个案例；
省略时使用全部十个案例，默认每边三次，共 60 个任务。

准备任务不会调用模型。运行前，为每个任务配置新的独立会话，保持实际模型版本、
工具权限与设置一致。baseline 必须关闭自动或全局技能加载。Agent 只应访问自己的
任务目录，不能读仓库、其他任务、`batch.json` 或评分规则。

## 连接你实际使用的运行程序

运行器接受一个读取标准输入、在当前目录工作、向 `submission/` 写入成果的外部
CLI 或适配程序。下面是配置结构，所有占位值都需要替换成实际记录；
`--fresh-session` 只是示意参数，必须使用你的程序支持的参数。

将 `runner-spec.json` 放在任务目录之外：

```json
{
  "schema": 1,
  "command": ["/absolute/path/to/your-adapter", "--fresh-session"],
  "agent": "实际 CLI 与版本",
  "model": "实际模型标识",
  "model_version": "实际解析到的模型版本",
  "session_id": "本次真实且独立的会话标识",
  "settings": {
    "tools": "实际工具权限",
    "context_policy": "只读任务输入与指定 context，关闭全局技能"
  }
}
```

Windows 路径可以使用正斜杠，也可以在 JSON 中转义反斜杠。命令参数会保留在证据中，
凭据应沿用适配程序自己的安全配置，不要放进参数。模型身份与会话标识由实际运行
程序提供；这里的记录不能独立证明服务商身份，也不会自动创建新会话。

```sh
als benchmark run --task evaluation-runs/pilot-01/tasks/polish-scope-01-baseline --spec runner-spec.json --timeout 600
```

运行器将原样的 `TASK.md` 字节送入 stdin，并以该任务目录为工作目录，按参数列表
启动指定命令。命令可以使用你已有的服务商账户并产生其正常费用。它不会解释管道、
重定向等 shell 语法；访问隔离与隐式上下文需要由适配程序配置。超时终止直接启动的
命令，适配程序应管理自己的子进程，退出前完成写入，不留下后台工作进程。

每次尝试保留 `runner/` 下的原始准备记录、归属记录与完整 stdout/stderr 日志。
`execution.json` 记录实际墙钟耗时、退出码、失败或超时，以及日志、归属记录和全部
提交文件的 SHA-256。缺少的 token 与账单信息保留为 null。后续修改日志、运行记录
或提交成果会被报告拒绝；改变输入或技能上下文也会触发校验失败。

已有尝试不会被覆盖；重试需要新准备的任务。`.execution.lock` 防止并发运行。
异常终止留下锁时，先确认原进程已停止并检查证据，再手动处理。退出码 0 表示命令
成功且证据完整，1 表示执行或完整性失败，2 表示前提或参数错误，130 表示中断。
命令成功不等于成果满足字面检查、完成编译或通过人工质量审查。

## 人工审查与完整报告

用另一个真实会话运行 with-skill 条件，随后在任务目录之外生成空白审查表：

```sh
als benchmark review-template --task evaluation-runs/pilot-01/tasks/polish-scope-01-baseline --output work/baseline-review.json
als benchmark report --batch evaluation-runs/pilot-01 --output work/pilot-report-01
```

审查表包含四个问题，初始分数为 null。实名审查者为每项填写 0–2 分、理由、实际
成果的 `file:line` 和该行的准确摘录；完成后放到对应任务的 `human-review.json`。
对另一条件同样操作，并尽可能隐藏条件信息、随机审查顺序。空表不能计为人工评分；
工具能校验证据位置，无法验证审查者判断或证明评审确实盲化。

报告保留所有计划任务，包括未运行、失败、超时和无效证据。独立编译工具出错会将
构建标为未验证，并保留有效的模型运行和字面评分。耗时、token、费用与人工审查
分别显示覆盖数量，费用按币种汇总；没有测量的数据不能变成零。重复会话、改变
运行条件或缺少真实归属会使前后对照不可比较。

小规模试运行只覆盖选中的案例；单次对照与字面检查都不能支持普遍提升的结论。
分享结果时保留全部失败、实际模型与设置、原始日志、审查证据及完整批次。已有其他
运行器生成的证据也可以按[英文协议](evaluation.md#bring-evidence-from-an-existing-runner)
的 `execution.json` 格式导入，无需再次调用模型。
