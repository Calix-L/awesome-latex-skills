# 接受论文修改前，单独核对公式变化

[English](math-review.md) · [完整审阅流程](review_CN.md) · [文档导航](README.md)

`x+y` 被改成 `x-y` 后，论文仍可能编译成功，数值和引用键也可能没有变化。
公式内容需要单独核对。

```sh
als review --before path/to/original --after path/to/candidate --output work/formula-review --language zh
als verify review work/formula-review
```

打开 `work/formula-review/report.html`。“公式环境变化”列出新增和删除的字面公式；
“带源码位置的公式环境”并排展示两份源码的文件名、起止行号和可展开内容。
纯源码检查只需要 Python 标准库。按[完整流程](review_CN.md)附上实际构建报告，
还能查看日志、成功 PDF 和页面预览。

例如，以下只改运算符的修改现在会触发审查提示：

```tex
% 原稿
\begin{equation}x+y\end{equation}
% 候选稿
\begin{equation}x-y\end{equation}
```

## 检查范围

| 字面检查 | 覆盖内容 |
|---|---|
| 基本环境 | `math`、`displaymath`、`equation`、`eqnarray` |
| AMS 展示公式 | `align`、`alignat`、`flalign`、`gather`、`multline` |
| 无编号形式 | 上述展示公式的星号版本，`displaymath` 除外 |
| 嵌套内容 | 完整外层正文，包括 `split`、`aligned`、矩阵、参数、标签、编号和文本 |
| 文件类型 | `.tex`、`.sty`、`.cls`；包含未改动及新增、删除的文件 |

检查器屏蔽注释和支持的原样文本，再按环境名、完整字面内容及出现次数比较。
空白变化也可能触发提示；相同公式的移动或重排不会单独产生公式内容提示。
顺序变化对含义的影响仍需人工核对，实际位置保留在清单中。
原有 `$…$`、`$$…$$`、`\(…\)`、`\[…\]` 检查保持可用。

未闭合、嵌套配对错误、无起始标记的结束标记，以及动态内部环境名，都会在
`source_scan_issues` 和页面中给出位置。这些区域不提供完整公式值。恢复到外层
结束位置后，后续配对完整的公式仍可被收录；请结合真实 TeX 日志判断。

扫描以单个文件和普通类别码为前提，不展开宏，不执行定义、条件或分组，不拼接
跨 `input` 文件的公式环境，不识别自定义外层公式环境，也不验证 TeX 语法或数学
等价性。字面配对不能证明这段内容会执行或编译。科学含义仍由作者确认。
嵌套环境作为外层内容保留，不重复计为独立公式。

## JSON 与离线分享

schema-1 报告新增 `math_environment_inventory.before/after`，每项包括 `file`、
`environment`、`line`、`end_line` 和屏蔽后的字面 `content`；
`math_environment_scope` 记录范围。发生变化时，
`content_audit[].math_environments` 列出新增、删除的字面值和次数。
已有字段与 schema 保持兼容。

分享时保持审阅目录完整。`verify review` 不需要原项目路径；自行修改交付文件会
使初始清单校验失败。环境的预期用法可查阅
[AMS/LaTeX Project 官方用户指南第 3.2–3.7 节](https://texdoc.org/serve/amsldoc.pdf/0)，
工具只检查其中有限的字面范围。

## 定界符公式与源码位置

“带源码位置的定界符公式”展示 `$…$`、`$$…$$`、`\(…\)`、`\[…\]` 的
精确配对、文件名与起止行号。相邻的 `$x$$y$` 按两个行内公式观察；`\$` 不会
开启公式。完整配对的字面内容和出现次数继续使用已有
`content_audit[].simple_math` 字段。移动相同公式仅改变位置，不虚构内容变化；
注释与已知原样文本保持屏蔽。

未闭合、孤立的显式结束符和冲突定界符记录为定位后的 `math-delimiter-*`
源码问题，包括未改动的 `.tex/.sty/.cls` 文件。含歧义区域不提供完整公式值。
精确配对采取保守范围：混用写法、`$a+\text{$b$}$` 等嵌套模式，或跨字面
花括号深度的配对需人工核对；这不等于判定源码无效。工具不执行宏定义、参数、
条件或修改后的类别码，也不拼接跨文件的数学模式。字面配对无法证明 TeX
有效性、实际执行或数学等价性。

schema-1 增加可选 `math_delimiter_inventory.before/after`，每项包含 `file`、
`delimiter`、`closing`、`mode`、`line`、`end_line` 和屏蔽后的 `content`；
`math_delimiter_scope` 记录解释边界。已有 schema、命令退出语义和旧报告渲染
保持兼容。定位清单仅覆盖 `.tex/.sty/.cls`；其他文本文件原有通用内容信号保留。

[LaTeX 内核源码 Math Environments](https://github.com/latex3/latex2e/blob/develop/base/ltmath.dtx)
给出了 `\(`、`\)` 与 `\[`、`\]` 依赖实际数学模式的实现；工具观察范围小于
TeX 可执行语言，不能用静态配对代替真实构建。
