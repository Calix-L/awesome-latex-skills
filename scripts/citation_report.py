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
