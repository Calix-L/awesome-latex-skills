# Supported checks and interface expectations

[简体中文](#中文说明) · [Installation](install.md) · [CLI](cli.md)

## Evidence matrix

| Area | Current verification | What remains environment-specific |
|---|---|---|
| Portable Python helpers and package first use | CI on Windows, macOS and Ubuntu, Python 3.10 and 3.13; original wheel and rebuilt source distribution | Other Python versions, OS versions and local agent integrations |
| Native TeX | Ubuntu CI with pdfLaTeX, XeLaTeX, LuaLaTeX, BibTeX and Biber regressions | Windows/macOS native TeX, arbitrary templates/packages and fonts |
| PDF extraction | Supported PyMuPDF range `>=1.24.10,<2`; minimum version tested on Ubuntu/Python 3.10 | OCR, exact source recovery and untested PDF structures |
| Skills | Literal regression tasks, synthetic examples and attributable evaluation tooling | Independent model efficacy, semantic fidelity and venue compliance |

Use the successful CI run for the exact commit/release you consume. A matrix
entry describes exercised checks, not a guarantee for every project on that OS.
`doctor --project ...` connects local probes with static project evidence; it
does not build the document or test whether an agent loaded a skill correctly.

## Machine interfaces

- `als --json COMMAND` keeps the schema-1 envelope: version, command, status,
  exit code, result, invocation, stdout/stderr and evidence paths. The envelope's
  schema does not replace the nested helper report's schema or kind.
- Current doctor schema 1 adds `project` and combined `status` only in project
  mode. Existing environment-only calls remain supported. Unknown engine/backend
  selections stay unresolved; project mode does not default to pdfLaTeX.
- Readers should tolerate additional object fields, but inspect schema/kind,
  required fields, status and exit code before using evidence. Do not interpret
  null as zero, missing as passed, or `needs-review` as a successful native build.
- Diagnostic codes and file/line locations are suitable for routing findings.
  Human wording and translated headings may improve between releases. JSON and
  native/source diagnostics retain their original text when the UI is Chinese.
- Report artifacts are immutable deliveries. Verification covers supplied
  bytes/inventories, not publisher identity, current source correspondence or
  scientific truth. Rebuild/reinspect into a new output directory after changes.

Release notes should identify changed meanings, arguments, required fields or
exit behavior, not only new files. Breaking interface changes require explicit
migration guidance and a major version increment. Additional fields/options and
new task recipes can be released as compatible minor updates; fixes retain
documented existing interfaces. Record the actual version and command in bug
reports along with sanitized source and native logs.

<a id="中文说明"></a>

## 中文说明

可移植脚本和包首次使用在 Windows、macOS、Ubuntu 的 Python 3.10/3.13 上检查；
本地 TeX 构建在 Ubuntu CI 中验证。其他系统的本地 TeX、任意模板和字体仍取决于
实际环境。测试矩阵描述已执行的检查，不能保证所有论文通过。技能的合成回归和
工具测试不能替代独立模型评测、语义审查或投稿合规确认。

JSON 外层 schema 与内部报告 schema/kind 分别检查。读取方容忍新增字段，
但必须核对版本、必需字段、状态和退出码。`doctor --project` 才增加 `project`
和综合 `status`；未选引擎/后端保持未选择。环境检查通过和 `needs-review` 都
不能当成实际编译通过。空值不是零分，缺失不算通过。

问题代码和文件/行号用于定位；人类可读措辞可以改进。报告是一次性产物，源码
变化后应写入新目录重新检查。破坏接口的版本需要明确迁移指南并提升主版本；
兼容新增选项/字段用次版本，修复保留现有约定。报告问题时提供实际版本、命令、
脱敏源码和真实日志。
