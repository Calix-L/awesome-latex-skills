# 把案例复制到自己的工作区

[English](examples-export.md) · [任务指南](tasks_CN.md) · [文档索引](README.md)

安装后的 wheel 已包含全部案例。`examples export` 可直接复制一个案例到新的
工作区，无需 TeX、PyMuPDF、模型账号或仓库源码：

```sh
als examples list
als examples export --case full-paper --output ../my-example --language zh
als verify example ../my-example
```

未安装 CLI 时，在源码目录用 `python scripts/als.py` 代替 `als`。目标必须是
仓库或安装包内置资源目录之外的新目录。以下案例路径均相对导出目录。

打开 `../my-example/report.html`，离线查看原稿、候选稿、修改说明、依赖和命令。
`README.md` 提供相同的 Markdown 操作说明。`--language zh` 选择生成指南的中文
界面；原始源码和决策说明保留原有语言。

## 选择案例

| `--case` | 原始输入 → 候选结果 | 仍需明确处理 |
|---|---|---|
| `full-paper`（默认） | `case/before/` → `case/after/` | 完整中英文项目、后端/字体依赖及未决计时协议 |
| `rescue` | `case/input.tex` → `case/output.tex` | 最小修复、未知引用键和模糊公式 |
| `polish` | `case/input.tex` → `case/output.tex` | 数量、范围和否定主张的语义审查 |
| `fmt` | `case/input.tex` → `case/output.tex` | 局部宽度修复，不能替代官方模板 |
| `read` | `case/input.md` → `case/analysis.md` | 结果冲突、假设和缺失计时信息 |
| `pdf2tex` | `case/input.pdf` → `case/output.tex` | 表格空白/精度、图件不确定性和未知引用 |

`examples list` 保留五个既有案例条目，并新增六个 `export_cases`，包含单独的
完整论文项目。一次只复制一个案例，不同案例使用不同的新目录。

## 先检查，再编辑单独的候选副本

完整论文保留隐藏的 `case/after/.als.json`、本地样式、图件、文献库和章节。
仓库级 README 链接由独立生成的操作指南替代；实际源文件、决策说明和 MIT
许可证保留原始字节。

在导出目录中，使用已安装 CLI：

```sh
als doctor --project case/after --skill latex-rescue --language zh
als build --project case/after --output ../example-build --until-stable --require-resolved
als build case/after/main-cn.tex --engine xelatex --backend bibtex --passes 3 --output ../example-chinese --require-resolved
```

英文候选稿需要 pdfLaTeX/BibTeX，中文稿需要 XeLaTeX/BibTeX 和 Noto Serif CJK SC。
构建工具将生成文件与源码树隔离。原生 CI 回归会编译导出的原稿（预期失败）、
英文和中文候选稿，并再次核验未变化的导出目录。其他案例按生成指南操作。
PDF 提取/审查需要可选 PyMuPDF；复制 PDF 不需要它。

保留未改动的导出目录，Agent 编辑前另建候选副本，构建输出放在两份源码之外。
按[审查流程](review_CN.md)检查修改。原稿/候选结果均为维护者编写的合成材料。
导出包含答案和修改说明，不能作为盲评 Agent 工作区；盲评使用[试运行准备](pilot_CN.md)。

## 移动与核验初始字节

移动或分享时保留整个目录：

- `example.json` 记录案例、源码版本、合成来源、入口，以及复制文件的来源路径、
  大小和 SHA-256。
- `integrity.json` 覆盖自身以外的全部文件，包括两种指南、来源记录、许可证和源码。
- `als verify example DIRECTORY` 在目录移动后仍可使用，不读取原始安装包或仓库。
  文件修改、缺失或新增会失败；来源记录与清单不一致也会失败。

导出状态为 `exported-not-run`，不是构建或模型质量结果。导出退出码 `0` 表示
完整初始副本，输入无效或发布失败返回 `2`。核验一致返回 `0`，字节不一致返回
`1`，缺失/无效清单或与清单一致但结构无效的来源记录返回 `2`。损坏的来源记录
字节仅报告变化，不解释其内容。能替换全部文件和清单的人也能生成匹配目录；
字节核验不能认证发布者或科学内容。

文件先在临时同级目录准备、封存，复核源清单和字节，再完整核验暂存产物后重命名。
复制、渲染、封存失败或源文件变化时，不会产生只有一部分的最终目录。即时检查
期间请保持源文件和目标不变；不提供并发编辑锁或断电持久性保证。源文件最多
2,000 个，每个源文件及读取的版本/案例目录元数据不超过 8 MiB，源码和许可证
总计不超过 64 MiB。生成的来源记录/清单还遵守[产物核验器的读取限制](verification_CN.md)。
