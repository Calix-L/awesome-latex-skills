# 检查文献引用命令与引用键变化

[English](citations.md) · [项目检查](project_CN.md) · [修改审阅](review_CN.md)

项目检查与修改审阅共用引用扫描器，覆盖常用 LaTeX、natbib 和 biblatex 语法。

| 形式 | 示例 | 检查的字面参数 |
|---|---|---|
| 单组引用 | `\cite`、`\citep`、`\Citet`、`\parencite`、`\textcite`、`\autocite`、`\footcite` | 最多两个 `[说明]`，后接 `{键,键}` |
| 多组引用 | `\cites`、`\parencites`、`\textcites`、`\autocites`、`\footcites` | 最多两个全局 `(说明)`，然后逐组读取 `[说明][说明]{键,键}` |
| 作者、标题、年份等 | `\citeauthor`、`\citetitle`、`\citeyear`、`\fullcite`、`\notecite` | 字面引用键；说明参数不作为键 |
| 文献表选择 | `\nocite{键}` / `\nocite{*}` | 保留选择；只有 `nocite` 将 `*` 视为全部条目 |
| 文字包装 | `\citetext{说明; \citealp{键}}` | 文字不作为键；继续扫描里面的引用命令 |

完整支持列表见 [citation_lexer.py](../scripts/citation_lexer.py)。清单保留大小写和
星号写法，但不证明当前宏包、样式支持某个变体。说明参数支持花括号保护的结束
符与转义符号；注释及支持的原样文本示例不会混入键。参数采用迭代扫描，花括号
深度上限为 128，同时受项目检查器的 UTF-8 文件大小限制。

## 定位项目中的引用

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend biber --bundle work/citation-check --html-language zh
als verify inspection work/citation-check
```

打开 `work/citation-check/report.html`。每行包含引用键、命令、星号、参数组编号
及**命令起始行号**；跨行参数组共用命令起始位置。第二组或后续组缺少文献键时
也会在此处提示，键名按大小写精确比较。schema-1 JSON 新增 `citation_inventory`，
原有文献条目头仍在 `bibliography_entries`；清单关联已读取源码指纹，并与
HTML/JSON 一起记录离线目录校验值。

## 审阅只改引用键的修改

```sh
als review --before path/to/original --after path/to/candidate --output work/citation-review --language zh
als verify review work/citation-review
```

只将 `\parencites{known}{old}` 第二个键改成 `new`，即使数值和公式不变，也会
产生 `reference_keys` 内容提示。重复出现的键保留次数；同一命令内仅重排相同
键不制造键变化提示。报告新增修改前后的 `citation_inventory` 与可展开表格。
审阅扫描清单内 `.tex`、`.sty`、`.cls`，包括未使用文件；项目检查只扫描选中
根文件的字面依赖图。仅提供源码的审阅不会运行 TeX。

## 不完整语法会明确提示

说明未闭合、无花括号、动态或嵌套键、空键、过多说明参数，以及 `\volcite`、
`\citefield` 等暂不支持的特殊语法会产生带位置的 `citation-unverified`。
多组引用中之前已完整读取的组仍保留，但出现提示意味着清单可能不完整。
自定义 `cite...` 名称不会被默认当成普通引用参数语法。

扫描器不展开宏，不判断定义、条件分支、活动 catcode、refsection、别名、说明
参数中的命令、其他名称的自定义命令、手写 `\bibitem` 或外部文献资源；不验证
命令和样式可用性、说明语义、字段、引用顺序或文献是否支持论断。应另用实际
配置的原生后端编译并核对 PDF。

本轮语法依据：[biblatex 手册 §3.9](https://ctan.math.illinois.edu/macros/latex/contrib/biblatex/doc/biblatex.pdf)
及 [natbib 手册 §2.3–2.5](https://mirrors.ctan.org/macros/latex/contrib/natbib/natbib.pdf)。
