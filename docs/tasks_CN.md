# 从论文任务开始

[English](tasks.md) · [安装](install.md) · [命令速查](cli_CN.md)

| 当前任务 | 第一个有用的结果 | 接下来核验 |
|---|---|---|
| [修复编译](#repair) | 项目设置、缺失资源与问题位置 | 实际日志和未解决的引用 |
| [润色正文](#polish) | 保留原稿主张的可编辑候选稿 | 源码差异与作者审查 |
| [更换模板](#format) | 基于所提供官方模板的限定范围迁移 | 实际页面和投稿要求 |
| [阅读论文](#read) | 带原文位置的主张与证据 | 假设、冲突与未决问题 |
| [恢复 PDF 源码](#recover) | 页面提取结果与可编辑重建稿 | 原始与重建页面对照 |

下面是使用流程。`als` 准备或检查证据；编辑和分析由你的 Agent 按对应 Skill
完成，命令本身不会调用外部模型。未安装包时，在源码目录中用
`python scripts/als.py` 代替 `als`。将示例路径替换为自己的路径，含空格时加引号。
输出目录必须是论文源码目录之外的新目录。让 Agent 编辑前，保留未改动的原稿。

<a id="repair"></a>

## 修复编译

1. 确认实际主文件、引擎和参考文献后端。已知设置可以保存一次；`project init`
   创建 `.als.json`，拒绝已有配置。不使用文献后端时省略 `--backend`。

   ```sh
   als project init path/to/paper --main main.tex --engine xelatex --backend biber
   als doctor --project path/to/paper --skill latex-rescue --language zh
   ```

2. 没有配置文件时，显式提供实际设置：

   ```sh
   als doctor --project path/to/paper --main main.tex --engine xelatex --backend biber --skill latex-rescue --language zh
   als project check path/to/paper --main main.tex --engine xelatex --backend biber --bundle work/inspection-01 --html-language zh
   ```

   `doctor` 只读检查工具与源码，展示问题位置，不编译或写入文件。退出码 `1`
   表示受阻，`2` 表示参数错误或项目无法读取/配置无效。退出码 `0` 仍可能显示
   `needs-review`，需要审查提示。打开 `work/inspection-01/report.html` 阅读或分享
   静态报告。中文选项翻译界面和环境处理建议；源码诊断和 JSON 保留原文。

3. 在单独的候选副本上使用 `latex-rescue`。提供原始日志，要求最小修复，保留数值、
   公式和未知引用键，报告剩余不确定项。构建已经配置的候选稿：

   ```sh
   als build --project path/to/candidate --output work/build-01 --until-stable --require-resolved
   ```

   查看 `work/build-01/build-report.json` 和保留的日志。失败构建也是证据。
   PATH 上存在工具，不等于这篇论文能编译通过。
   [项目设置](project_CN.md) · [参考文献问题](bibliography_CN.md)

<a id="polish"></a>

## 润色正文

1. 保留原稿并建立候选副本。选择 `latex-polish`，指定轻度、中度或严格润色，说明
   修改章节、目标读者，以及哪些科学主张必须由作者确认。
2. 要求 Agent 保留数量、单位、因果/否定主张、引用键、公式和 TeX 命令，并说明
   实质性的措辞选择。
3. 集中审查两份源码：

   ```sh
   als review --before path/to/original --after path/to/candidate --output work/polish-review --language zh
   als verify review work/polish-review
   ```

   打开 `work/polish-review/report.html`。数值、引用、公式变化和 TODO 帮助定位
   作者审查，但字面量未变不能证明原意未变。不提供 `--before-build`/`--after-build`
   时，编译仍未验证。需要实际构建证据时，分别用真实设置编译：

   ```sh
   als build path/to/original/main.tex --output work/polish-before --engine pdflatex --backend bibtex --until-stable --require-resolved
   als build path/to/candidate/main.tex --output work/polish-after --engine pdflatex --backend bibtex --until-stable --require-resolved
   als review --before path/to/original --after path/to/candidate --before-build work/polish-before/build-report.json --after-build work/polish-after/build-report.json --output work/polish-built --language zh
   ```

   [润色案例](../examples/polish/README.md) · [审查选项](review_CN.md)

<a id="format"></a>

## 更换模板

1. 提供官方作者模板，以及目标会议/期刊、年份、赛道、文章类型和提交阶段。阅读
   `latex-fmt`，明确排版与正文修改的范围。仓库的演示模板不能代替官方作者包。
2. 用候选稿实际设置体检：

   ```sh
   als doctor --project path/to/candidate --main main.tex --engine pdflatex --backend bibtex --skill latex-fmt --language zh
   ```

3. 按[审查流程](review_CN.md)构建和对比原稿、候选稿。在实际页面检查溢出、页数、
   匿名要求、字体和必需章节。分别用各自实际设置构建，再通过 `--before-build`
   和 `--after-build` 附上对应的 `build-report.json` 文件；不同模板可用不同引擎/文献后端。

   [排版案例](../examples/fmt/README.md) · [官方要求入口](../latex-fmt/references/templates/venue-guide.md)

<a id="read"></a>

## 阅读论文

粘贴文本使用 `paper-read` 不需要 PDF 工具。数字 PDF 可以先提取：

```sh
als doctor --skill paper-read --language zh
als extract paper.pdf --output work/reading-pages --render
```

打开 `work/reading-pages/report.html`。选择速读、阅读或深读，向 Agent 提供论文
和必要参考文件。要求主张、假设、方法、局限与矛盾结果都指向原文页码/章节，
再核对源页面。缺少可选 PyMuPDF 不阻止粘贴文本阅读，但实际提取必须有该库。

[阅读案例](../examples/read/README.md) · [提取选项](cli_CN.md)

<a id="recover"></a>

## 恢复 PDF 源码

```sh
als doctor --skill pdf2tex --language zh
als extract original.pdf --output work/recovery-pages --chars --render
```

打开 `work/recovery-pages/report.html`，把提取证据交给 `pdf2tex`。要求可编辑源码和
重建说明，覆盖页面范围、不确定符号、表格空白/精度、矢量图与参考文献。用实际
引擎构建候选稿，再对比原始 PDF 页面。提取不是 OCR，也不能恢复原始源码。
只有图片的扫描 PDF 需要先采用单独选择的 OCR 流程。

[两页恢复案例](../examples/pdf2tex/README.md) · [完整论文演示](../examples/full-paper/README.md)

## 先试一次完整演示

```sh
python -m pip install ".[pdf]"
als paper --output work/manuscript-demo --language zh
```

需要[完整论文案例](../examples/full-paper/README.md)所列的本地引擎和后端。
打开 `work/manuscript-demo/review/report.html`。现有案例均为合成输入、MIT 授权，
候选结果由维护者编写。真实案例按[贡献验收清单](case-contributions_CN.md)准备；
衡量模型表现从[配对评测试运行](pilot_CN.md)开始。

## 从导出案例开始

已安装包可[导出六类案例](examples-export_CN.md)，无需仓库源码或可选依赖。
打开离线操作页，核验初始字节，再另建候选副本。维护者答案不能进入盲评会话。
[文档索引](README.md)。
