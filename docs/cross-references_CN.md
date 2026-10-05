# 定位标签并核对交叉引用变化

[English](cross-references.md) · [项目检查](project_CN.md) · [论文审阅](review_CN.md)

无需修改稿件即可定位缺失、重复的引用目标：

```sh
als project check path/to/paper --main main.tex --engine pdflatex --bundle work/label-check --html-language zh
als verify inspection work/label-check
```

打开 `work/label-check/report.html`。“标签定义与交叉引用”表格保留键与源码位置。
每个引用展示选中根文件的字面依赖图中找到的定义数量、状态及第一个定义位置。
前向引用在依赖图扫描完后统一检查；后续每个重复定义都在真实文件、行号处提示，
并指出第一个定义的位置。

## 支持的源码形式

| 形式 | 示例 | 解释 |
|---|---|---|
| 定义 | `\label{键}`、cleveref 的 `\label[类型]{键}` | 一个字面键；读取可选类型但不解释其意义 |
| 单目标 | `\ref`、`\eqref`、`\pageref`、`\autoref`、`\autopageref`、`\nameref`、`\Nameref`、cleveref 名称命令 | 一个花括号键，里面的逗号仍属于该键 |
| 列表 | `\cref`、`\Cref`、`\cpageref`、`\Cpageref`、`\labelcref`、`\labelcpageref` | 以逗号分隔多个键 |
| 范围 | `\crefrange`、`\Crefrange`、`\cpagerefrange`、`\Cpagerefrange` | 两个花括号端点，分别保留参数角色 |
| 标签链接 | `\hyperref[键]{文字}` | 方括号内才是目标；文字不作为目标，其中嵌套的支持命令继续扫描 |

完整命令集合见 [reference_lexer.py](../scripts/reference_lexer.py)。清单保留大小写
与星号，但不证明当前宏包、样式实现了该写法。`label`、`eqref`、`Nameref`、
`hyperref` 的星号写法明确标为未验证，不猜测目标。标签和单目标键中的逗号保持完整，
仅 cleveref 列表按逗号拆分；cleveref 本身不支持含逗号的标签名。键按大小写精确
匹配；跨行参数仍指向命令起始行。

注释、转义反斜杠、支持的行内原样文本与代码示例不会混入清单。共用参数读取器
采用迭代方式，花括号深度最多 128，同时受项目 UTF-8 文件大小上限约束。
未闭合、动态、嵌套或空目标，以及不支持的可选语法产生带位置的
`reference-unverified`。此前已完整读取的范围端点仍保留，但出现提示意味着
清单可能不完整。旧式四个花括号参数的 `\hyperref` 会明确标为未验证。

## 审阅改目标与端点调换

```sh
als review --before path/to/original --after path/to/candidate --output work/label-review --language zh
als verify review work/label-review
```

将 `\hyperref[old]{相同文字}` 改成 `\hyperref[new]{相同文字}` 会产生
`reference_keys` 内容提示。将 `\crefrange{a}{b}` 调换成 `\crefrange{b}{a}`
也会提示，即使标签集合不变：审阅保留两个端点的参数角色。仅重排列表中的相同
键不会制造键变化；重复键仍按出现次数统计。

schema-1 项目检查新增 `label_inventory` 和 `reference_inventory`，审阅在
`before`、`after` 两侧新增同名清单及可展开表格。审阅扫描清单内 `.tex`、`.sty`、
`.cls`，包括未使用文件，因此不宣称按根文件解析了实际目标。未改动文件中的
暂不支持语法也进入 `source_scan_issues`。没有这些字段的旧报告保持可读；清单
沿用源码指纹和报告目录校验机制，关联同一份已观察证据。

## 定义数量意味着什么

数量描述源码字面观察，不能证明 TeX 实际使用哪个定义。宏展开、定义与条件执行、
重复执行、活动 catcode、`xr` 等外部或生成标签、样式语义、计数器类型、标签与
标题位置，以及引用论断正确性尚未检查。重复输入只扫描一次，并保留原有重复
源码提示；被排除的 include 不提供定义。检查器不会重编号、改名或修复目标。
应使用项目的实际宏包编译，再核对 PDF 中的目标行为。

本轮语法依据：[cleveref §4、§6](https://tug.ctan.org/macros/latex/contrib/cleveref/cleveref.pdf)、
[hyperref §6](https://ctan.math.illinois.edu/macros/latex/contrib/hyperref/doc/hyperref-doc.pdf)
及 [nameref 前端说明](https://ctan.math.illinois.edu/macros/latex/contrib/hyperref/doc/nameref.pdf)。
