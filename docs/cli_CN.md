# 命令行使用指南

[English](cli.md) · [安装](install.md) · [项目检查](project_CN.md) · [修改审阅](review_CN.md)

安装 Python 包后使用 `als` 或 `python -m awesome_latex_skills`；从源码运行时，将
`als` 替换为 `python scripts/als.py`。用户路径相对于当前工作目录解析，工具脚本
相对于安装包或仓库定位。包含空格的路径需要加引号。

## 从检查到交付

```sh
als project init "path/to/paper" --main main.tex --engine pdflatex --backend bibtex --passes 3
als project check "path/to/paper" --html work/inspection.html --html-language zh
als --json build --project "path/to/paper" --output work/build-01 --require-resolved
als review --before "path/to/original" --after "path/to/paper" --after-build work/build-01/build-report.json --output work/review-01 --language zh
als verify review work/review-01
```

引擎和参考文献工具应按论文实际设置填写；没有文献后端时省略 `--backend`。
输出使用新文件或新目录。完整的构建、PDF 和科学内容分别核对，不能用静态检查
代替编译，也不能用编译成功代替内容审阅。

## 整体交付项目检查报告

```sh
als project check "path/to/paper" --bundle work/inspection-02 --html-language zh
als verify inspection work/inspection-02
```

打开 `work/inspection-02/report.html` 阅读问题与建议，分享整个目录保留 JSON 和
文件校验清单。目标须是论文目录之外的新目录，不能混用 `--output`、`--html`。
报告移走后仍可离线校验，不要求原论文路径存在。报告文件完整、静态问题状态和
真实编译结果各自独立；完整性通过不代表论文没有问题。详见[项目指南](project_CN.md)。

## 参数、文件名与帮助

```sh
als build --project "path/to/paper" --output work/build-02 --engine=lualatex --passes=4
als --json build --output work/build-dash -- --submission.tex
als --json extract --output work/extracted-dash -- --paper.pdf
als build --project "path/to/missing-project" --help
als extract --help
```

使用一个源码文件或一个 `--project`，不能同时指定。明确提供的引擎、文献工具及
轮次覆盖配置。工具共享参数规则，支持 `--参数=值`；支持无歧义的长选项缩写，保存
命令时建议使用完整选项名。`--` 后的内容是字面位置参数，不再当成选项；所有选项
应放在它前面。已配置的项目构建也允许在命令末尾加 `--`。

普通值选项重复时以最后一个为准，JSON 证据绑定实际生效的输出目录，较早的目录
不会被创建或修改。建议每个选项只写一次。`--project` 重复会被拒绝，避免项目
选择不清楚。构建与提取的帮助、参数格式错误在执行前返回；它们不读取项目配置，
也不启动编译或提取。帮助不要求 TeX 或 PyMuPDF 可用。

## 读取 JSON 结果

`--json` 必须放在命令名称之前。顶层 `--help` 使用纯文本；构建或提取的帮助会在
JSON 的 `stdout` 中保留，`result` 为 null，`evidence` 为空。

| 字段 | 含义 |
| :--- | :--- |
| `status` / `exit_code` | 命令的执行状态与退出码。 |
| `result` | 工具的结构化结果；构建或提取从本次新输出中加载。 |
| `evidence` | 本次绑定的报告路径，不附加已有目录中的旧报告。 |
| `invocation` | 尝试调用的 Python、工具脚本、工作目录及完整参数。 |
| `stdout` / `stderr` | 工具输出与错误信息。 |

项目构建的 `invocation.arguments` 包含解析后的主文件与实际传递的设置，便于核对
配置覆盖。构建/提取的帮助、参数预检错误、版本查询及未知命令的 `invocation` 为 null。
调用记录只描述执行尝试，不能单独证明进程启动或完成；判断结果仍需日志与退出码。

常见退出码为：完成 0，检查或构建失败 1，参数或前提无效 2，中断 130。PDF 提取的
运行错误使用 1。允许未验证的示例可能返回 0 和 `partial`，应继续核对 `result`。
详细契约和依赖见[英文指南](cli.md)。
