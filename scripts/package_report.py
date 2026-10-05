"""Escaped, script-free tables for literal class/package declarations."""
import html

LABELS = {
    'en': ('Class and package declarations', 'Name', 'Command', 'Literal options', 'Source location',
           'No supported loader declarations.',
           'Literal loader observations only. Defaults, forwarded/global options, precedence and option validity are not evaluated; backend observations do not select a build tool.'),
    'zh': ('文档类与宏包声明', '名称', '命令', '字面选项', '源码位置',
           '未找到支持范围内的加载声明。',
           '仅记录字面加载声明；不判断默认、传递或全局选项、优先级及选项有效性。后端观察不会自动选择构建工具。'),
}


def package_table(rows, language):
    labels = LABELS[language]
    esc = lambda value: html.escape(str(value), quote=True)
    if not rows:
        return f'<p>{esc(labels[5])}</p>'
    content = ['<div class="table-scroll"><table><thead><tr>']
    content.extend(f'<th scope="col">{esc(label)}</th>' for label in labels[1:5])
    content.append('</tr></thead><tbody>')
    for row in rows:
        content.append('<tr>' + ''.join(f'<td><code>{esc(row[key])}</code></td>' for key in ('name', 'command', 'options')))
        content.append(f'<td><code>{esc(row["file"])}:{esc(row["line"])}</code></td></tr>')
    content.append('</tbody></table></div>')
    return ''.join(content)
