"""Readable bilingual HTML for project review; no scripts or remote resources."""
import html
import json
from urllib.parse import quote


LABELS = {
    "en": {
        "title": "Manuscript change review", "intro": "Review source changes beside supplied build evidence and actual PDF pages. Literal checks do not certify scientific fidelity.",
        "required": "Human content review required", "json": "JSON evidence", "diff": "Source diff", "integrity": "Bundle checksums",
        "changes": "Changed files", "flags": "Content signals", "decisions": "Open author decisions", "pages": "PDF pages",
        "builds": "Build evidence", "before": "Before", "after": "After", "success": "Successful build", "failed": "Failed build", "unverified": "Build unverified",
        "build_report": "Build report", "pdf": "PDF", "engine": "Engine", "backend": "Bibliography tool", "unset": "Not selected",
        "no_build": "No actual build report supplied.", "legacy": "Legacy report: PDF identity at build time is unverified; only the current retained bytes are fingerprinted.",
        "warnings": "Build diagnostics", "unresolved": "Recognized unresolved references or citations remain.", "no_warnings": "No retained diagnostics. Inspect the PDF separately.",
        "retained": "Retained evidence files", "file": "File", "kind": "Change", "added": "Added", "removed": "Removed", "modified": "Modified",
        "files": "File changes", "empty_changes": "No changes in the supported inventory.", "no_diff": "Binary/asset change: compare file fingerprints in the JSON evidence.",
        "audit": "Content signals to review", "audit_note": "Added or removed literal values are review signals, not judgments of correctness. Numbers are counted as text tokens, not interpreted as scientific measurements.",
        "numbers": "Numbers", "reference_keys": "Labels, references and citations", "simple_math": "Delimited math", "count": "Count", "value": "Literal value",
        "scan_issues": "Incomplete literal source regions", "scan_note": "Unclosed verbatim regions can hide later content from the literal audit. Check the source and actual build before interpreting absent change signals.",
        "none": "No supported literal changes detected; this does not establish unchanged meaning.",
        "author": "Author decisions", "no_decisions": "No visible TODO or UNCERTAIN markers found.", "notes": "Supplied notes",
        "scope": "Inventory and limits", "scope_note": "Only the listed source/configuration/asset types are compared. Generated and environment directories are excluded. Other files are outside this review's coverage.",
        "suffixes": "Supported extensions", "excluded": "Excluded directory names", "complete": "Complete evidence",
        "no_page": "No supplied successful PDF page.", "page": "Page", "page_note": "Pages align by index only. Pagination changes need manual comparison. Keep this folder together for offline use.",
    },
    "zh": {
        "title": "论文修改审阅", "intro": "对照源码改动、所提供的构建证据与实际 PDF 页面。字面检查不能证明科学内容正确。",
        "required": "需要人工核对内容", "json": "JSON 证据", "diff": "源码差异", "integrity": "目录校验清单",
        "changes": "改动文件", "flags": "内容变化提示", "decisions": "待作者确认", "pages": "PDF 页面",
        "builds": "构建证据", "before": "修改前", "after": "修改后", "success": "编译成功", "failed": "编译失败", "unverified": "编译未验证",
        "build_report": "构建报告", "pdf": "PDF", "engine": "编译引擎", "backend": "参考文献工具", "unset": "未选择",
        "no_build": "未提供实际构建报告。", "legacy": "旧报告未记录编译时的 PDF 校验值；这里只核对当前保留文件的字节，编译时身份仍未验证。",
        "warnings": "构建诊断", "unresolved": "仍有检查器识别到的未解析引用或文献。", "no_warnings": "没有保留的诊断信息。仍需单独检查 PDF。",
        "retained": "已保留的证据文件", "file": "文件", "kind": "变化", "added": "新增", "removed": "删除", "modified": "修改",
        "files": "文件改动", "empty_changes": "支持的清单范围内未发现改动。", "no_diff": "二进制或资源文件改动：请在 JSON 证据中对照文件校验值。",
        "audit": "需要核对的内容变化", "audit_note": "新增或删除的字面值只是核对提示，不能判断修改是否正确。数值按文本统计，不解释其科学含义。",
        "numbers": "数值", "reference_keys": "标签、引用与文献键", "simple_math": "有定界符的公式", "count": "次数", "value": "字面值",
        "scan_issues": "未闭合的源码字面区域", "scan_note": "未闭合的原样文本可能遮住后续内容，影响字面变化检查。请先核对源码与实际构建，再判断未出现变化提示的内容。",
        "none": "未检测到支持范围内的字面变化；这不能证明含义不变。",
        "author": "作者待确认事项", "no_decisions": "未发现可见的 TODO 或 UNCERTAIN 标记。", "notes": "提供的说明",
        "scope": "清单范围与限制", "scope_note": "只比较所列源码、配置和资源类型；生成目录与环境目录会被排除。其他文件不在本次审阅覆盖范围内。",
        "suffixes": "支持的扩展名", "excluded": "排除的目录名", "complete": "完整证据",
        "no_page": "未提供来自成功构建的对应 PDF 页面。", "page": "页面", "page_note": "页面仅按序号对齐。分页变化需要人工对照；离线使用时请保持整个目录完整。",
    },
}


def review_html(report, diffs, language="en"):
    if language not in LABELS:
        raise ValueError("Review language must be en or zh")
    labels = LABELS[language]
    esc = lambda value: html.escape(str(value), quote=True)
    link = lambda path, text: f'<a href="{esc(quote(path, safe="/"))}">{esc(text)}</a>'
    details = lambda title, text: f'<details><summary>{esc(title)}</summary><pre>{esc(text)}</pre></details>'
    content = [f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' data:; style-src \'unsafe-inline\'">',
               f'<title>{esc(labels["title"])}</title><style>',
               ':root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:#f4f3ed;color:#263027;font:16px/1.65 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:40px 24px}h1{font-size:clamp(28px,5vw,42px);line-height:1.2;letter-spacing:-.025em}h2{margin-top:36px}h3,h4{margin:0 0 12px}small{color:#586555}section,article,details{background:#fffefa;border:1px solid #d5dacd;border-radius:14px;padding:20px;margin:16px 0}pre,code{font:13px/1.6 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere}pre{margin:12px 0 0}a{color:#326041}a:focus-visible,summary:focus-visible{outline:3px solid #b58c30;outline-offset:4px}.pair,.facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.pair>section{margin:0}.facts{grid-template-columns:repeat(4,minmax(0,1fr))}.facts section{margin:0;padding:16px}.facts strong{display:block;font-size:28px}.pair img{width:100%;height:auto;border:1px solid #d5dacd;background:white}.table-scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #d5dacd}td{overflow-wrap:anywhere}summary{cursor:pointer;font-weight:600}.pill{display:inline-block;border:1px solid #bac5b3;border-radius:20px;padding:3px 12px}.failed{border-top:4px solid #a84436}.success{border-top:4px solid #537b55}.unverified{border-top:4px solid #778779}.location{overflow-wrap:anywhere}.nav{display:flex;gap:18px;flex-wrap:wrap}.nav a{text-underline-offset:4px}@media(max-width:700px){main{padding:24px 16px}.pair{grid-template-columns:1fr}.facts{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(prefers-color-scheme:dark){body{background:#171c18;color:#e0e7da}section,article,details{background:#212a22;border-color:#40523f}a{color:#b2d9a6}small{color:#b6c2b0}td,th{border-color:#40523f}}@media print{body{background:white;color:black}main{padding:0}section,article{break-inside:avoid}.nav{display:none}}',
               '</style></head><body><main><small>MANUSCRIPT TOOLKIT / REVIEW</small>',
               f'<h1>{esc(labels["title"])}</h1><p>{esc(labels["intro"])}</p><p><span class="pill">{esc(labels["required"])}</span></p>',
               '<nav class="nav" aria-label="Report">' + link('review.json', labels['json']) + link('changes.diff', labels['diff']) + link('integrity.json', labels['integrity']) + '</nav>',
               '<div class="facts">']
    for key, count in (("changes", len(report["changes"])), ("flags", len(report["content_audit"])),
                       ("decisions", len(report["author_decisions"])), ("pages", sum(len(item["pages"]) for item in report["builds"].values()))):
        content.append(f'<section><small>{esc(labels[key])}</small><strong>{count}</strong></section>')
    content.append(f'</div><h2>{esc(labels["builds"])}</h2><div class="pair">')
    for side in ("before", "after"):
        build = report["builds"][side]
        status = build["status"]
        content.append(f'<section class="{esc(status)}"><h3>{esc(labels[side])} · {esc(labels[status])}</h3>')
        if build.get("evidence"):
            content.append('<p>' + link(build['evidence'], labels['build_report']) + '</p>')
            content.append(f'<p>{esc(labels["engine"])}: <code>{esc(build.get("engine") or labels["unset"])}</code><br>{esc(labels["backend"])}: <code>{esc(build.get("backend") or labels["unset"])}</code></p>')
        else:
            content.append(f'<p>{esc(labels["no_build"])}</p>')
        if build.get("pdf"):
            content.append('<p>' + link(build['pdf'], labels['pdf']) + '</p>')
        if build.get("pdf_binding") == "unverified-legacy-report":
            content.append(f'<p>{esc(labels["legacy"])}</p>')
        if build.get("failure"):
            content.append(f'<pre>{esc(build["failure"])}</pre>')
        if build.get("unresolved_references"):
            content.append(f'<p>{esc(labels["unresolved"])}</p>')
        if build.get("diagnostics"):
            content.append(details(labels["warnings"], json.dumps(build["diagnostics"], ensure_ascii=False, indent=2)))
        elif status == "success":
            content.append(f'<p>{esc(labels["no_warnings"])}</p>')
        if build.get("retained_files"):
            content.append('<details><summary>' + esc(labels['retained']) + '</summary><ul>')
            for item in build['retained_files']:
                content.append('<li>' + link(item['file'], item['file'].split('/')[-1]) + f' · <code>{esc(item["sha256"])}</code></li>')
            content.append('</ul></details>')
        content.append('</section>')
    content.append(f'</div><h2>{esc(labels["files"])}</h2>')
    if report["changes"]:
        content.append(f'<section class="table-scroll"><table><thead><tr><th scope="col">{esc(labels["file"])}</th><th scope="col">{esc(labels["kind"])}</th></tr></thead><tbody>')
        for item in report["changes"]:
            content.append(f'<tr><td><code>{esc(item["file"])}</code></td><td>{esc(labels[item["kind"]])}</td></tr>')
        content.append('</tbody></table></section>')
        for item in report["changes"]:
            content.append(details(item['file'], diffs.get(item['file']) or labels['no_diff']))
    else:
        content.append(f'<section>{esc(labels["empty_changes"])}</section>')
    if report.get("source_scan_issues"):
        content.append(f'<h2>{esc(labels["scan_issues"])}</h2><p>{esc(labels["scan_note"])}</p><section><ul>')
        for item in report["source_scan_issues"]:
            content.append(f'<li>{esc(labels[item["side"]])} · <code>{esc(item["file"])}:{esc(item["line"])}</code> — {esc(item["message"])}</li>')
        content.append('</ul></section>')
    content.append(f'<h2>{esc(labels["audit"])}</h2><p>{esc(labels["audit_note"])}</p>')
    if not report["content_audit"]:
        content.append(f'<section>{esc(labels["none"])}</section>')
    for item in report["content_audit"]:
        content.append(f'<article><h3 class="location">{esc(item["file"])}</h3>')
        for category in ("numbers", "reference_keys", "simple_math"):
            if category not in item:
                continue
            content.append(f'<h4>{esc(labels[category])}</h4><div class="table-scroll"><table><thead><tr>')
            for field in ("kind", "value", "count"):
                content.append(f'<th scope="col">{esc(labels[field])}</th>')
            content.append('</tr></thead><tbody>')
            for kind in ("removed", "added"):
                for value, count in item[category][kind]:
                    content.append(f'<tr><td>{esc(labels[kind])}</td><td><code>{esc(value)}</code></td><td>{count}</td></tr>')
            content.append('</tbody></table></div>')
        content.append('</article>')
    content.append(f'<h2>{esc(labels["author"])}</h2>')
    for item in report["author_decisions"]:
        content.append(f'<article><h3 class="location">{esc(item["file"])}:{esc(item["line"])}</h3><pre>{esc(item["excerpt"])}</pre></article>')
    if not report["author_decisions"]:
        content.append(f'<section>{esc(labels["no_decisions"])}</section>')
    if report["notes"]:
        content.append(f'<section><h3>{esc(labels["notes"])}</h3><pre>{esc(report["notes"])}</pre></section>')
    content.append(f'<h2>{esc(labels["pages"])}</h2>')
    before, after = (report['builds'][side]['pages'] for side in ('before', 'after'))
    for index in range(max(len(before), len(after))):
        content.append(f'<section><h3>{esc(labels["page"])} {index + 1}</h3><div class="pair">')
        for side, pages in (("before", before), ("after", after)):
            content.append(f'<div><h4>{esc(labels[side])}</h4>')
            content.append(f'<img loading="lazy" src="{esc(quote(pages[index], safe="/"))}" alt="{esc(labels[side])} {index + 1}">' if index < len(pages) else f'<p>{esc(labels["no_page"])}</p>')
            content.append('</div>')
        content.append('</div></section>')
    content.append(f'<p><small>{esc(labels["page_note"])}</small></p><h2>{esc(labels["scope"])}</h2><section><p>{esc(labels["scope_note"])}</p>')
    scope = report.get('inventory_scope', {})
    for key, field in (("suffixes", "extensions"), ("excluded", "excluded_directories")):
        content.append(f'<p><strong>{esc(labels[key])}:</strong> <code>{esc(", ".join(scope.get(field, [])))}</code></p>')
    content.append('</section>' + details(labels['complete'], json.dumps(report, ensure_ascii=False, indent=2)) + '</main></body></html>')
    return ''.join(content)
