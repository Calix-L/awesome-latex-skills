# 检查完整 LaTeX 项目

[完整英文指南](project.md) · [修改与 PDF 审查](review.md)

项目检查器只读取源码，记录字面依赖、文件校验值与问题位置。它不会修订论文，
也不会把静态检查当成编译或科学内容审查。

## 选择主文件，生成可读报告

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend bibtex --output work/inspection.json --html work/inspection.html --html-language zh
```

打开 `work/inspection.html`，查看错误、警告、未验证项、源码位置与处理建议。
报告区分“资源缺失”“被 includeonly 排除”“未验证”，同时保留输入校验值及完整
JSON 证据。它支持窄屏与深色模式，无需网络或 JavaScript。

HTML 和 JSON 使用不同的新文件名；已有目标会在写入前被拒绝。同目录下的 HTML
会以相对链接指向 JSON，分享时保留在一起。HTML 文件需要 `.html` 或 `.htm` 后缀。
省略 `--html-language zh` 时使用英文界面，诊断消息与 JSON 中的原文保持一致。
未安装 CLI 时，用 `python scripts/als.py` 代替 `als`。

## 整体导出与分享检查报告

```sh
als project check path/to/paper --bundle work/inspection-01 --html-language zh
als --json verify inspection work/inspection-01
```

`--bundle` 不能与 `--output`、`--html` 混用。目标必须是论文源码目录之外的新目录，
其中包含 `report.html`、`inspection.json` 和 `integrity.json`。打开 HTML 即可阅读，
页面提供 JSON 与校验清单的相对链接，支持窄屏和深色模式。分享时保留整个目录；
不会复制论文源码。

所有文件先在目标旁的临时目录内生成并记录校验值，发布前复核全部已读取源码的
指纹，再通过同一文件系统的目录重命名发布。渲染、写入、清单生成或发布失败时，
临时文件会清理，不会发布只有一部分报告的目录。导出期间请保持源码与目标路径
不变；这些即时检查不锁定并发编辑，也不保证断电后的持久性。

检查结果为 `blocked` 时仍导出问题报告，检查命令返回 `1`。离线校验独立检查
报告文件是否与清单一致，不读取原论文；即使检查发现错误、原稿后来修改，完整
报告仍可校验通过。它不证明当前源码仍与报告一致，也不编译 TeX 或认证作者。
缺失、变化或额外文件返回 `1`，无效或缺失清单返回 `2`。详见
[离线校验指南](verification_CN.md)。

原有分别导出 JSON/HTML 的方式会先准备两份内容再写入，但两份文件不构成事务，
I/O 失败仍可能留下部分结果。需要整体交付时使用 `--bundle`。
完整论文案例保留原有平铺报告，并新增 `inspection-before/`、`inspection-after/`
及 `verification.json` 中的两次完整性校验结果。

## 保存实际构建设置

```sh
als project init path/to/paper --main main.tex --engine pdflatex --backend bibtex --passes 3
als project check path/to/paper --html work/next-inspection.html --html-language zh
als build --project path/to/paper --output work/build-01 --require-resolved
```

`project init` 创建 `.als.json`，不会覆盖已有配置。主文件必须是项目内已有的
UTF-8 `.tex` 文件，支持 BOM；生成目录不能作为主文件位置。引擎、参考文献工具与
轮次会先校验再写入。无参考文献后端时用 null；切换设置需明确编辑配置。
构建命令的 `--engine`、`--backend` 和 `--passes` 可以覆盖配置，构建输出必须使用
新目录。检查报告也记录配置文件的 SHA-256。

没有明确主文件时，检查器在源码清单中寻找唯一的 `documentclass` 根文件；多个
候选需要选择。明确传入主文件或已有配置时，只解析选中主文件的可达源码，不会
解析无关章节或其他论文。`root_selection` 与 `root_candidate_scope` 说明候选范围。

`inputs` 记录实际依赖；`observed_files` 记录此次检查读取过的全部文件及 SHA-256，
包括用于自动选择主文件的其他 `.tex`、实际读取的配置及校验过的配置主文件。即使主文件不唯一、报告
为 `blocked`，也会保留这些判断依据并在返回前核对文件是否变化。两份清单在 HTML
中分别展示。校验值绑定实际解析的字节；它们不能锁住并发编辑，也不认证文件作者。

## 注释与代码示例不会混入依赖

检查按源码顺序区分普通注释、转义控制符、`verb`/`verb*` 以及字面的
`verbatim`/`verbatim*`、`lstlisting`、`minted` 区域。例如：

```tex
% \begin{verbatim} 是注释里的示例
\input{chapter} % 这个依赖仍会被检查
\verb|\input{example}| % 原样显示的命令不会当成依赖
```

反斜杠控制符 `\\` 不会凭空产生后面的命令。行号和源码偏移保留，支持 CRLF 与
UTF-8；行内 `verb` 支持星号、分隔符前的空格及数字分隔符。行为依据
[LaTeX 内核源码](https://github.com/latex3/latex2e/blob/main/base/ltmiscen.dtx)。
`verb*` 的星号必须紧接命令；有空格时，星号会成为原样文本的分隔符。
分隔符前的制表符受内核的记号化行为影响，会明确标记为未验证；此时遮罩只是近似结果。

行内原样文本缺少结束分隔符时，只遮住当前行；原样环境没有字面结束标记时遮住
后续源码。两种情况均报告文件与行号，状态至少为 `needs-review`，不能将未检测到
依赖理解为依赖不存在。宏展开、类别码修改、自定义原样环境、包的转义或终止选项
不在该扫描器的解释范围内，仍需实际编译。源码与配置的单次读取上限为 2,000,000
字节；读取时继续增长、超出上限的文件也会被拒绝。

参考文献条目表展示引用键、类型和条目头位置；重复键与未闭合区域另有提示。
圆括号、字段内示例和特殊注释的处理见[参考文献检查指南](bibliography_CN.md)。

## 能发现哪些问题

- 支持带括号与常见不带括号的 `input`、多行字面参数、引号文件名、`include`、
  图片、参考文献、本地 `.cls`、`.sty` 和 `.bst`。跟踪本地 `LoadClass`、
  `LoadClassWithOptions` 与 `RequirePackageWithOptions` 中的依赖。
- 字面的 `includeonly` 只排除 `include`，不会排除 `input`。被排除的章节记录为
  跳过，不会检查其存在性或扫描其中的依赖。
- 按源码顺序进入字面输入；其中的图片路径声明影响后续命令。新的 `graphicspath`
  替换旧路径，先按扩展名顺序再按目录查找；`DeclareGraphicsExtensions` 可指定顺序。
  动态声明会使后续相关搜索保持未验证，不沿用已经失效的旧路径。
- 提示缺失资源、未知引用与文献键、重复标签、字体与引擎不符、明确的后端冲突，
  以及 `natbib`/`biblatex` 同时加载。字面依赖环会阻止检查通过；重复输入需要审查，
  相同本地包的重复加载不会重复扫描内容。
- 校验值来自实际解析的字节；检查过程中发生变化的文件会被拒绝。

默认图片扩展名顺序只是常见 PDF 引擎的子集，驱动规则、自动转换、宏展开、分组、
条件分支、系统包内部行为、外部搜索路径及旧辅助文件仍需真实构建核对。
图片搜索依据[LaTeX 官方源码](https://github.com/latex3/latex2e/blob/develop/required/graphics/graphics.dtx)。
未知文献键应由作者提供来源，检查器不会编造引用。

清单遍历会在进入前跳过 `.git`、`work`、`dist`、`build`、`.als-runs`、
`__pycache__`、`evaluation-runs`、`.venv`、`venv` 和 `node_modules`。这些目录中的
文件不参与自动根文件选择；明确引用的项目内依赖仍可被跟踪。将论文源码与资源
放在生成目录之外，确保后续修改审查也能覆盖它们。项目边界内的符号链接被拒绝，
外部路径和动态参数会标记为未验证。

`ready` 表示未发现支持范围内的静态问题，`needs-review` 表示有警告或未验证项，
`blocked` 表示存在错误并返回退出码 1；配置或前提无效返回 2。

[完整中英文论文案例](../examples/full-paper/README.md)同时生成
`inspection-before.html`、`inspection-after.html` 和独立的构建/PDF 修改审查。
检查资源、真实编译和审查内容各有用途，应分别核对结果。

<a id="project-aware-prerequisites"></a>

## 按项目设置检查依赖

```sh
als doctor --project path/to/paper --skill latex-rescue --language zh
als doctor --project path/to/paper --main main.tex --engine xelatex --backend biber --skill latex-rescue --language zh
als --json doctor --project path/to/paper --skill latex-rescue
```

只读 `.als.json` 和检查器可达源码，不写入、编译或安装。显式主文件/引擎/后端
覆盖有效配置。没有配置时可自动选择唯一根文件，但不猜测引擎或文献后端。
需要编译的技能遇到未选引擎，或可达文献资源但未选后端时，会阻止就绪。

JSON 保留表示工具探测的 `local_prerequisites_met`，新增完整 `project` 检查和
综合 `status`。即使工具全部可用，缺失源码资源仍可阻止项目。`needs-review`
保留警告、未验证项和人工检查。退出码 `0` 只表示检查未受阻，不是编译通过；
受阻返回 `1`，无法读取/无效输入返回 `2`。显式所选引擎不在 PATH 上，也是
项目检查错误，即使该技能单独环境检查中的编译器仅为建议。

`--language zh` 翻译人类输出标签和环境处理建议；源码诊断、原生错误和 JSON
保持原文。`--main` 必须配合 `--project`。不提供项目时保留原有 pdfLaTeX 默认。

[任务指南](tasks_CN.md) · [兼容约定](compatibility.md#中文说明)
