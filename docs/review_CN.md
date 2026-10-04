# 对照源码、构建证据与 PDF 审阅论文修改

准备独立的原稿与候选稿目录，生成一个新的审阅目录。工具不修改两份论文；
输出目录必须位于两份项目之外，且不能已经存在。

```sh
als review --before path/to/original --after path/to/candidate --output work/review-01 --language zh
```

打开 `work/review-01/report.html`。页面先展示改动文件数、内容变化提示、待作者
确认项和 PDF 页数，再展示构建状态、文件清单、可展开的差异与新增/删除的字面值。
图片等二进制资源的变化也会列出，校验值保留在 `review.json`。
纯源码审阅只需要 Python 标准库；没有提供构建报告时，两边均明确显示“编译未验证”。

## 加入实际构建与页面证据

按论文实际的引擎与文献工具编译，再传入生成的报告。例如使用 pdfLaTeX 与 BibTeX：

```sh
als build path/to/original/main.tex --output work/original-build --backend bibtex --passes 3
als build path/to/candidate/main.tex --output work/candidate-build --backend bibtex --passes 3 --require-resolved
als review --before path/to/original --after path/to/candidate --before-build work/original-build/build-report.json --after-build work/candidate-build/build-report.json --notes decisions.md --output work/review-02 --language zh
```

成功 PDF 的页面预览需要 PyMuPDF，可通过 `python -m pip install ".[pdf]"` 安装。
报告会保留实际日志、构建报告、成功 PDF 和页面图片。失败构建仍显示错误与日志，
不会把失败时的残留 PDF 当成成功结果。页面仅按页码对齐，分页变化需要人工对照。
`--language zh` 只改变界面标签；源码、日志、说明文字保持原文。

主文件和构建记录中的本地输入必须与当前文件校验值匹配。声明过的日志、记录器
或终端输出文件缺失时，工具会拒绝生成最终审阅目录。复制期间变化的报告、日志、
PDF，以及渲染后变化的输入和证据，也会阻止最终发布。每个保留文件均记录路径、
SHA-256 和字节数。旧构建报告没有 PDF 校验值时，界面仍标明“编译时身份未验证”。
这些检查保证生成时的一致性，不会锁住论文目录，也不能独立认证报告的提供者。

## 正确理解检查结果

数值、标签/引用/文献键和简单公式的字面变化是核对提示，不能判断修改是否正确。
支持 `$…$`、`$$…$$`、`\(…\)`、`\[…\]`，转义的 `\$` 不作为公式边界。
宏展开、命名公式环境、catcode 变化、科学含义均不在这种字面比较范围内。
未发现字面变化不能证明含义不变；编译成功也不能证明结论正确或满足投稿要求。

审阅覆盖 `.tex`、`.bib`、`.sty`、`.cls`、`.bst`、`.als.json` 及支持的图片/PDF 类型。
生成目录和环境目录会被排除，完整范围列在页面与 `inventory_scope` 中。
其他文件类型不在本次清单覆盖范围内。请将实际论文输入放在生成目录之外。
源码中的 `TODO`、`[UNCERTAIN]` 会列出位置，包括注释里的可见标记，交由作者决定。

离线查看时保持整个输出目录完整。完整的中英文论文案例可以直接运行：

```sh
als paper --output work/full-paper-zh --language zh
```

该命令仍需要真实 TeX 工具；详情见[完整案例](../examples/full-paper/README.md)。
也可以阅读[英文指南](review.md)与[项目检查指南](project_CN.md)。
