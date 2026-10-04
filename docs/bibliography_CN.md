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
