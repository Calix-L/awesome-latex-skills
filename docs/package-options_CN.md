# 检查文档类、宏包选项与后端声明

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend biber --bundle work/package-inspection --html-language zh
als verify inspection work/package-inspection
```

后端仍由你在 CLI 或配置中明确选择。检查器只把完整的直接字面 biblatex 赋值
与所选工具比较，不会修改设置或按宏包默认值自动选择工具。

## 完整读取加载参数

`documentclass`、`LoadClass`、`usepackage`、`RequirePackage` 支持一个可选
选项列表、字面花括号名称及名称后的可选最低版本日期。宏包加载支持逗号名称
列表，文档类加载要求单个名称。`LoadClassWithOptions` 与
`RequirePackageWithOptions` 支持名称及日期形式，不判断传递选项。

选项中的嵌套花括号保护 `]` 与逗号。选项参数和尾随日期内的命令不会被拆成
独立加载、输入或文献引用。注释与已支持的原样区域沿用既有遮罩规则，位置保留
命令起始行。动态、嵌套或空名称、多组前置方括号、星号加载、未闭合参数及超过
128 层花括号会产生带位置的 `package-unverified`，不猜测依赖。

这些语法检查不证明宏包接受选项、最低日期满足或声明实际执行。

## 精确观察后端

| 直接 biblatex 选项 | 检查行为 |
|---|---|
| `backend=biber`、`backend={biber}` | 完整值与所选工具比较 |
| `backend=bibtex`、`backend={bibtex}` | 完整值与所选工具比较 |
| `note={backend=biber},backend=bibtex` | 只比较顶层 `backend`；其他选项有效性未检查 |
| `mybackend=biber` | 不当作后端赋值 |
| `backend=bibtex8` | 明确未验证，不误当成 `bibtex` |
| `backend=\macro`、单独的 `backend` 或空值 | 明确未验证 |
| `backend=biber,backend=bibtex` | 保留两者，优先级未验证 |
| 未直接赋值、传递或全局选项 | 不推断默认值及实际后端 |

`bibtex8` 是 biblatex 手册中的独立后端。本项目构建接口支持 `biber` 与
`bibtex`，诊断改进不代表新增其他工具支持。暂不支持的值产生
`backend-options-unverified`；完整且支持的直接赋值与已明确选择的后端不同时，
在声明的实际文件与行号报告 `backend-mismatch`。重复的相同赋值保留出现次数，
冲突赋值不擅自选择覆盖结果。

## 报告与源码审阅

schema-1 检查新增 `package_inventory`，包含 `file`、`line`、加载 `command`、
文档类或宏包 `name`、经过遮罩的字面 `options`（含方括号，未设置时为空）。
直接 biblatex 加载行另含 `backend_options` 与 `backend_options_complete`，
仅描述已观察参数；空列表不证明实际运行后端。实际构建行为应核对原生控制文件。

schema-1 审阅新增 `package_inventory.before/after` 与可展开双语表格。
审阅记录清单内全部 `.tex`、`.cls`、`.sty`，包括未使用文件；项目检查只跟随
选中根文件的字面依赖。即使源码未改动，错误加载、暂不支持或冲突的后端参数
仍会提示。支持范围内的选项修改在源码差异和两侧表格可见，不推断语义内容分数。
没有新字段的旧报告仍可显示。

项目配置要求整数 `"schema": 1`；`true`、`1.0`、`"1"` 或缺失值会在验证和
读取配置中的主文件前被拒绝。现有引擎、后端和编译轮次设置保持兼容。

语法依据是[固定版本 LaTeX 内核类与宏包实现](https://github.com/latex3/latex2e/blob/b604e2e24e76d12f9aeb0bb81e017f29b5ddd473/base/ltclass.dtx)
及 [biblatex 手册 §3.1.1、§3.16](https://ctan.math.illinois.edu/macros/latex/contrib/biblatex/doc/biblatex.pdf)。
原生回归会编译嵌套选项的合成加载器及两种带花括号的后端选择；静态检查不展开
宏、不解析传递或全局选项、不判断条件分支或宏包样式兼容性。

[English guide](package-options.md) · [项目流程](project_CN.md) · [源码审阅](review_CN.md)
