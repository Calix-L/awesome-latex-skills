"""Copy one bundled synthetic case without editing, compiling or executing it."""
import hashlib
import html
from pathlib import Path
import re
import tempfile
from urllib.parse import quote

from artifact_integrity import regular_files, seal_bundle
from project_support import ROOT, parse_json, safe_path, sha256, write_new_json

EXPORT_CASES = ("rescue", "polish", "fmt", "read", "pdf2tex", "full-paper")
MAX_COPY_FILES = 2000
MAX_COPY_BYTES = 8 * 1024 * 1024
MAX_COPY_TOTAL = 64 * 1024 * 1024
REPOSITORY = "https://github.com/Calix-L/awesome-latex-skills"


def bounded_source(path):
    with path.open("rb") as stream:
        content = stream.read(MAX_COPY_BYTES + 1)
    if len(content) > MAX_COPY_BYTES:
        raise ValueError(f"Example source exceeds the per-file byte limit: {path.name}")
    return content


def case_spec(identifier, root=ROOT, document=None):
    if identifier not in EXPORT_CASES:
        raise ValueError("Select a known example case")
    if identifier == "full-paper":
        return {"id": identifier, "skill": "latex-rescue / latex-polish / latex-fmt",
                "directory": "examples/full-paper", "input": "before/main.tex", "candidate": "after/main.tex",
                "decisions": "decisions.md",
                "required": ["before/main-cn.tex", "after/main-cn.tex", "after/.als.json"]}
    from run_examples import catalog
    item = next((item for item in catalog(root, document) if item["id"] == identifier), None)
    if item is None:
        raise ValueError("Selected example is absent from the catalog")
    return {**item, "decisions": "report.md", "required": []}


def copy_inputs(root, spec):
    source = safe_path(root, spec["directory"])
    files = regular_files(source)
    # Repository-level README references are replaced by a standalone export guide.
    selected = {name: path for name, path in files.items()
                if name != "README.md" and "__pycache__" not in Path(name).parts
                and Path(name).suffix not in {".pyc", ".pyo"}}
    required = {spec["input"], spec["candidate"], spec["decisions"], *spec["required"]}
    if not required.issubset(selected):
        raise ValueError("Example source is incomplete: " + ", ".join(sorted(required - set(selected))))
    if len(selected) > MAX_COPY_FILES:
        raise ValueError("Example exceeds the file-count limit")
    return selected


def example_commands(report, language="en"):
    identifier = report["case"]
    if identifier == "full-paper":
        commands = ["als doctor --project case/after --skill latex-rescue",
                "als build --project case/after --output ../example-build --until-stable --require-resolved",
                "als build case/after/main-cn.tex --engine xelatex --backend bibtex --passes 3 --output ../example-chinese --require-resolved"]
    elif identifier == "read":
        commands = ["als doctor --skill paper-read"]
    elif identifier == "pdf2tex":
        commands = ["als doctor --skill pdf2tex",
                "als extract case/input.pdf --output ../example-extraction --chars --render",
                "als build case/output.tex --output ../example-build"]
    else:
        commands = [f"als doctor --project case --main output.tex --engine pdflatex --skill {report['skill']}",
                    "als build case/output.tex --output ../example-build"]
    return [command + " --language zh" if language == "zh" and command.startswith("als doctor ") else command for command in commands]


def guide_text(report, language):
    zh = language == "zh"
    return {
        "title": "可编辑的论文案例" if zh else "An editable manuscript example",
        "intro": "自制合成案例，候选结果由维护者编写。导出不调用模型，不编译或安装依赖。" if zh else
                 "A synthetic case with a maintainer-authored candidate. Export does not call a model, build documents or install dependencies.",
        "input": "原始输入" if zh else "Original input", "candidate": "候选结果" if zh else "Candidate",
        "decisions": "修改与未决问题" if zh else "Changes and open decisions", "steps": "接下来怎么做" if zh else "Next steps",
        "cwd": "在导出目录中运行以下命令，需已安装 als。按实际环境使用新输出目录。" if zh else
               "Run these commands from the exported directory with als installed. Use fresh output directories in your actual environment.",
        "scope": "这些命令检查证据；编辑和分析仍由所选 Skill 的 Agent 完成。未选中的原稿可能故意编译失败；未知引用仍需作者确认。" if zh else
                 "These commands inspect evidence; editing and analysis require your skill-enabled agent. The original may intentionally fail, and unknown citations still need author confirmation.",
        "tools": ("完整论文需要 pdfLaTeX、XeLaTeX、BibTeX 和 Noto Serif CJK SC；其他 TeX 案例需要实际引擎与包。PDF 提取和 PDF 审查另需 PyMuPDF。阅读文本本身无需 TeX 或 PDF 库。" if zh else
                  "The full paper needs pdfLaTeX, XeLaTeX, BibTeX and Noto Serif CJK SC. Other TeX cases need the actual engine/packages. PDF extraction/review additionally needs PyMuPDF. Text reading needs neither TeX nor a PDF library."),
        "verify": "先核验，再在单独副本上编辑" if zh else "Verify first, then edit a separate copy",
        "immutable": "导出清单记录初始字节。移动整个目录仍可核验；修改或增加文件后核验会失败。保留一份未修改导出，另建候选副本和构建输出。核验不证明来源身份、科学内容或模型质量。" if zh else
                     "The manifest records initial bytes. A moved directory remains verifiable; edits or added files fail the check. Preserve the export and edit a separate candidate copy, keeping builds elsewhere. Verification does not certify publisher identity, scientific truth or model quality.",
        "files": "导出的源文件" if zh else "Exported source files", "source": "仓库来源" if zh else "Repository source",
        "receipt": "来源与指纹" if zh else "Provenance and fingerprints", "license": "MIT 许可证" if zh else "MIT license",
        "limit": "保留数量、精度、公式、引用键和不确定项；字面量不变不代表原意不变。此导出包含候选答案与修改说明，不能用作盲评 Agent 工作区。" if zh else
                 "Preserve quantities, precision, equations, keys and uncertainties; unchanged literals do not prove unchanged meaning. This export includes candidate answers and decisions and must not be used as a blind evaluation task workspace.",
    }


def example_markdown(report, language):
    labels = guide_text(report, language)
    lines = [f"# {labels['title']}", "", labels["intro"], "",
             f"**{report['case']}** · {report['version']} · {report['skill']}", ""]
    for field in ("input", "candidate", "decisions"):
        lines.append(f"- [{labels[field]}]({quote(report[field], safe='/')})")
    lines.extend(["", f"## {labels['steps']}", "", labels["cwd"], "", "```sh",
                  *example_commands(report, language), "```", "", labels["tools"], "", labels["scope"], "",
                  f"## {labels['verify']}", "", "```sh", "als verify example .", "```", "", labels["immutable"], "",
                  labels["limit"], "", f"[{labels['receipt']}](example.json) · [{labels['license']}](LICENSE) · "
                  f"[{labels['source']}]({report['source_url']})", ""])
    return "\n".join(lines)


def example_html(report, language):
    labels = guide_text(report, language)
    esc = lambda value: html.escape(str(value), quote=True)
    link = lambda target, label: f'<a href="{esc(quote(target, safe="/"))}">{esc(label)}</a>'
    content = ['<!doctype html>', f'<html lang="{language}"><head><meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width,initial-scale=1">',
               '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">',
               f'<title>{esc(labels["title"])}</title><style>',
               ':root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:#f4f3ed;color:#263027;font:16px/1.65 system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:40px 24px}h1{font-size:40px;line-height:1.15}h2{font-size:22px;margin-top:32px}small{color:#586555}section,article,details{background:#fffefa;border:1px solid #d5dacd;border-radius:12px;padding:22px;margin:16px 0}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.cards article{margin:0}.cards a{display:block;font-weight:600}a{color:#326041}pre,code{font:13px/1.65 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer;font-weight:600}li{overflow-wrap:anywhere}.meta{padding:5px 14px;border:1px solid #bac5b3;border-radius:24px;display:inline-block}footer{margin-top:28px;font-size:14px}@media(max-width:650px){main{padding:24px 16px}h1{font-size:30px}.cards{grid-template-columns:1fr}}@media(prefers-color-scheme:dark){body{background:#171c18;color:#e0e7da}section,article,details{background:#212a22;border-color:#40523f}small{color:#b6c2b0}a{color:#b2d9a6}}',
               '</style></head><body><main><small>MANUSCRIPT TOOLKIT / EXAMPLE</small>',
               f'<h1>{esc(labels["title"])}</h1><p>{esc(labels["intro"])}</p>',
               f'<p class="meta">{esc(report["case"])} · {esc(report["version"])} · {esc(report["skill"])}</p><div class="cards">']
    for field in ("input", "candidate", "decisions"):
        content.append(f'<article>{link(report[field], labels[field])}<code>{esc(report[field])}</code></article>')
    content.extend(['</div>', f'<h2>{esc(labels["steps"])}</h2><section><p>{esc(labels["cwd"])}</p>',
                    f'<pre>{esc(chr(10).join(example_commands(report, language)))}</pre><p>{esc(labels["tools"])}</p>',
                    f'<p>{esc(labels["scope"])}</p></section><h2>{esc(labels["verify"])}</h2>',
                    f'<section><pre>als verify example .</pre><p>{esc(labels["immutable"])}</p><p>{esc(labels["limit"])}</p></section>',
                    f'<details><summary>{esc(labels["files"])}</summary><ul>'])
    for row in report["source_files"]:
        content.append(f'<li>{link(row["file"], row["file"])} · {esc(row["bytes"])} B</li>')
    content.extend(['</ul></details><footer>', link("example.json", labels["receipt"]), ' · ',
                    link("integrity.json", "SHA-256"), ' · ', link("LICENSE", labels["license"]), ' · ',
                    f'<a href="{esc(report["source_url"])}">{esc(labels["source"])}</a>', '</footer></main></body></html>'])
    return "".join(content)


def export_example(identifier, output, language="en", root=ROOT):
    if language not in {"en", "zh"}:
        raise ValueError("Example language must be en or zh")
    root = Path(root).resolve()
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(root):
        raise ValueError("Example output must be new and outside bundled source resources")
    output = output.resolve()
    version_bytes = bounded_source(safe_path(root, "VERSION"))
    current = version_bytes.decode("utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", current):
        raise ValueError("Example export requires a semantic source version")
    index_bytes = bounded_source(safe_path(root, "examples/index.json")) if identifier != "full-paper" else None
    spec = case_spec(identifier, root, parse_json(index_bytes.decode("utf-8")) if index_bytes is not None else None)
    selected = copy_inputs(root, spec)
    contents, observations, total = {}, {}, 0
    for name, path in sorted(selected.items()):
        data = bounded_source(path)
        total += len(data)
        if len(data) > MAX_COPY_BYTES or total > MAX_COPY_TOTAL:
            raise ValueError("Example exceeds source byte limits")
        destination = "case/" + name
        source_name = spec["directory"] + "/" + name
        contents[destination] = data
        observations[source_name] = hashlib.sha256(data).hexdigest()
    license_path = safe_path(root, "LICENSE")
    license_bytes = bounded_source(license_path)
    if not license_bytes or len(license_bytes) > MAX_COPY_BYTES or total + len(license_bytes) > MAX_COPY_TOTAL:
        raise ValueError("Example requires a nonempty bounded license")
    contents["LICENSE"] = license_bytes
    observations["LICENSE"] = hashlib.sha256(license_bytes).hexdigest()
    observations["VERSION"] = hashlib.sha256(version_bytes).hexdigest()
    if identifier != "full-paper":
        observations["examples/index.json"] = hashlib.sha256(index_bytes).hexdigest()
    result = {"schema": 1, "kind": "worked_example_export", "version": current, "case": identifier,
              "skill": spec["skill"], "origin": "synthetic-maintainer-authored", "language": language,
              "input": "case/" + spec["input"], "candidate": "case/" + spec["candidate"],
              "decisions": "case/" + spec["decisions"],
              "source_url": f"{REPOSITORY}/tree/v{current}/{spec['directory']}",
              "source_files": [{"file": name, "source": "LICENSE" if name == "LICENSE" else spec["directory"] + "/" + name[5:],
                                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for name, data in sorted(contents.items())],
              "interpretation": "Initial source-byte copy only; no compilation, model execution, author review or venue-compliance certification."}
    # Prepare both formats before creating a staging directory.
    markdown, page = example_markdown(result, language), example_html(result, language)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".example-", dir=output.parent) as temporary:
        staged = Path(temporary) / "bundle"
        staged.mkdir()
        for name, data in contents.items():
            target = safe_path(staged, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        write_new_json(staged / "example.json", result)
        (staged / "README.md").write_text(markdown, encoding="utf-8")
        (staged / "report.html").write_text(page, encoding="utf-8")
        seal_bundle(staged, "worked_example_integrity")
        # Check every selected file, source membership and the actual copied bytes.
        if set(copy_inputs(root, spec)) != set(selected):
            raise ValueError("Example source inventory changed during export")
        for name, digest in observations.items():
            if sha256(safe_path(root, name)) != digest:
                raise ValueError(f"Example source changed during export: {name}")
        for name, data in contents.items():
            if sha256(safe_path(staged, name)) != hashlib.sha256(data).hexdigest():
                raise ValueError(f"Example staged bytes changed during export: {name}")
        from verify_artifacts import verify_example
        if verify_example(staged)["status"] != "verified":
            raise ValueError("Staged example failed complete byte verification")
        if output.exists() or output.is_symlink():
            raise ValueError("Example output appeared during publication")
        staged.rename(output)
    return {"schema": 1, "status": "exported-not-run", "case": identifier, "version": current,
            "output": str(output), "files_copied": len(contents), "guide": "report.html",
            "provenance": "example.json", "integrity": "integrity.json", "language": language,
            "next": "Open report.html; verify the initial export, then edit a separate copy. No model or native tool has run."}
