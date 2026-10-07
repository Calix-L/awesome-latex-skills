# 完整读取依赖命令参数

[English](dependency-arguments.md) · [项目检查](project_CN.md) · [修改评审](review_CN.md)

选项值里用花括号保护的右方括号，不应遮住图片文件名：

```tex
\includegraphics[note={literal ] text},width=1cm]{figures/plot}
```

检查器保留完整选项并查找 `figures/plot`，但不会验证或执行 `note` 设置。
真实编译仍需实际定义该键的宏包。选项或动态文件参数中的 `\cite`、`\ref`、
`\input` 不计入正文命令，避免伪引用与伪依赖；这不证明宏在运行时不会执行它们。

| 声明 | 字面读取范围 |
|---|---|
| `input` | 一个花括号、裸写或双引号文件名 |
| `include`、`bibliographystyle` | 一个花括号文件名 |
| `includeonly`、`bibliography` | 一个花括号名称列表；空 `includeonly` 排除全部 include |
| `includegraphics` | 可选星号，最多两组平衡可选参数，一个花括号文件名 |
| `addbibresource` | 最多一组平衡可选参数，一个花括号文件名 |
| `graphicspath` | 完整外层花括号内的一组组字面目录 |
| `DeclareGraphicsExtensions` | 一个花括号扩展名列表；扩展名语法由检查器另行核对 |

[LaTeX Project 图片指南](https://ctan.math.illinois.edu/macros/latex/required/graphics/grfguide.pdf)
第 4.4 节说明键值与传统双可选参数接口及星号。扫描器记录参数形式，不推断
实际驱动、设置有效性或宏包行为。

检查报告增加 `dependency_inventory`，评审报告增加
`dependency_inventory.before/after`。每条记录包含
`file`、`line`、`command`、`value`、`options`、`starred`、`supported`、`issue`。
双语离线表格将命令声明与解析后的依赖分开显示；支持的声明仍可能指向缺失、
动态或项目外资源。规范路径查找和源码指纹继续独立核对。

错误、动态、嵌套文件名，以及意外的可选参数或星号，保留为未验证项。项目诊断
继续使用 `dynamic-reference`，评审源码问题使用 `dependency-unverified`。
未闭合或过深的参数会保守地停止该文件后续命令观察，并明确提示清单可能不完整。
最多读取 128 层花括号、32 组可选参数；仅上表对应的零、一、两组形式受支持。
这是解析器边界，不是 TeX 的限制。

报告 schema 与 CLI 退出码语义不变；旧报告没有新增字段时仍能展示。静态扫描
不会展开宏或计算条件、分组作用域，也不代替真实编译。原有 UTF-8、源码大小、
项目根和离线交付核验限制继续适用。

原生合成测试用 pdfLaTeX、XeLaTeX、LuaLaTeX 编译一个明确不执行内容的本地选项
键，核对引号章节和图片的 recorder 记录，再用 `graphics`、`graphicx` 分别编译
传统双参数接口。原始 wheel 和重建源码包在仓库外重复检查与报告流程。
