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

Example export adds schema-1 `worked_example_export` receipts and
`worked_example_integrity` manifests. `examples list` adds `export_cases` and
preserves its original five entries. Existing run/build/review report schemas
are unchanged. Source-copy hashes and language-specific guides are initial
artifact evidence, not build or model-quality results.

## Located formula review / 带位置的公式审查

Schema-1 review adds `math_environment_inventory`, `math_environment_scope` and
optional `content_audit[].math_environments`; existing fields and the direct
three-counter `content_tokens` helper remain unchanged. Old reports without the
additive inventory still render. Source-only review needs only the standard
library. See [coverage](math-review.md) / [中文范围](math-review_CN.md).

## Explicit build inputs / 显式构建输入

Schema-3 build adds `input_tracking.watched_inputs` (empty by default) and
`preflight`/backend observations within existing `local_inputs` for selected
files. The direct build helper adds only a trailing optional `watch_inputs`.
Schema-1 review build summaries add `watched_inputs`; missing legacy selection
metadata means no explicit guard. No configuration schema change or inferred
backend-consumption record. [English](build-inputs.md) / [中文](build-inputs_CN.md).

## Citation inventories / 文献引用清单

Schema-1 inspection adds a flat `citation_inventory`; schema-1 review adds
`citation_inventory.before/after`. Rows contain literal `key`, `command`, `file`,
command-opening `line`, 1-based argument `group` and Boolean `starred`. Old reports
without the field still render. Existing `reference_keys` counters now include
common natbib/biblatex commands and every complete multicite group.
`citation-unverified` reports incomplete or special syntax; partial inventories
never imply exhaustive coverage. Configuration/build schemas stay unchanged.
[English](citations.md) / [中文](citations_CN.md).

## Cross-reference inventories / 交叉引用清单

Schema-1 inspection adds `label_inventory` and `reference_inventory`; review adds
`before/after` dictionaries under both names. Label rows keep `file/line/key`;
inspection adds `definition_count`. Reference rows keep `file/line/key/command`,
1-based argument `group` and Boolean `starred`; inspection adds `resolution`
(missing/defined/ambiguous), `definition_count` and `first_definition` (null or
file/line). Review inventories intentionally do not assert root resolution.
Old reports without these fields remain renderable. Range content counters retain
argument role as `(command, group, key)`; ordinary keys keep `(command, key)`.
Repeated-label diagnostics now occur at each later definition and name the first
location. Unsupported arguments produce `reference-unverified` instead of guessed
targets. No configuration/build schema change. [Guide](cross-references.md).

## Manual bibliography inventory / 手写文献清单

Schema-1 inspection adds `bibitem_inventory` rows with `file/line/key` and manual
`definition_count`. Schema-1 review adds raw `bibitem_inventory.before/after`
without counts or root resolution. Old reports without the fields still render.
Definition keys enter `reference_keys` as `(bibitem, key)`; command roles remain
distinct. `bibitem-unverified` covers unsupported arguments,
`duplicate-bibitem-key` locates later manual definitions, and
`bibliography-key-overlap` marks database/manual overlap unverified. Existing
configuration/build schemas and default backend selection remain unchanged.
[Guide](bibliography.md#manual-bibliographies).

## Loader option inventory / 加载选项清单

Schema-1 inspection adds `package_inventory`; review adds
`package_inventory.before/after`. Rows retain `file/line/command/name/options`.
Direct biblatex loader rows add `backend_options` and `backend_options_complete`,
which describe the literal argument rather than effective runtime configuration.
Legacy HTML without the fields remains supported. Configuration schema 1 now
requires an integer, rejecting Boolean/float/string lookalikes. Build and
configuration schema numbers and backend defaults remain unchanged.
[Guide](package-options.md).

## Bounded I/O / 有界读取

No report schema changes. Shared JSON readers/writers enforce 16 MiB; notes enforce
2,000,000 bytes; shared hashing and evidence copying enforce 512 MiB per file.
Review inventory enforces the existing sealed-artifact 2 GiB total per project
side, before hashing and again on actual snapshot sizes. Regular-file checks
reject special files/symlinks; descriptor/path fingerprints check observed changes.
Normal inputs and legacy report rendering remain compatible; oversized or changing
inputs now return an error before report publication. See [English](input-limits.md)
and [中文](input-limits_CN.md). These checks are observations, not file locks.

## Internal dependency paths and prepared BibTeX inputs

Configuration/inspection/review/build schema numbers remain unchanged. Literal
internal dot/parent dependencies normalize to canonical evidence names without
relaxing configured main, watched selector or manifest paths. Bibliography steps
optionally add structured `prepared_inputs` with file/hash/bytes/kind metadata;
resource rows bind an original path, AUX rows record their initial AUX hash.
Review retains these files and rechecks resource originals inside its project.
Reports without this optional field retain previous behavior.
[English](relative-paths.md) / [中文](relative-paths_CN.md).

## Dependency argument inventory / 依赖参数清单

Schema-1 inspection adds optional `dependency_inventory`; review adds
`dependency_inventory.before/after`. Rows contain `file/line/command/value/options/
starred/supported/issue`. Bilingual HTML renders these observations independently
of resolved dependencies; legacy reports without this field remain supported.
Malformed dependency syntax now produces located unverified observations rather
than phantom body keys. CLI/configuration/build schemas and exit semantics stay
unchanged. [English](dependency-arguments.md) / [中文](dependency-arguments_CN.md).

## Located math pairs / 定界符公式位置

Schema-1 review adds optional `math_delimiter_inventory.before/after` and
`math_delimiter_scope`; rows contain file/delimiter/closing/mode/line/end_line/content.
Existing `content_audit[].simple_math`, schemas and CLI exit meanings remain.
Adjacent inline pairs are now correctly separated. Unclosed/conflicting or
group-dependent spans become located source issues, including unchanged files,
and supply no complete formula values. Mixed/nested modes are unverified rather
than judged invalid; legacy HTML without the fields remains supported.
[English](math-review.md) / [中文](math-review_CN.md).
