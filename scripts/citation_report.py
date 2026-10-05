"""Escaped, script-free citation inventory shared by offline reports."""
import html

LABELS = {
    "en": ("Citations with source locations", "Key", "Command / group", "Source location",
           "No supported literal citation keys found.",
           "Literal keys only; notes and special/custom syntax are not evaluated. This inventory does not prove that a backend accepted a citation or that it supports a claim."),
    "zh": ("带源码位置的文献引用", "引用键", "命令 / 参数组", "源码位置",
           "未找到支持范围内的字面引用键。",
           "仅列字面引用键；不解析注释参数与特殊、自定义语法。清单不能证明后端接受了引用，也不能证明文献支持相关论断。"),
}


def citation_table(rows, language):
    labels = LABELS[language]
    esc = lambda value: html.escape(str(value), quote=True)
    if not rows:
        return f'<p>{esc(labels[4])}</p>'
    content = ['<div class="table-scroll"><table><thead><tr>']
    content.extend(f'<th scope="col">{esc(label)}</th>' for label in labels[1:4])
    content.append('</tr></thead><tbody>')
    for item in rows:
        command = item["command"] + ("*" if item.get("starred") else "")
        content.append(f'<tr><td><code>{esc(item["key"])}</code></td><td><code>{esc(command)} / {esc(item["group"])}</code></td><td><code>{esc(item["file"])}:{esc(item["line"])}</code></td></tr>')
    content.append('</tbody></table></div>')
    return "".join(content)


BIBITEM_LABELS = {
    "en": ("Manual bibliography entries", "Key", "Source location", "Literal definitions",
           "No supported literal bibitem keys found.",
           "Keys from source bibitem commands only; optional display labels are skipped. Presence/counts do not prove execution, label validity, generated BBL contents or claim support."),
    "zh": ("手写参考文献条目", "条目键", "源码位置", "字面定义数量",
           "未找到支持范围内的字面 bibitem 键。",
           "仅记录源码 bibitem 命令的键，跳过可选显示标签；存在与数量不能证明实际执行、标签有效性、生成 BBL 的内容或文献支持相关论断。"),
}


def bibitem_table(rows, language):
    labels = BIBITEM_LABELS[language]
    esc = lambda value: html.escape(str(value), quote=True)
    if not rows:
        return f'<p>{esc(labels[4])}</p>'
    counted = any("definition_count" in row for row in rows)
    content = ['<div class="table-scroll"><table><thead><tr>']
    content.extend(f'<th scope="col">{esc(label)}</th>' for label in labels[1:4 if counted else 3])
    content.append('</tr></thead><tbody>')
    for row in rows:
        content.append(f'<tr><td><code>{esc(row["key"])}</code></td><td><code>{esc(row["file"])}:{esc(row["line"])}</code></td>')
        if counted:
            content.append(f'<td>{esc(row.get("definition_count", "—"))}</td>')
        content.append('</tr>')
    content.append('</tbody></table></div>')
    return "".join(content)
