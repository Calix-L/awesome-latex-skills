"""Escaped, offline tables for literal labels and cross-reference targets."""
import html

LABELS = {
    "en": {"title": "Labels and cross-reference targets", "labels": "Label definitions", "refs": "References",
           "key": "Label key", "command": "Command / argument", "location": "Source location", "resolution": "Literal definitions",
           "defined": "One definition", "missing": "No definition found", "ambiguous": "Multiple definitions",
           "none": "No supported literal entries.", "note": "Definitions and targets are literal source observations. Counts do not prove conditional execution, generated/external labels, counter types or the actual compiled target."},
    "zh": {"title": "标签定义与交叉引用", "labels": "标签定义", "refs": "引用目标", "key": "标签键",
           "command": "命令 / 参数", "location": "源码位置", "resolution": "字面定义",
           "defined": "找到一个定义", "missing": "未找到定义", "ambiguous": "存在多个定义",
           "none": "未找到支持范围内的字面条目。", "note": "定义与目标来自源码字面观察；数量不证明条件分支执行、生成或外部标签、计数器类型及实际编译目标。"},
}


def reference_tables(definitions, references, language):
    labels = LABELS[language]
    esc = lambda value: html.escape(str(value), quote=True)
    content = []
    for kind, rows in (("labels", definitions), ("refs", references)):
        content.append(f'<details><summary>{esc(labels[kind])} ({len(rows)})</summary>')
        if not rows:
            content.append(f'<p>{esc(labels["none"])}</p></details>')
            continue
        columns = ("key", "location") if kind == "labels" else ("key", "command", "location")
        resolved = kind == "refs" and any("resolution" in row for row in rows)
        content.append('<div class="table-scroll"><table><thead><tr>')
        content.extend(f'<th scope="col">{esc(labels[key])}</th>' for key in columns + (("resolution",) if resolved else ()))
        content.append('</tr></thead><tbody>')
        for row in rows:
            content.append(f'<tr><td><code>{esc(row["key"])}</code></td>')
            if kind == "refs":
                command = row["command"] + ("*" if row.get("starred") else "")
                content.append(f'<td><code>{esc(command)} / {esc(row["group"])}</code></td>')
            content.append(f'<td><code>{esc(row["file"])}:{esc(row["line"])}</code></td>')
            if resolved:
                status = labels.get(row.get("resolution"), "—")
                target = row.get("first_definition")
                content.append(f'<td>{esc(status)} ({esc(row.get("definition_count", "—"))})')
                if target:
                    content.append(f'<br><code>{esc(target["file"])}:{esc(target["line"])}</code>')
                content.append('</td>')
            content.append('</tr>')
        content.append('</tbody></table></div></details>')
    return "".join(content)
