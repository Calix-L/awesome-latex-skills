<div align="center">

<img src="./assets/banner.svg" alt="awesome-latex-skills" width="100%">

<br>

### 每个研究者都经历过这些时刻。

> *凌晨 2 点，47 个编译错误。审稿人一句"English needs improvement。"*
> *CVPR 被拒，周五前要改成 ICML 格式。*

**awesome-latex-skills** 让任何 AI 拥有处理这些问题的领域专家能力——结构化工作流、精选知识库、严格防护栏，这是普通 Prompt 做不到的。

<br>

`47 errors → 0` &nbsp;·&nbsp; `Chinglish → publication-ready` &nbsp;·&nbsp; `CVPR → NeurIPS` &nbsp;·&nbsp; `50 pages → structured notes`

<br>

<a href="https://github.com/Calix-L/awesome-latex-skills/actions"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="CI"></a>
<img src="https://img.shields.io/badge/skills-5-blue" alt="5 skills">
<img src="https://img.shields.io/badge/tests-162_passing-brightgreen" alt="162 tests">
<img src="https://img.shields.io/github/stars/Calix-L/awesome-latex-skills?style=social" alt="Stars">
<img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">

</div>

---

**[技能一览](#技能一览) · [效果演示](#效果演示) · [组合工作流](#组合工作流) · [快速上手](#快速上手) · [平台兼容](#平台兼容) · [更新日志](./CHANGELOG.md) · [参与贡献](./CONTRIBUTING.md)**

[English](./README.md)

---

## 技能一览

<table>
<tr>
<td width="54" align="center">:ambulance:</td>
<td width="120"><strong><a href="./latex-rescue/SKILL.md">latex-rescue</a></strong></td>
<td>修复编译错误 — 80+ 自动修复模式、包冲突检测、Overleaf 支持</td>
</tr>
<tr>
<td align="center">:pencil2:</td>
<td><strong><a href="./latex-polish/SKILL.md">latex-polish</a></strong></td>
<td>润色学术写作 — 18 类中式英语纠正、100+ phrasebank 模板、3 档强度</td>
</tr>
<tr>
<td align="center">:repeat:</td>
<td><strong><a href="./latex-fmt/SKILL.md">latex-fmt</a></strong></td>
<td>会议格式转换 — NeurIPS · ICML · CVPR · ACL · ICLR · ECCV · AAAI · TMLR · IEEE · Nature · Science · COLING · KDD · SIGIR · Interspeech</td>
</tr>
<tr>
<td align="center">:book:</td>
<td><strong><a href="./paper-read/SKILL.md">paper-read</a></strong></td>
<td>论文阅读分析 — 速读 / 精读 / 深度审计，43 项评审指标，假设审计</td>
</tr>
<tr>
<td align="center">:wrench:</td>
<td><strong><a href="./pdf2tex/SKILL.md">pdf2tex</a></strong></td>
<td>PDF 逆向重建 LaTeX — 7 阶段流水线、97+ 数学符号映射、表格重建</td>
</tr>
</table>

| | | | |
|---|---|---|---|
| 80+ 错误模式 | 14 种包冲突 | 18 类中式英语 | 100+ phrasebank 模板 |
| 15 个会议规则 | 43 项评审指标 | 97+ 数学符号映射 | 15 个参考文件 |

---

## 为什么是 Skill 而不是 Prompt？

你试过让 ChatGPT 修 LaTeX。它会猜。它会漏。它还会改你的数学公式。

| 场景 | 普通 Prompt | 使用 Skill 包 |
|---|---|---|
| `\beginn{table}` | "这是个有趣的拼写错误" | 自动纠正为 `\begin{table}` |
| "According to the experiment" | 照单全收 | 标记 overuse，推荐替代表达 |
| 投稿 NeurIPS | 忘记 Broader Impact | 自动检测缺失的必填章节 |
| PDF → LaTeX | 生成乱码标记 | 7 阶段流水线 + 验证 |
| 没有 natbib 却用 `\citep{}` | 直接忽略 | 检测缺失包，自动添加 |

Skill 注入了**数百条领域专用规则**，这些规则 LLM 无法仅靠记忆可靠地调用。每个 Skill = 结构化工作流 + 领域知识 + 防护栏。同样的输入，每次都是专家级的输出。

---

## 效果演示

### :ambulance: latex-rescue — *凌晨 2 点，47 个错误，明天截稿*

```diff
- \textbff{bold}              → Undefined control sequence
+ \textbf{bold}               → 自动修复

- x_i is important            → Missing $ inserted
+ $x_i$ is important          → 自动修复

- \begin{figure}...\end{table}
+ \begin{figure}...\end{figure}  → 环境不匹配已修复
```

### :pencil2: latex-polish — *审稿人写了句"English needs improvement"*

```diff
- The model can achieves good performance on the dataset.
+ The model achieves strong performance on the benchmark.

- According to the experiment, it makes the accuracy improved by 3.2%.
+ Experiments show that the method improves accuracy by 3.2%.

- Most of methods in this research field can not achieve the same result.
+ Most methods in this field fail to match this result.
```

### :repeat: latex-fmt — *Camera-ready 格式转换，CVPR → NeurIPS*

```diff
- \documentclass{article}
+ \documentclass{neurips_2025}
- \author{Zhang et al.}
+ \author{Anonymous}
- (没有 Broader Impact 章节)
+ ⚠ NeurIPS 要求 Broader Impact — 已标记
```

### :book: paper-read — *待读列表 50 篇论文，没时间*

```diff
- "This paper proposes a novel transformer-based approach for..."
+ [速读] 目标检测 · Wang et al., CVPR 2024
+        新颖性：sparse attention 实现实时推理。结论：值得深读

- (逐字逐句读完每篇论文)
+ [深度] 核心公式：sparse attention。提升：10x 加速
+        局限：仅在 COCO 上测试。过度宣称："SOTA"（仅 0.3% 提升）
```

### :wrench: pdf2tex — *源码丢了，只剩 PDF*

```diff
- (盯着编译好的 PDF，没有任何源文件)
+ \documentclass{article}
+ \usepackage{amsmath,amssymb}
+ \section{Introduction}
+ The model achieves $F_1 = 92.3$ on the benchmark.
+ % [UNCERTAIN: math notation — verify subscripts]
```

---

## 组合工作流

多个 Skill 可以组合成流水线，覆盖真实学术场景：

| 场景 | 输入 | 执行流程 |
|---|---|---|
| 截稿赶工 | `/latex-rescue` | 崩溃 → 修复 → 编译 |
| 审稿修改 | `/latex-polish` → `/latex-fmt` | 草稿 → 润色 → 格式化 → 提交 |
| 转投改格式 | `/latex-polish` → `/latex-fmt` | CVPR 被拒 → 润色 → 转换为 ICML 格式 |
| 源码丢失 | `/pdf2tex` → `/latex-rescue` | PDF → 重建 → 修复 → 编译 |
| 新论文写作 | `/paper-read` → `/latex-polish` → `/latex-fmt` | 读论文 → 润色 → 按会议格式化 |
| Overleaf 用户 | `/latex-rescue` | 粘贴错误日志 → 获取修复建议 |

---

## 快速上手

**一条命令安装全部 5 个 Skill：**
```bash
git clone https://github.com/Calix-L/awesome-latex-skills.git && \
cp -r awesome-latex-skills/{latex-rescue,latex-polish,latex-fmt,paper-read,pdf2tex} ~/.claude/skills/
```

然后在 Claude Code 中输入 `/latex-rescue`、`/latex-polish` 等即可使用。

**只安装单个 Skill：**
```bash
cp -r awesome-latex-skills/latex-rescue ~/.claude/skills/
```

**不用 Claude Code？** 直接让 AI 读取 SKILL.md：
```
Read awesome-latex-skills/latex-rescue/SKILL.md and follow the workflow.
```

<sup>`latex-polish`、`latex-fmt`、`paper-read` 无需额外安装。`latex-rescue` 需要本地安装 LaTeX。`pdf2tex` 需要 `pip install pymupdf`。</sup>

---

## 平台兼容

| 平台 | 使用方式 |
|---|---|
| **Claude Code** | 复制到 `~/.claude/skills/`，输入 `/latex-rescue` 调用 |
| **ChatGPT / GPT-4** | 将 SKILL.md 粘贴为自定义指令或系统提示 |
| **Cursor** | 将 SKILL.md 内容添加到 `.cursor/rules/` |
| **Copilot** | 将 SKILL.md 内容添加到 `.github/copilot-instructions.md` |
| **任意 LLM** | 将 SKILL.md 作为上下文发送，然后提问 |

---

<details>
<summary>工作原理</summary>

每个 Skill 是一个自包含的目录：

```
latex-rescue/
├── SKILL.md              # 提示词 — 角色、触发器、工作流、防护栏
├── references/           # 领域知识，Agent 在每个阶段按需读取
│   ├── error-catalog.md
│   ├── package-conflicts.md
│   └── debug-workflow.md
└── agents/
    └── config.yaml       # 自动激活触发器和平台设置
```

1. 你输入 `/latex-rescue` 或说"帮我修 LaTeX 报错"
2. Agent 加载 `SKILL.md` — 获得结构化工作流 + 防护栏
3. 按阶段读取 `references/` 获取精确的领域规则
4. 同样的工作流 → 每次都是专家级的输出

</details>

---

## 许可证

MIT