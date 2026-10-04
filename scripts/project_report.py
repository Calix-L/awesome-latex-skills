"""Render a supplied static inspection as a self-contained, escaped HTML report."""
from collections import Counter
import html
import json
from pathlib import Path
from urllib.parse import quote


LABELS = {
    "en": {"title": "LaTeX project inspection", "note": "Static inspection · Build not run",
           "intro": "Literal dependencies, file fingerprints and next steps. A clean static report does not prove compilation or scientific fidelity.",
           "main": "Main source", "engine": "Engine", "backend": "Bibliography tool", "inputs": "Observed inputs",
           "diagnostics": "Issues and next steps", "none": "No supported static issues found.",
           "candidates": "Root candidates", "dependencies": "Literal dependencies", "from": "Source location",
           "selected": "Selected main only", "all_roots": "All inventoried TeX sources",
           "command": "Command", "requested": "Requested input", "resolved": "Resolution",
           "found": "Found", "missing": "Missing", "skipped": "Excluded by includeonly; not checked",
           "unknown": "Unverified", "hashes": "Dependency input fingerprints", "observed": "All observed file fingerprints", "limitations": "Inspection limits",
           "json": "JSON report", "integrity": "File integrity manifest", "complete": "Complete evidence", "next": "Next step", "unset": "Not selected",
           "error": "Errors", "warning": "Warnings", "unverified": "Unverified checks"},
    "zh": {"title": "LaTeX 项目检查", "note": "静态检查 · 尚未编译",
           "intro": "查看字面依赖、文件校验值及处理建议。静态检查通过不代表编译通过，也不能证明科学内容正确。",
           "main": "主文件", "engine": "编译引擎", "backend": "参考文献工具", "inputs": "已记录输入",
           "diagnostics": "问题与处理建议", "none": "未发现检查器支持范围内的静态问题。",
           "candidates": "候选根文件", "dependencies": "字面依赖", "from": "源码位置", "command": "命令",
           "selected": "仅选中的主文件", "all_roots": "全部清单内 TeX 源文件",
           "requested": "请求的输入", "resolved": "解析结果", "found": "已找到", "missing": "缺失",
           "skipped": "被 includeonly 排除；未检查", "unknown": "未验证", "hashes": "依赖输入文件校验值", "observed": "全部已读取文件校验值",
           "limitations": "检查范围与限制", "json": "JSON 报告", "integrity": "文件校验清单", "complete": "完整证据",
           "next": "下一步", "unset": "未选择", "error": "错误", "warning": "警告", "unverified": "未验证项"},
}


def inspection_html(report, language="en", json_name=None, integrity_name=None):
    labels = LABELS[language]
    esc = lambda value: html.escape(str(value), quote=True)
    location = lambda item: esc(item.get("file") or item.get("from") or "—") + (f":{esc(item['line'])}" if item.get("line") else "")
    counts = Counter(item["severity"] for item in report["diagnostics"])
    content = [f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">',
               f'<title>{esc(labels["title"])}</title><style>',
               ':root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:#f4f3ed;color:#263027;font:16px/1.65 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:36px 24px}h1{font-size:36px;line-height:1.2}h2{margin-top:32px}small{color:#586555}article,section,details{background:#fffefa;border:1px solid #d5dacd;border-radius:12px;padding:20px;margin:16px 0}pre,code{font:13px/1.6 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere}pre{margin:0}a{color:#326041}.facts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.facts section{margin:0;padding:16px}.facts strong{display:block;overflow-wrap:anywhere}.pill{display:inline-block;border:1px solid #bac5b3;border-radius:20px;padding:3px 12px;margin-right:6px}.error{border-left:4px solid #a84436}.warning{border-left:4px solid #b58c30}.unverified{border-left:4px solid #778779}.table-scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;vertical-align:top;padding:12px 9px;border-bottom:1px solid #ddd}td code{white-space:normal;overflow-wrap:anywhere}summary{cursor:pointer;font-weight:600}.path{overflow-wrap:anywhere}@media(max-width:700px){main{padding:24px 16px}h1{font-size:28px}.facts{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(prefers-color-scheme:dark){body{background:#171c18;color:#e0e7da}article,section,details{background:#212a22;border-color:#40523f}small{color:#b6c2b0}a{color:#b2d9a6}td,th{border-color:#40523f}}',
               '</style></head><body><main><small>MANUSCRIPT TOOLKIT / PROJECT</small>',
               f'<h1>{esc(labels["title"])}</h1><p>{esc(labels["intro"])}</p>',
               f'<p><span class="pill">{esc(report["status"])}</span><span class="pill">{esc(labels["note"])}</span></p>',
               f'<p class="path"><code>{esc(report["root"])}</code></p>']
    if json_name is not None:
        content.append(f'<p><a href="{esc(quote(json_name, safe=""))}">{esc(labels["json"])}</a></p>')
    if integrity_name is not None:
        content.append(f'<p><a href="{esc(quote(integrity_name, safe=""))}">{esc(labels["integrity"])}</a></p>')
    content.append('<div class="facts">')
    for key, value in (("main", report.get("main")), ("engine", report.get("engine")),
                       ("backend", report.get("backend")), ("inputs", len(report["inputs"]))):
        content.append(f'<section><small>{esc(labels[key])}</small><strong>{esc(labels["unset"] if value is None else value)}</strong></section>')
    content.append(f'</div><h2>{esc(labels["diagnostics"])}</h2><p>')
    for severity in ("error", "warning", "unverified"):
        content.append(f'<span class="pill">{esc(labels[severity])}: {counts[severity]}</span>')
    content.append('</p>')
    if not report["diagnostics"]:
        content.append(f'<section>{esc(labels["none"])}</section>')
    for item in report["diagnostics"]:
        severity = item["severity"] if item["severity"] in {"error", "warning", "unverified"} else "unverified"
        content.append(f'<article class="{severity}"><small>{location(item)} · {esc(item["code"])}</small><p>{esc(item["message"])}</p><p><strong>{esc(labels["next"])}:</strong> {esc(item["next_step"])}</p></article>')
    if report["root_candidates"]:
        scope = labels["selected"] if report.get("root_candidate_scope") == "selected-main-only" else labels["all_roots"]
        content.append(f'<details><summary>{esc(labels["candidates"])} · {esc(scope)}</summary><pre>{esc(chr(10).join(report["root_candidates"]))}</pre></details>')
    content.append(f'<h2>{esc(labels["dependencies"])}</h2><section class="table-scroll"><table><thead><tr>')
    for label in ("from", "command", "requested", "resolved"):
        content.append(f'<th scope="col">{esc(labels[label])}</th>')
    content.append('</tr></thead><tbody>')
    for item in report["dependencies"]:
        resolution = labels["skipped"] if item.get("skipped") else labels["found"] if item["exists"] is True else labels["missing"] if item["exists"] is False else labels["unknown"]
        target = f'<br><code>{esc(item["file"])}</code>' if item.get("file") else ""
        content.append(f'<tr><td><code>{location(item)}</code></td><td><code>{esc(item["command"])}</code></td><td><code>{esc(item["requested"])}</code></td><td>{esc(resolution)}{target}</td></tr>')
    content.append('</tbody></table></section>')
    content.append(f'<details><summary>{esc(labels["hashes"])}</summary><pre>{esc(json.dumps(report["inputs"], ensure_ascii=False, indent=2))}</pre></details>')
    if "observed_files" in report:
        content.append(f'<details><summary>{esc(labels["observed"])}</summary><pre>{esc(json.dumps(report["observed_files"], ensure_ascii=False, indent=2))}</pre></details>')
    content.append(f'<h2>{esc(labels["limitations"])}</h2><section><ul>')
    content.extend(f'<li>{esc(item)}</li>' for item in report["limitations"])
    content.append(f'</ul></section><details><summary>{esc(labels["complete"])}</summary><pre>{esc(json.dumps(report, ensure_ascii=False, indent=2))}</pre></details></main></body></html>')
    return "".join(content)


def write_inspection_reports(json_path, html_path, report, language="en", integrity_name=None):
    """Prepare all content first; separate files are not a transaction."""
    paths = [Path(path).expanduser().absolute() if path is not None else None
             for path in (json_path, html_path)]
    destinations = [path for path in paths if path is not None]
    resolved = [path.resolve() for path in destinations]
    if (len(set(resolved)) != len(resolved)
            or any(path.exists() or path.is_symlink() for path in destinations)
            or any(a != b and a.is_relative_to(b) for a in resolved for b in resolved)):
        raise ValueError("Each report needs a distinct new file without parent/child collisions")
    if paths[1] and paths[1].suffix.lower() not in {".html", ".htm"}:
        raise ValueError("HTML report needs a .html or .htm filename")
    content = []
    if paths[0]:
        content.append((paths[0], json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"))
    if paths[1]:
        name = paths[0].name if paths[0] and paths[0].resolve().parent == paths[1].resolve().parent else None
        content.append((paths[1], inspection_html(report, language, name, integrity_name)))
    for path, text in content:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as destination:
            destination.write(text)


def write_inspection_html(path, report, language="en", json_path=None):
    path = Path(path).expanduser().absolute()
    name = Path(json_path).name if json_path and Path(json_path).resolve().parent == path.resolve().parent else None
    content = inspection_html(report, language, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as destination:
        destination.write(content)
