# 主文件位于子目录的论文项目

[English](relative-paths.md) · [项目检查](project_CN.md) · [构建证据](build-inputs_CN.md)

项目根目录应包含主文件及其共享资源：

```text
manuscript/
├── paper/main.tex
├── shared/section.tex
├── shared/refs.bib
├── styles/local.sty
└── figures/plot.pdf
```

在 `paper/main.tex` 中，`../shared/section`、`../shared/refs`、`../styles/local`
仍是项目内部依赖。检查器以**选中主文件所在目录**为工作目录，包括被包含源码、本地
文档类或宏包里的命令；读入另一个文件不会自动切换目录。已有 `./` 写法继续支持。

```sh
als project init manuscript --main paper/main.tex --engine pdflatex --backend bibtex
als project check manuscript --bundle ../inspection --html-language zh
als verify inspection ../inspection
als build --project manuscript --output ../build --until-stable --require-resolved
```

报告保留字面请求和源码位置，解析文件及指纹使用相对项目根的规范路径，例如
`shared/section.tex`。同一文件的不同路径写法共享依赖图身份，可以提示重复输入并
发现循环。`includeonly` 仍比较字面名称，不擅自把不同写法当成相同的运行时选择。

规范化前逐个检查实际经过的组件。禁止跨出项目根、符号链接（包括随后被 `..` 消去
的组件），以及通过缺失目录或普通文件回到父目录。绝对路径、盘符、反斜线、控制
字符与宏展开不会被猜测成本地路径。主文件配置、显式监视选择器及交付清单继续
采用原有严格可移植语法；这次调整只用于源码依赖查找。

## BibTeX 的显式相对文献路径

BibTeX 在新建输出目录运行，以隔离日志、BBL 和子 AUX。以 `./`、`../` 开头的
文件名不走普通 Kpathsea 搜索路径，单独设置 `BIBINPUTS` 无法恢复主文件目录的
含义。对应接口见 [Kpathsea 搜索规则](https://tug.ctan.org/systems/doc/kpathsea/kpathsea.html#Searching-overview)
和 [BibTeX 调用](https://www.tug.org/texinfohtml/web2c.html#bibtex-invocation)。

当可达生成 AUX 中有字面显式相对数据库或样式声明时，构建辅助脚本在输出目录的
`bibtex-inputs/` 中准备字节一致的资源副本、目录内别名和适配后的 AUX 树。
准备不会编辑源码或原始 AUX；后续原生编译仍正常更新输出 AUX。普通文件名继续
使用原有调用。子 AUX 指向暂存副本，
注释与无关 AUX 文件不会触发准备。

参考文献步骤新增 `prepared_inputs` 清单，记录实际保留文件、大小、摘要、类型和
原始资源路径；在文献执行前后及构建结束时核对副本和原始资源。评审保留暂存
AUX、数据库、样式证据，验证指纹并绑定所给项目内部的原始资源；原件缺失、变化
或处于项目外时，不发布评审目录。报告 schema 编号保持不变。

准备只处理字面单行 `bibdata`、`bibstyle`、`@input` 记录，不解释自定义 AUX 语法
或展开宏。最多读取 128 个可达 AUX，每个 2,000,000 字节；最多准备 128 个资源，
每个 64 MiB、总量 256 MiB。缺失或超限输入明确失败。原生 `--watch-input` 仍
相对主文件目录；这些检查不表示已监视全部外部或生成的原生输入。

真实编译检查覆盖共享章节、本地文档类/宏包、父目录图片，比较 recorder 路径，并
运行父目录文献的 BibTeX、Biber 两种后端；同时验证保留的暂存证据及源码不变。
这些属于合成工具检查，不证明科学内容正确。
