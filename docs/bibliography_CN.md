# 检查参考文献条目与引用键

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend bibtex --bundle work/bib-inspection --html-language zh
als verify inspection work/bib-inspection
```

后端按论文实际设置选择；Biber 项目使用 `--backend biber`，也可保存在 `.als.json`。
检查器读取字面 `bibliography`/`addbibresource` 引用的项目内 `.bib`，不修改数据库。
打开 `report.html` 查看引用键、类型、文件和条目头行号；JSON 中的
`bibliography_entries` 保留逐条记录，重复条目也不会被静默合并。

## 避免把正文示例误认成条目

花括号 `@misc{key, ...}` 与圆括号 `@misc(key, ...)` 均可识别，支持多行、嵌套
花括号和引号值。标题中的 `@misc{...}` 属于字段文本，不会成为新条目。
`@string`、`@preamble` 的内容不提供引用键，也不会进行字符串展开。
类型转为小写，引用键保留原样；没有字段的完整花括号条目也会记录。

未闭合或括号不配对会标为“未验证”，后续区域停止扫描，未完成的条目头不会用来
满足引用。识别到条目头，不代表字段完整、类型被后端支持或数据库语法全部正确。

## 注释和重复键需要按实际后端核对

明确选择 BibTeX 时，`@comment` 后会从下一个 `@` 继续寻找条目；`.bib` 中的 `%`
也不等同于 TeX 的行注释。因此 `% @misc{key, ...}` 仍可能是有效输入，不要据此
认为引用已经禁用。未明确选择 BibTeX 时，包含 `@` 的完整注释体会跳过并标为
未验证；检查器不据此推断 Biber 的特殊注释处理结果。

同一数据库或多个已引用数据库内的重复键，会提示当前与首次条目头的位置。
首次位置按资源在字面源码中的遇到顺序记录，不按文件名排序；重复引用同一个
数据库不会重复记录条目。
明确选择 BibTeX 时，重复比较忽略 ASCII A–Z 的大小写；其他情况按原样比较。
引用查找始终严格按键名匹配，不推断 Unicode 大小写、别名或后端接受规则。
请选择实际来源，并用真实后端确认；工具不会合并或编造参考文献。

语法依据为已阅读的 [BibTeX 官方手册](https://tug.ctan.org/biblio/bibtex/base/btxdoc.pdf)
与[固定版本实现](https://github.com/TeX-Live/texlive-source/blob/a645809b018c7895d5326af2cabf73563f85f4bb/texk/web2c/bibtex.web)，
范围限于条目/字段边界、`@comment` 和 ASCII 大小写处理。常见结构另有真实
BibTeX/Biber 构建测试，仍不构成完整数据库语法验证。

## 范围与后续操作

每个数据库最多记录 10,000 个条目头及 10,000 条结构问题，源码读取仍限制为
2,000,000 字节；值扫描
使用迭代方式，不受 Python 递归深度限制。校验值绑定实际读取的数据库字节，
整体导出前会再次核对。字符串展开、别名、继承、crossref/xdata、远程资源、样式
规则和来源真实性不在此检查范围内。

未知引用应由作者提供真实条目；随后执行[配置构建](project_CN.md)，核对日志和
PDF，并保留待作者决定的问题。[headers.bib](../tests/fixtures/bibliography/headers.bib)
只是自动测试使用的自制控制数据，不引用真实研究。

## 手写参考文献

使用 `thebibliography` 手写条目的项目，不会仅因为这些条目而需要文献后端。
项目实际没有后端时，省略 `--backend`：

```sh
als project check path/to/manual-paper --main main.tex --engine pdflatex --bundle work/manual-inspection --html-language zh
als verify inspection work/manual-inspection
```

下面的合成文档无需数据库即可定义 `first` 与 `second`。用于实际论文时，
应由作者提供真实文献替换占位条目：

```tex
\documentclass{article}
\begin{document}
Synthetic citation control: \cite{first,second}.
\begin{thebibliography}{9}
\bibitem{first} Synthetic first entry.
\bibitem[Author(2020)]{second} Synthetic second entry.
\end{thebibliography}
\end{document}
```

检查支持可达 `.tex`、本地 `.sty`、`.cls` 中的 `\bibitem{key}` 与
`\bibitem[显示标签]{key}`。可选标签中的花括号与宏可以保留，但其含义不被
验证，内部命令不被当成引用键。`bibitem_inventory` 记录命令起始行、文件、
原样键与手写定义数量 `definition_count`；中英文离线报告提供可展开表格。
生成的 `.bbl` 不在该清单内。

引用查找结合手写条目和可达数据库的已解析条目头。手写重复键按原样精确比较，
不随后端折叠大小写；每个后续定义的 `duplicate-bibitem-key` 都定位到自身
文件与行号，并指出首次定义。数据库条目头与手写键相同时，报告未验证项
`bibliography-key-overlap`，因为条目头不能证明实际生成了重复条目。排除的
include 不提供键；重复输入保留仅扫描一次的限制。定义中的逗号保留为一个键，
引用命令仍使用自身的逗号列表语法。

审阅保存两侧原始 `bibitem_inventory`，包括清单内未使用的源码；仅修改条目键
也触发 `reference_keys`，且区分定义与引用角色、保留出现次数。可选标签和条目
正文不被解释为键；其源码差异仍可见，已有数值与公式检查继续适用。审阅清单
不宣称根文件级解析结果，仅源码审阅不会编译两侧。

空键、动态或嵌套键、无花括号键、星号命令、错误标签和过深参数会产生带位置的
`bibitem-unverified`；即使源码未改动也会提示。仅支持一个可选标签和一个字面
花括号键，花括号嵌套最多 128 层。不判断宏定义、条件执行、thebibliography
是否生效、refsection、`harvarditem` 等自定义命令、显示标签兼容性或论断支持。

语法依据是[固定版本 LaTeX 内核文献实现](https://github.com/latex3/latex2e/blob/2cdbff62d8da4886006978e8cfd805d128d44b4f/base/ltbibl.dtx)
和 [natbib 手册 §2.2](https://tug.ctan.org/macros/latex/contrib/natbib/natbib.pdf)。
原生编译回归对照实际 AUX `bibcite` 键，确保缺失手写键仍失败，并核对真实
重复定义警告。这些是合成工具回归，不是文献真实性或模型质量评测。
