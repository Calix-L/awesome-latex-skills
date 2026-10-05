<picture>
  <source media="(prefers-color-scheme: dark) and (max-width: 600px)" srcset="./assets/cover-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="./assets/cover-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="./assets/cover-dark.svg">
  <img src="./assets/cover-light.svg" alt="awesome-latex-skills — The manuscript toolkit. Repair, polish, format, read, recover." width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-64665f?style=flat-square&amp;labelColor=242622" alt="MIT license"></a>
  <a href="https://github.com/Calix-L/awesome-latex-skills/releases"><img src="https://img.shields.io/badge/release-1.22.0-537b55?style=flat-square&amp;labelColor=242622" alt="Release 1.22.0"></a>
</p>

<p align="center">五个专注于论文工作的 Agent Skills：修复编译、润色表达、转换格式、阅读论文、恢复源码。</p>

<div align="center">

[技能](#skills) &nbsp; / &nbsp; [安装](#quick-start) &nbsp; / &nbsp; [示例](#examples) &nbsp; / &nbsp; [文档](./docs/README.md) &nbsp; / &nbsp; [问答](#faq)

<sub>[English](./README.md) / **简体中文**</sub>

</div>

<br>

<a id="skills"></a>

## 01 / 选择你的技能

从当前需要解决的问题开始。每个入口都包含工作流、参考资料和验证要求。

| Skill | 用途与交付 |
| :--- | :--- |
| **[latex-rescue](./latex-rescue/SKILL.md)**<br><sub>01 / 修复</sub> | 排查编译错误，以最小改动修复源码，报告编译结果与剩余问题。 |
| **[latex-polish](./latex-polish/SKILL.md)**<br><sub>02 / 润色</sub> | 改善学术表达，保留论断与数值；支持轻度、中度、严格三档。 |
| **[latex-fmt](./latex-fmt/SKILL.md)**<br><sub>03 / 格式</sub> | 迁移投稿模板，按官方要求核对版式，说明通过、失败及未验证项。 |
| **[paper-read](./paper-read/SKILL.md)**<br><sub>04 / 阅读</sub> | 从速读到深度分析，将论断与证据对应到原文章节、图表和公式。 |
| **[pdf2tex](./pdf2tex/SKILL.md)**<br><sub>05 / 恢复</sub> | 从 PDF 重建可编辑 LaTeX，标记有歧义的内容并与原稿核对。 |

<details>
<summary>会议与期刊指导</summary>

NeurIPS · ICML · CVPR · ACL/EMNLP · ICLR · ECCV · AAAI · TMLR · IEEE ·
Nature · Science · COLING · KDD · SIGIR · Interspeech。

[会议与期刊指南](./latex-fmt/references/templates/venue-guide.md)指向官方要求。
使用前核验目标年份、赛道、文章类型和投稿阶段；官方模板包需另行获取。

</details>

<a id="quick-start"></a>

## 02 / 安装与使用

Python **3.10+** · Windows / macOS / Linux · 无需第三方安装依赖

```sh
git clone https://github.com/Calix-L/awesome-latex-skills.git
cd awesome-latex-skills
python -m pip install .
als install --agent claude
```

使用 **Codex** 时，将最后一行改为 `als install --agent codex`。
如果系统的 Python 命令是 `python3`，替换命令名即可。

[包安装与可选依赖](./docs/install.md)。也可以直接从源码运行，
用 `python scripts/als.py` 代替 `als`，参数相同。

[中文命令行速查](./docs/cli_CN.md)：项目构建、配置覆盖、特殊文件名与 JSON 证据。

**调用：** Claude Code 使用 `/latex-rescue`；Codex 使用 `$latex-rescue`。也可以直接描述任务。

**先得到一个可审查的结果。** [五类任务指南](./docs/tasks_CN.md)写明命令、
预期输出和下一步核验。

| 从这里开始 | 可以审查什么 |
| :--- | :--- |
| **[导出可编辑案例](./docs/examples-export_CN.md)** | 从已安装 wheel 复制六类案例，附离线操作页和源码指纹 |
| **[体检自己的项目](./docs/project_CN.md#project-aware-prerequisites)** | 实际配置、本地工具、缺失资源与源码位置 |
| **[检查论文修改](./docs/tasks_CN.md#polish)** | 原稿/候选差异、作者决策与保留的构建证据 |
| **[试跑完整案例](./examples/full-paper/README.md)** | 多文件中英文论文与离线审查报告 |

先复制到自己的目录；导出无需 TeX 或 PDF 库：

```sh
als examples export --case full-paper --output ../my-example --language zh
als verify example ../my-example
```

打开 `../my-example/report.html`，按操作页继续。保留初始导出，另建候选副本再编辑。
[六类案例与实际依赖](./docs/examples-export_CN.md)。

需要衡量技能质量？从 [12 次运行的评测试运行](./docs/pilot_CN.md)开始。
集成报告前，阅读[测试环境与接口约定](./docs/compatibility.md#中文说明)。

<details>
<summary><strong>只安装一个 Skill、预览改动、指定安装目录</strong></summary>

```sh
# 先预览，不写入任何文件
python scripts/install.py --agent codex --skill latex-rescue --dry-run

# 只安装指定 Skill；重复 --skill 可选择多个
python scripts/install.py --agent codex --skill latex-rescue

# 使用自己的 Skills 目录
python scripts/install.py --dest "path/to/skills" --skill paper-read
```

每次安装都会包含入口、参考文件、脚本和 Agent 元数据。
默认目录为 Claude Code 的 `~/.claude/skills/` 和 Codex 的 `$CODEX_HOME/skills/`
（未设置时为 `~/.codex/skills/`）。已有内容相同时保持原样；普通安装不会覆盖不同的内容。

</details>

<details>
<summary><strong>安全更新已安装的技能</strong></summary>

```sh
git pull --ff-only
python scripts/install.py --agent codex --update --dry-run
python scripts/install.py --agent codex --update
```

新安装会记录各文件的 SHA-256。`--update` 只替换与安装记录完全一致的技能；
本地改动、新增或删除的文件都会阻止整批更新，不提供强制覆盖选项。
更新失败或被中断时尝试恢复旧目录；恢复失败时保留备份并报告位置。

没有安装记录的手工复制版本，只有与当前源码完全相同时才能被接管
（`adopt`）。不同的旧版本需先备份并移走，或选择新目录。`--dry-run`
不会写入文件或安装记录。Claude Code 使用 `--agent claude`。

同一技能目录的写入使用互斥锁；第二个安装进程会停止并报告锁的位置，避免并发
更新相互覆盖。进程异常终止后，确认原安装器已停止，再手动移除
`.awesome-latex-skills.lock`；工具不会自动让仍在使用的锁过期。

</details>

<details>
<summary><strong>在其他 Agent 或纯聊天界面中使用</strong></summary>

让 Agent 能访问完整 Skill 目录，然后输入：

```text
Read awesome-latex-skills/latex-rescue/SKILL.md and follow its workflow.
```

在纯聊天界面中，需要提供入口及当前任务用到的参考文件。只粘贴 `SKILL.md`
会缺少配套知识。本地编辑和编译能力取决于 Agent 已配置的工具。
`agents/config.yaml` 是旧版集成提示，不是所有平台通用的配置 API。

</details>

<a id="examples"></a>

## 03 / 实际示例

**完整论文工作流。** 检查根文件与资源依赖，按项目配置构建，再集中审查源码
差异、实际日志和 PDF 页面。

```sh
python -m pip install ".[pdf]"
als project check examples/full-paper/after --bundle work/project-inspection --html-language zh
als verify inspection work/project-inspection
als paper --output work/full-paper-run --language zh
```

[查看多文件中英文案例](./examples/full-paper/README.md)：章节、参考文献、本地样式、
合并表头、多面板图及附录。原稿构建失败，修复后必须真实编译通过；打开
`work/full-paper-run/review/report.html`，查看差异、构建证据、页面预览，以及仍需
作者决定的计时协议。

[项目体检与配置](./docs/project_CN.md) · [统一修改审查](./docs/review_CN.md) · [公式变化核对](./docs/math-review_CN.md)

打开 `work/project-inspection/report.html`，查看带源码位置的问题、资源依赖与处理建议。
分享整个目录即可保留 JSON 和校验清单；完整案例也会整体导出原稿和修复稿的检查报告。

| 需求 | 入口 |
|---|---|
| 阅读静态问题与处理建议 | `project-inspection/report.html` |
| 处理大文件、评审备注与读取变化 | [输入大小与重试](./docs/input-limits_CN.md) |
| 检查文档类、宏包选项与后端声明 | [加载选项](./docs/package-options_CN.md) |
| 检查数据库、手写文献条目与重复键 | [参考文献指南](./docs/bibliography_CN.md) |
| 定位常用引用命令、核对引用键变化 | [文献引用检查](./docs/citations_CN.md) |
| 定位重复标签、缺失目标与范围端点调换 | [交叉引用检查](./docs/cross-references_CN.md) |
| 对照公式内容与运算符变化 | [公式审查](./docs/math-review_CN.md) |
| 监测构建中的指定文献库与样式 | [构建输入监测](./docs/build-inputs_CN.md) |
| 核验收到的检查报告 | `als verify inspection path/to/report-directory` |
| 审阅源码修改与实际 PDF 页面 | `full-paper-run/review/report.html` |

中文审阅页集中展示改动文件、数值/引用/公式变化、待作者确认项和构建状态；
可展开差异与证据文件，不必先阅读完整 JSON。界面支持窄屏与深色模式。

检查器区分注释、转义反斜杠与原样文本，保留真实依赖及源码位置。未闭合的代码
示例会明确提示；自动主文件选择也记录全部已读取文件的指纹。详见
[源码扫描范围](./docs/project_CN.md#注释与代码示例不会混入依赖)。

**交付后仍可核验。** 新审阅目录会记录报告、差异、日志、PDF 与页面图片的校验值。
转移目录或下载完整发布资产后，可离线检查：

```sh
als verify review work/full-paper-run/review
als verify inspection work/full-paper-run/inspection-after
als verify release path/to/downloaded-release-assets
```

[离线校验指南](./docs/verification_CN.md)。检查确认文件与清单一致；发布者身份和
科学内容正确性仍需分别确认。

**实际构建失败 → 真实编译的修复稿**

<p align="center">
  <img src="./assets/previews/full-paper-before.svg" alt="来自实际日志的错误摘录：methods.tex 第 13 行缺少图像，并展示原始面板宽度" width="400">
  <img src="./assets/previews/full-paper-after.png" alt="真实编译的英文修复稿局部，包含公式、多面板图、合并表头及保留的演示数值" width="400">
</p>

完整自制案例的原稿日志摘录与修复稿 PDF 局部。[编译与渲染来源](./assets/previews/README.md)。

<details>
<summary><strong>中文伴随稿：真实 XeLaTeX 编译结果</strong></summary>

<img src="./assets/previews/full-paper-chinese.png" alt="真实编译的中文伴随稿，保留原始数值、演示流程图与参考文献" width="540">

本案例显式指定 Noto Serif CJK SC；实际论文应保留其模板的字体设置。
[完整源码与验证步骤](./examples/full-paper/README.md)。

</details>

<br>

<img src="./assets/workflow-preview.svg" alt="五个自制案例的可视化概览：修复语法、保留论断、局部宽度、冲突证据与 PDF 表格恢复" width="100%">

每个案例都提供原始输入、候选结果、修改说明和可运行的核验步骤。
候选结果由维护者编写；尚未测量模型使用技能前后的质量提升。

| 案例 | 查看完整结果 | 核验重点 |
| :--- | :--- | :--- |
| **编译修复** | [错误源码 → 最小修复](./examples/rescue/README.md) | 新构建日志、原始数值、保留的未知引用 |
| **学术润色** | [语法修改 → 论断保留](./examples/polish/README.md) | 源码差异、能力与不确定性、技术组件与否定结论 |
| **版式调整** | [双栏溢出 → 局部宽度](./examples/fmt/README.md) | 实际编译、溢出检查和页面预览 |
| **论文阅读** | [论文片段 → 证据地图](./examples/read/README.md) | 冲突结果、来源位置与缺失的实验协议 |
| **PDF 恢复** | [双页 PDF → 可编辑 TeX](./examples/pdf2tex/README.md) | 字符证据、合并表头、空白单元格与歧义 |

```sh
python -m pip install -r pdf2tex/requirements.txt
python scripts/als.py examples run --output work/example-run
```

需要本地 TeX 引擎。[案例说明](./examples/README.md)介绍无 TeX 时的显式未验证模式，
以及 CI 编译证据的下载方式。

<details>
<summary><strong>实际 PDF 细节：编译版式与原始表格</strong></summary>

| 真实编译后的局部版式 | 原始 PDF 中的表格证据 |
| :---: | :---: |
| <img src="./assets/previews/fmt-column.png" alt="真实编译的栏内图、表格与已解析引用" width="270"> | <img src="./assets/previews/pdf-table.png" alt="原始 PDF 的合并表头、小数精度和空白单元格" width="480"> |

来自自制案例的 PDF 局部渲染。[来源与渲染记录](./assets/previews/README.md)。

</details>

<details>
<summary><strong>展开查看单个修改示例</strong></summary>

### 修复明确的语法错误

```diff
- \textbff{Results}
+ \textbf{Results}

- \begin{figure} ... \end{table}
+ \begin{figure} ... \end{figure}
```

已知语法错误可以直接修复；有歧义的公式、表格数据、引用键和标签仍需作者判断。
编译成功无法证明修改符合作者原意。

### 润色表达，保留论断

```diff
- The model can achieves good performance on the dataset.
+ The model can achieve good performance on the dataset.

- According to the experiment, the accuracy is improved by 3.2%.
+ The experiments show a 3.2% improvement in accuracy.
```

保留术语、数值、不确定性以及“3.2%”原有含义，不会擅自把相对百分比改为百分点。

</details>

<details>
<summary><strong>统一入口与可复现的质量流程</strong></summary>

```sh
python scripts/als.py --json doctor
python scripts/als.py evaluate validate
python scripts/als.py sources
python scripts/als.py release --output dist/1.22.0
```

[CLI 与 JSON 报告](./docs/cli.md) · [中文评测指南](./docs/evaluation_CN.md) ·
[来源维护登记](./maintenance/README.md) · [版本发布与迁移](./docs/releases.md)

评测准备器只向独立会话提供原始输入和所选技能；评分区分有限的字面检查和附证据的
人工审查，样例不会被包装成模型的前后对照成绩。
多轮运行器默认准备 60 个盲测任务，保留失败及未运行记录。也可以先做两个任务的试运行：

```sh
als benchmark prepare --case polish-scope --trials 1 --output evaluation-runs/pilot-01
```

[配置外部运行程序](./docs/evaluation_CN.md#连接你实际使用的运行程序)，自动保留实际耗时、
原始日志与全部提交文件的校验值；空白人工审查表不会被计为已评分。模型归属与账单
费用仍需真实证据，当前不宣称已测得质量提升。

</details>

<details>
<summary><strong>更多请求：投稿格式、论文阅读与 PDF 恢复</strong></summary>

**转换投稿格式**

```text
将这个项目改为 NeurIPS 2026 主赛道匿名评审格式。
使用官方模板，保留科学内容，并报告无法验证的要求。
```

**带着问题读论文**

```text
用 deep 模式阅读这篇论文。解释主要论断、支持证据、关键假设，
以及复现结果需要哪些条件。注明对应章节、图表或公式的位置。
```

**恢复可编辑源码**

```text
把这份有文本层的 PDF 重建为 LaTeX。保留章节顺序，
标记有歧义的符号、合并表格单元格和缺失素材。
明确说明是否完成编译和视觉核对。
```

</details>

<details>
<summary><strong>先运行一个自包含排版示例</strong></summary>

将 [layout-example.tex](./latex-fmt/assets/layout-example.tex) 复制到新的工作目录，
用可用的 TeX 引擎编译两次。示例包含图形面板、表格及公式／图／表交叉引用，
不依赖外部图片、字体或参考文献。把 `twocolumn` 改为 `onecolumn`，即可核对
相同内容在两种栏宽下的效果。只安装 `latex-fmt` 也会包含这个示例。

CI 使用 pdfLaTeX、XeLaTeX、LuaLaTeX 检查两种模式。它用于演示排版；投稿仍需
使用目标会议或期刊的官方模板。

</details>

<a id="workflows"></a>

## 04 / 从草稿到交付

| 当前任务 | 建议顺序 | 完成前核对 |
|---|---|---|
| 草稿编译失败 | `latex-rescue` | 最终日志、剩余警告、渲染后的 PDF |
| 修改论文表达 | `latex-polish` → `latex-rescue` | 含义保持不变的 diff 和编译结果 |
| 转换投稿目标 | `latex-fmt` → `latex-rescue` | 官方要求、正文页数边界、匿名信息 |
| 原始源码丢失 | `pdf2tex` → `latex-rescue` | 内容完整性、公式、表格、视觉对照 |
| 阅读相关工作 | `paper-read` | 论断与证据的对应关系、原文位置 |

每一步也可以独立使用。格式转换流程不会自动上传或提交论文。

## 05 / 检查本地环境

Skill 提供指导，提取和编译由外部工具执行。开始处理本地项目之前，可运行只读检查：

```sh
python scripts/doctor.py --skill latex-rescue --engine pdflatex

# 使用项目实际的引擎和参考文献后端
python scripts/doctor.py --skill latex-fmt --engine xelatex --backend biber

# JSON 报告；返回码 1 表示必需的本地前提不满足
python scripts/doctor.py --skill pdf2tex --json
```

| 任务 | 本地前提 | 不满足时 |
|---|---|---|
| 编译或验证格式 | 项目的 TeX 引擎、已选择的参考文献后端 | 可根据提供的日志诊断；编译状态标记为未验证 |
| 润色粘贴文本／阅读已提供文本 | 不需要 TeX 编译器 | 可继续处理文本；PDF 验证是另一步 |
| 提取有文本层的 PDF | PyMuPDF：`python -m pip install -r pdf2tex/requirements.txt` | 提供提取文本，或配置提取工具 |
| 恢复扫描 PDF | 单独的 OCR 工作流 | 普通文本提取无法完成 |
| 应用投稿规则 | 官方模板及作者指南 | 尚未确定的规则标记为未验证 |

诊断命令报告正在使用的 Python、PyMuPDF 版本、实际导入路径及建议处理步骤，
区分未安装、版本不兼容、导入失败和同名模块遮蔽。它不安装软件、不编译文档，
也不认证稿件已经满足投稿要求。

<details>
<summary><strong>执行一次新构建，并保留验证证据</strong></summary>

对常规根文档，在仓库根目录运行：

```sh
python latex-rescue/scripts/check_build.py path/to/paper.tex --output fresh-build
python latex-rescue/scripts/check_build.py path/to/paper.tex --output fresh-bib-build --engine xelatex --backend biber
python latex-rescue/scripts/check_build.py path/to/paper.tex --output final-check --until-stable --require-resolved
```

选择项目实际的引擎和参考文献后端；不需要后端时省略 `--backend`。
目标必须是新目录。工具保存每次运行的日志、终端输出、辅助文件、PDF 和
`build-report.json`，记录退出码与逐步诊断；参考文献后端失败时直接使用后端日志。
实际记录的本地章节、样式和图片附有逐轮指纹，可发现观察之间的文件变化；这不是冻结的项目快照。
工具关闭 shell escape，遇到失败或超时
即停止。输出名默认沿用根文件名，并支持常规嵌套章节。
`--until-stable` 在限定次数内检查辅助文件是否稳定；`--require-resolved` 会将
已识别的未解析引用或重跑请求视为检查失败。不加该选项时，构建成功仍可能存在
未解析引用或排版警告。

只安装 `latex-rescue` 也会包含这个独立脚本。自定义构建流程应继续使用项目
原有命令。参数和报告的适用范围见[构建指南](./latex-rescue/references/build-check.md)。

</details>

<details>
<summary><strong>先提取 PDF 证据，再重建 LaTeX</strong></summary>

在仓库根目录运行：

```sh
python -m pip install -r pdf2tex/requirements.txt
python pdf2tex/scripts/extract_pdf.py paper.pdf --output extraction --pages 1-3,5 --images --render
```

不加 `--pages` 时提取全部页面；`--images` 可选。目标必须是新目录。
输出包含按页分隔的 UTF-8 文本、布局／字体／页码／元数据 JSON，以及可选的嵌入图片。
`--render` 额外保存所选页面的 PNG 预览，默认 144 DPI；`--dpi` 可选 72–300，
每页最多 2000 万像素，便于核对公式、矢量图和完整图组。
打开 `extraction/report.html` 即可离线并排核对页面与提取文本，查看页码导航、覆盖范围、
警告和来源信息；报告适配窄屏与深色模式，分享时保留整个输出目录。
检查上下标或细小符号时可加 `--chars`，保留逐字符原点和边界框，同时兼容已有的
文本片段字段。页面几何信息及旋转矩阵可用于将文本坐标对应到预览，详见
[字符与坐标说明](./pdf2tex/references/pdf-extraction-guide.md#character-detail-and-page-coordinates)。
工具保留原始 PDF，输入指纹发生变化时停止发布；标记无文本页面，记录重复图片位置和独立透明蒙版。

这一步不执行 OCR，也不自动生成 LaTeX。多栏顺序、公式、表格与完整图组仍需
根据原始页面核对。详见 [PDF 提取指南](./pdf2tex/references/pdf-extraction-guide.md)。

</details>

<a id="faq"></a>

## 06 / 常见问题

<details>
<summary><strong>安装 Skill 会同时安装 LaTeX 或模型吗？</strong></summary>

不会。安装器只复制技能文件。使用你已配置的 AI Agent 和 TeX 发行版；
环境诊断命令会报告缺少的本地工具。

</details>

<details>
<summary><strong>可以配合 Overleaf 使用吗？</strong></summary>

可以提供错误日志和相关源码进行诊断，也可以导出完整项目进行本地验证。
Agent 应明确区分“提出修复方案”和“修复后已经重新编译”。

</details>

<details>
<summary><strong>PDF 恢复能精确还原原始源码吗？</strong></summary>

不能。PDF 已丢失宏和源码结构。恢复的目标是内容忠实、可编辑，并标出不确定之处。
公式、表格、引用和排版需要与原始 PDF 对照；扫描页面需要先做 OCR。

</details>

<details>
<summary><strong>CI 通过能证明什么？</strong></summary>

CI 验证元数据、包内资源与文档链接、SVG 素材、安全安装与更新、真实 PDF 提取、依赖诊断报告、
样例的数据保留、新构建的证据，以及真实 TeX／BibTeX／Biber 编译。跨平台检查覆盖 Windows、macOS、Linux，
使用 Python 3.10 和 3.13。它不认证 AI 的实际编辑质量，也不保证论文符合当前
投稿规则。详见[测试说明](./tests/README.md)。

</details>

## 一起完善

发现规则不准确、缺少错误模式或安装失败？欢迎提交
[Issue](https://github.com/Calix-L/awesome-latex-skills/issues/new/choose) 或聚焦单个问题的 PR。
请附最小示例、预期行为；涉及会议规则时，注明官方来源。

[贡献指南](./CONTRIBUTING.md) · [测试说明](./tests/README.md) ·
[更新日志](./CHANGELOG.md) · [MIT 许可证](./LICENSE)

<div align="center">

<br>

<sub>为研究者提供有用的辅助，以及可以亲自审查的修改。</sub>

</div>
