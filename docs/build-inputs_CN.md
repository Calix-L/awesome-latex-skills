# 构建期间核对选定的本地输入

[English](build-inputs.md) · [独立构建脚本](../latex-rescue/references/build-check.md) · [审阅流程](review_CN.md)

显式选择需要在构建期间保持一致的文献库、样式或其他本地资源。例如：

```sh
als build path/to/paper/main.tex --backend bibtex --output work/guarded-build --until-stable --require-resolved --watch-input references.bib --watch-input styles/local.bst
```

已有 `.als.json` 时，用 `--project path/to/paper` 代替源码位置参数，监测选项相同。
独立安装的 `latex-rescue/scripts/check_build.py` 也支持这些选项。

**监测路径相对于实际主文件所在目录**，包括配置选择了嵌套主文件的情况；不是
相对于 shell 工作目录，也不一定相对于配置文件。路径用 `/` 分隔，含空格时加
引号。以 `-` 开头的文件名写成 `--watch-input=--refs.bib`。每个文件重复一次选项。

## 检查阶段与结果

| 阶段 | 记录的证据 |
|---|---|
| 创建输出前 | 验证路径并记录初始指纹；文件无效或缺失时，不创建构建目录，不启动编译工具 |
| 每次引擎或文献工具运行后 | 再次记录指纹；正常返回的失败和超时也会记录 |
| 构建尝试正常结束时 | 与已有本地输入一起进行最终核对 |

即使各编译工具退出码都是 `0`，被监测文件发生变化、缺失、无法读取或被符号链接
替换，构建仍会失败。工具保留当前作者文件、日志和失败 JSON，不把 PDF 呈现为
已核验成功，也不会恢复旧文件。原生进程失败时保留原始失败原因。
创建前检查失败返回 `2`；完成尝试后发现不一致返回 `1`。

schema-3 报告的 `input_tracking.watched_inputs` 列出显式选择；对应的
`local_inputs` 先记录 `preflight`，再记录步骤名、SHA-256、字节数和读取错误。
与引擎记录器重叠时，每个步骤只记录一次；记录器覆盖仍单独保留在
`input_tracking.recorder_steps` 中。不加选项时，原有记录器范围保持不变，
新增监测清单为空。

## 用于审阅当前稿件

```sh
als review --before path/to/original --after path/to/paper --after-build work/guarded-build/build-report.json --output work/guarded-review --language zh
als verify review work/guarded-review
```

审阅页在构建旁列出“显式监测的输入文件”，重新核对包括初始观察在内的所有指纹，
并保留实际构建报告。构建后又修改文献库，会使旧证据过期，阻止审阅目录发布。
请为当前候选稿生成新的构建证据，不要为了通过旧指纹核对而恢复作者文件。
输入不一致的失败报告可以直接读取，无需把它当作当前稿件的一致构建记录附上。

## 范围与限制

- 只选择主文件目录树内已有的普通文件。拒绝绝对路径、越界和非便携路径、符号
  链接及构建输出中的文件；不支持通配符，不自动推断文献工具的全部依赖。
- 最多 128 个选择参数，同一文件重复选择会合并。单文件在初始和后续读取时均
  限制为 64 MiB；初始选择集合最多 256 MiB。指纹按流式字节计算。
- 选择文件不证明 BibTeX/Biber 实际使用它。未选择的文献库、外部字体和系统资源
  仍在显式监测之外，除非引擎另行在本地输入范围内记录了它。
- 指纹是时间点观察，不锁定编辑器，也不冻结构建。两次观察之间修改又恢复、瞬时
  重定向竞态、被中断或证据写入失败，都可能留下未验证项。科学内容、发布者身份
  和完整环境复现需要分别核对。

[完整中英文合成论文](../examples/full-paper/README.md)已经在实际构建中选择监测文献库
和本地样式；导出的离线操作页也提供相应命令。
