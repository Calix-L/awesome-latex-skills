# 检查发布包、审阅目录与项目检查报告

离线校验命令只需要 Python 标准库，不访问网络、不解压或执行压缩条目，
也不修改待检查目录。通过只表示文件与所提供清单一致，不能认证发布者，
也不能证明科学内容正确。

## 发布资产

将同一个 Release 的全部资产下载到独立目录并保留原名：完整源码 ZIP、
五个 Skill ZIP、`release-manifest.json` 和 `SHA256SUMS`。如包含 wheel
和源码发行包，也必须同时保留它们。

```sh
als verify release path/to/release-assets
als --json verify release path/to/release-assets
# 未安装 CLI 时，从可信源码目录运行
python scripts/als.py verify release path/to/release-assets
```

检查文件大小、SHA-256、清单覆盖、ZIP 条目和源码指纹、版本、CRC，以及
wheel/源码发行包与发布源码的一致性，不安装包或运行脚本。不要混用版本、
重命名资产或在资产目录保存说明、校验结果、解压后的项目；额外文件也会失败。
缺失或损坏时请重新下载，不要修改清单使它“通过”。来源仍需另行核对仓库、
版本标签、CI 和发布者。

## 审阅目录

新审阅目录的 `integrity.json` 覆盖 HTML、JSON、源码差异、日志、成功 PDF、
页面图片等全部文件，清单本身除外。转移后直接检查，无需原论文目录：

```sh
als verify review path/to/review-bundle
als --json verify review path/to/review-bundle
```

缺失、变化、新增文件都会被报告，请保持整个目录完整，将自己的批注和检查
输出保存在其他位置。清单不能自证可信：能同时修改清单与文件的人仍可生成
匹配结果。

旧目录没有完整清单时显示“未验证”，退出码为 `1`。已有的 `retained_files`
指纹仍被检查，证据变化会失败；但不能据此确认旧 HTML、JSON、差异文件。
用当前工具重新生成审阅目录即可得到完整清单，校验工具不会自动补写或覆盖。

## 项目检查报告目录

```sh
als project check path/to/paper --bundle work/inspection-01 --html-language zh
als verify inspection work/inspection-01
```

目录内包含 `inspection.json`、`report.html` 和 `integrity.json`，清单必须恰好覆盖
两份报告。完整转移后可直接校验，不需要原论文或原导出路径；报告不包含源码，
校验也不会读取源码。缺失、变化、额外文件均失败。无效或缺失清单返回 `2`，
单独导出的 HTML/JSON 不能作为完整报告目录校验。

报告完整性与检查结果各自独立：包含 `blocked` 问题的报告仍可校验通过。这不代表
当前论文与报告一致，也不能证明编译成功。详见
[整体报告导出](project_CN.md#整体导出与分享检查报告)。

## 结果与限制

| 退出码 | 含义 |
|---|---|
| `0` | 完整性检查通过，`verified` |
| `1` | 文件不一致或旧目录覆盖不完整，查看 `failed` / `unverified` 问题 |
| `2` | 清单无效、路径不安全、参数或顶层清单超出范围 |

异常压缩结构作为对应文件的 `invalid-archive` 返回 `1`，无效顶层清单返回 `2`。
拒绝符号链接、越界/非规范路径、重复/大小写冲突、加密 ZIP、链接或特殊条目、
分卷及 ZIP64 中央目录元数据；支持范围内的普通 ZIP64 成员头仍可读取。

限制为 20,000 个文件/条目、单文件/成员 512 MiB、每个清单或压缩包合计
2 GiB、元数据 16 MiB。ZIP 中央目录在解析条目前检查，gzip/tar 读取也有限制。
检查时请保持输入不变。工具不会编译、安装软件、执行 OCR、调用模型或判断投稿质量。

详见[英文指南](verification.md)、[审阅流程](review_CN.md)和[版本迁移](releases.md)。
