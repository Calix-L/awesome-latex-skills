"""Escaped bilingual tables for complete literal dependency declarations."""
import html

LABELS = {
    'en': ('Dependency declarations', 'Command', 'Literal argument', 'Literal options', 'Source location', 'Syntax',
           'Supported literal syntax', 'Unverified syntax', 'No dependency declarations.',
           'Options are observations, not validated settings. Contents of options and filename arguments are not scanned as body commands; expansion and actual execution remain unverified.'),
    'zh': ('依赖命令声明', '命令', '字面参数', '字面选项', '源码位置', '语法',
           '支持的字面语法', '未验证语法', '未找到依赖命令声明。',
           '选项仅作观察，不代表设置有效。选项和文件参数内的内容不作为正文命令扫描；宏展开与实际执行仍未验证。'),
}


def dependency_table(rows, language):
    labels = LABELS[language]
    esc = lambda value: html.escape(str(value), quote=True)
    if not rows:
        return f'<p>{esc(labels[8])}</p>'
    content = ['<div class="table-scroll"><table><thead><tr>']
    content.extend(f'<th scope="col">{esc(label)}</th>' for label in labels[1:6])
    content.append('</tr></thead><tbody>')
    for row in rows:
        command = row['command'] + ('*' if row.get('starred') else '')
        content.append(f'<tr><td><code>{esc(command)}</code></td>' + ''.join(f'<td><code>{esc(row[key])}</code></td>' for key in ('value', 'options')))
        content.append(f'<td><code>{esc(row["file"])}:{esc(row["line"])}</code></td>')
        content.append(f'<td>{esc(labels[6] if row["supported"] else labels[7])}')
        if row.get('issue'):
            content.append(f'<br>{esc(row["issue"])}')
        content.append('</td></tr>')
    content.append('</tbody></table></div>')
    return ''.join(content)
